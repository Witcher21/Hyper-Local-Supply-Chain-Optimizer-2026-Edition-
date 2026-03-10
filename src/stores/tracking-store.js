/**
 * Tracking Store — Pinia (Composition API)
 *
 * Manages:
 *  - WebSocket connection lifecycle (connect / disconnect / auto-reconnect)
 *  - Live driver fleet state (map of driver_id → DriverRecord)
 *  - Selected driver for the detail pane
 *
 * WebSocket URL: ws(s)://{VITE_API_HOST}/ws/tracking/{businessId}
 *   ?api_key=xxx&client_type=admin
 */

import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
// No demo simulation — real backend required

/** @typedef {{ id: number, lat: number, lng: number, speed: number|null, heading: number|null, status: string, lastSeen: string, orders?: Array }} DriverRecord */

const WS_CLOSE_NORMAL = 1000
const RECONNECT_DELAY_MS = 5_000
const PING_INTERVAL_MS = 30_000

export const useTrackingStore = defineStore('tracking', () => {
  // -------------------------------------------------------------------------
  // State
  // -------------------------------------------------------------------------

  /** @type {import('vue').Ref<Map<number, DriverRecord>>} */
  const drivers = ref(new Map())

  /** 'disconnected' | 'connecting' | 'connected' */
  const wsStatus = ref('disconnected')

  /** Driver ID selected in the detail pane */
  const selectedDriverId = ref(null)

  // Internal — not exposed
  let _ws = null
  let _reconnectTimer = null
  let _pingInterval = null
  let _businessId = null
  let _apiKey = null


  // -------------------------------------------------------------------------
  // Getters
  // -------------------------------------------------------------------------

  const activeDrivers = computed(() => Array.from(drivers.value.values()))

  const driverCount = computed(() => drivers.value.size)

  const onTrackCount = computed(
    () => activeDrivers.value.filter((d) => d.status === 'on_track').length,
  )
  const delayedCount = computed(
    () => activeDrivers.value.filter((d) => d.status === 'delayed').length,
  )
  const reroutingCount = computed(
    () => activeDrivers.value.filter((d) => d.status === 'rerouting').length,
  )

  const selectedDriver = computed(() =>
    selectedDriverId.value !== null ? (drivers.value.get(selectedDriverId.value) ?? null) : null,
  )

  const isConnected = computed(() => wsStatus.value === 'connected')

  // -------------------------------------------------------------------------
  // Actions
  // -------------------------------------------------------------------------

  function connect(businessId, apiKey) {
    if (_ws && _ws.readyState === WebSocket.OPEN) return

    _businessId = businessId
    _apiKey = apiKey
    wsStatus.value = 'connecting'

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = import.meta.env.VITE_API_HOST ?? 'localhost:8000'
    const url =
      `${protocol}//${host}/ws/tracking/${businessId}` +
      `?api_key=${encodeURIComponent(apiKey)}&client_type=admin`

    _ws = new WebSocket(url)

    _ws.onopen = _onOpen
    _ws.onmessage = _onMessage
    _ws.onerror = _onError
    _ws.onclose = _onClose
  }

  function disconnect() {
    _clearTimers()
    if (_ws) {
      _ws.close(WS_CLOSE_NORMAL, 'Client disconnected')
      _ws = null
    }
    wsStatus.value = 'disconnected'
  }

  function selectDriver(driverId) {
    selectedDriverId.value = driverId === selectedDriverId.value ? null : driverId
  }

  function clearSelectedDriver() {
    selectedDriverId.value = null
  }

  // -------------------------------------------------------------------------
  // Internal WebSocket handlers
  // -------------------------------------------------------------------------

  function _onOpen() {
    wsStatus.value = 'connected'
    clearTimeout(_reconnectTimer)
    _startPing()
  }

  function _onMessage(event) {
    let msg
    try {
      msg = JSON.parse(event.data)
    } catch {
      return
    }
    _handleMessage(msg)
  }

  function _onError() {
    wsStatus.value = 'disconnected'
  }

  function _onClose(event) {
    _clearTimers()
    wsStatus.value = 'disconnected'
    // Only auto-reconnect on abnormal closure
    if (event.code !== WS_CLOSE_NORMAL && _businessId && _apiKey) {
      _reconnectTimer = setTimeout(() => connect(_businessId, _apiKey), RECONNECT_DELAY_MS)
    }
  }

  function _handleMessage(msg) {
    switch (msg.type) {
      case 'fleet_update':
        drivers.value.set(msg.driver_id, {
          id: msg.driver_id,
          lat: msg.lat,
          lng: msg.lng,
          speed: msg.speed ?? null,
          heading: msg.heading ?? null,
          status: (msg.status ?? '').toLowerCase(),
          lastSeen: msg.timestamp,
        })
        break

      case 'driver_connected':
        // Driver came online — record with unknown position until first update
        if (!drivers.value.has(msg.driver_id)) {
          drivers.value.set(msg.driver_id, {
            id: msg.driver_id,
            lat: null,
            lng: null,
            speed: null,
            heading: null,
            status: 'idle',
            lastSeen: msg.timestamp,
          })
        }
        break

      case 'driver_disconnected':
        drivers.value.delete(msg.driver_id)
        if (selectedDriverId.value === msg.driver_id) {
          selectedDriverId.value = null
        }
        break

      case 'connection_established':
        // Server sends the list of already-connected driver IDs at handshake
        if (Array.isArray(msg.active_driver_ids)) {
          msg.active_driver_ids.forEach((id) => {
            if (!drivers.value.has(id)) {
              drivers.value.set(id, {
                id,
                lat: null,
                lng: null,
                speed: null,
                heading: null,
                status: 'idle',
                lastSeen: null,
              })
            }
          })
        }
        break

      case 'pong':
        // Heartbeat acknowledged — no-op
        break

      default:
        break
    }
  }



  function _startPing() {
    _pingInterval = setInterval(() => {
      if (_ws && _ws.readyState === WebSocket.OPEN) {
        _ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, PING_INTERVAL_MS)
  }

  function _clearTimers() {
    clearInterval(_pingInterval)
    clearTimeout(_reconnectTimer)
    _pingInterval = null
    _reconnectTimer = null
  }

  // -------------------------------------------------------------------------
  // Seed fleet from REST (used on initial page load for instant map state)
  // -------------------------------------------------------------------------

  async function fetchInitialFleet(businessId, apiKey) {
    const host = import.meta.env.VITE_API_HOST ?? 'localhost:8000'
    const protocol = window.location.protocol
    try {
      const res = await fetch(
        `${protocol}//${host}/api/businesses/${businessId}/drivers?api_key=${encodeURIComponent(apiKey)}&active_only=true`,
      )
      if (!res.ok) return
      const list = await res.json()
      list.forEach((d) => {
        drivers.value.set(d.id, {
          id: d.id,
          lat: d.lat,
          lng: d.lng,
          speed: d.speed,
          heading: d.heading,
          status: (d.status ?? '').toLowerCase(),
          lastSeen: d.last_seen,
          name: d.name,
          vehicleType: d.vehicle_type,
        })
      })
    } catch {
      // Silently fail — WebSocket will sync state anyway
    }
  }

  return {
    // State
    drivers,
    wsStatus,
    selectedDriverId,
    // Getters
    activeDrivers,
    driverCount,
    onTrackCount,
    delayedCount,
    reroutingCount,
    selectedDriver,
    isConnected,
    // Actions
    connect,
    disconnect,
    selectDriver,
    clearSelectedDriver,
    fetchInitialFleet,
  }
})
