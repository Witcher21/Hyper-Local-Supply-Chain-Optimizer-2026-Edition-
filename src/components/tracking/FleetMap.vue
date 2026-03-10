<!--
  FleetMap.vue — Full-screen Mapbox GL map with live driver markers.

  Props:
    mapboxToken (String) — Public Mapbox access token

  Emits:
    driver-click (driverId: number) — user tapped a vehicle marker
-->
<template>
  <div class="fleet-map-root">
    <!-- Map container -->
    <div ref="mapContainer" class="map-container" />

    <!-- Loading state -->
    <Transition name="fade">
      <div v-if="!mapLoaded" class="map-loading">
        <q-spinner-dots color="primary" size="48px" />
        <p class="map-loading__label">Initialising map…</p>
      </div>
    </Transition>

    <!-- No token warning -->
    <div v-if="!mapboxToken" class="map-token-warn glass-panel">
      <q-icon name="warning" color="warning" size="32px" />
      <p>Set <code>VITE_MAPBOX_TOKEN</code> in your <code>.env</code> to enable the live map.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useTrackingStore } from 'src/stores/tracking-store'
import { storeToRefs } from 'pinia'

const props = defineProps({
  mapboxToken: { type: String, default: '' },
})

const emit = defineEmits(['driver-click'])

const trackingStore = useTrackingStore()
const { activeDrivers, selectedDriverId } = storeToRefs(trackingStore)

const mapContainer = ref(null)
const mapLoaded = ref(false)

let map = null
let mapboxgl = null
// driver_id → { marker: mapboxgl.Marker, el: HTMLElement }
const markerRegistry = new Map()

// ---------------------------------------------------------------------------
// Status → neon colour mapping
// ---------------------------------------------------------------------------
const STATUS_COLORS = {
  on_track: '#00F5A0',
  delayed: '#FFB800',
  rerouting: '#FF3B5C',
  idle: '#8892A4',
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------
onMounted(async () => {
  if (!props.mapboxToken) return
  await initMap()
})

onBeforeUnmount(() => {
  markerRegistry.forEach(({ marker }) => marker.remove())
  markerRegistry.clear()
  if (map) {
    map.remove()
    map = null
  }
})

// ---------------------------------------------------------------------------
// Map initialisation (lazy-loaded for LCP optimisation)
// ---------------------------------------------------------------------------
async function initMap() {
  // Dynamic import keeps mapbox-gl out of the initial bundle
  const mod = await import('mapbox-gl')
  await import('mapbox-gl/dist/mapbox-gl.css')
  mapboxgl = mod.default

  mapboxgl.accessToken = props.mapboxToken

  map = new mapboxgl.Map({
    container: mapContainer.value,
    style: 'mapbox://styles/mapbox/dark-v11',
    center: [0, 20],
    zoom: 2,
    projection: 'mercator',
    antialias: true,
  })

  map.addControl(new mapboxgl.NavigationControl({ showCompass: true }), 'bottom-right')
  map.addControl(new mapboxgl.ScaleControl(), 'bottom-left')

  map.on('load', () => {
    mapLoaded.value = true
    // Render any drivers that loaded from REST before map was ready
    activeDrivers.value.forEach(syncMarker)
  })
}

// ---------------------------------------------------------------------------
// Marker helpers
// ---------------------------------------------------------------------------
function createMarkerEl(driver) {
  const color = STATUS_COLORS[driver.status] ?? STATUS_COLORS.idle
  const el = document.createElement('div')
  el.className = 'driver-marker'
  el.style.setProperty('--marker-color', color)
  el.dataset.driverId = driver.id
  el.innerHTML = `
    <div class="driver-marker__pulse"></div>
    <div class="driver-marker__dot">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
        <path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99z"/>
      </svg>
    </div>
  `
  el.addEventListener('click', () => emit('driver-click', driver.id))
  return el
}

function syncMarker(driver) {
  if (!map || !mapLoaded.value || driver.lat === null || driver.lng === null) return

  const color = STATUS_COLORS[driver.status] ?? STATUS_COLORS.idle

  if (markerRegistry.has(driver.id)) {
    // Update existing marker
    const { marker, el } = markerRegistry.get(driver.id)
    marker.setLngLat([driver.lng, driver.lat])
    el.style.setProperty('--marker-color', color)
    el.querySelector('.driver-marker__dot').style.backgroundColor = color
  } else {
    // Create new marker
    const el = createMarkerEl(driver)
    const marker = new mapboxgl.Marker({ element: el, anchor: 'center' })
      .setLngLat([driver.lng, driver.lat])
      .addTo(map)
    markerRegistry.set(driver.id, { marker, el })
  }
}

function removeMarker(driverId) {
  if (markerRegistry.has(driverId)) {
    markerRegistry.get(driverId).marker.remove()
    markerRegistry.delete(driverId)
  }
}

// ---------------------------------------------------------------------------
// Reactivity — sync store → map markers
// ---------------------------------------------------------------------------
watch(
  activeDrivers,
  (drivers) => {
    if (!mapLoaded.value) return

    const activeIds = new Set(drivers.map((d) => d.id))

    // Remove markers for gone drivers
    markerRegistry.forEach((_, id) => {
      if (!activeIds.has(id)) removeMarker(id)
    })

    // Add / update markers
    drivers.forEach(syncMarker)
  },
  { deep: true },
)

// Highlight selected marker
watch(selectedDriverId, (newId, oldId) => {
  if (oldId !== null && markerRegistry.has(oldId)) {
    markerRegistry.get(oldId).el.classList.remove('is-selected')
  }
  if (newId !== null && markerRegistry.has(newId)) {
    const { el, marker } = markerRegistry.get(newId)
    el.classList.add('is-selected')
    // Fly to selected driver
    map?.flyTo({ center: marker.getLngLat(), zoom: 14, speed: 1.4 })
  }
})
</script>

<style scoped>
.fleet-map-root {
  position: relative;
  width: 100%;
  height: 100%;
}

.map-container {
  width: 100%;
  height: 100%;
}

.map-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #060b18;
  gap: 16px;
}

.map-loading__label {
  color: #8892a4;
  font-size: 14px;
  letter-spacing: 0.05em;
}

.map-token-warn {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
  color: #cdd5e0;
  max-width: 340px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

<!-- Driver marker styles injected globally so they work outside scoped -->
<style>
.driver-marker {
  position: relative;
  width: 36px;
  height: 36px;
  cursor: pointer;
  --marker-color: #00f5a0;
}

.driver-marker__pulse {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  background: var(--marker-color);
  opacity: 0.25;
  animation: pulse 2s ease-out infinite;
}

.driver-marker__dot {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--marker-color);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 12px var(--marker-color), 0 2px 8px rgba(0, 0, 0, 0.5);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.driver-marker:hover .driver-marker__dot,
.driver-marker.is-selected .driver-marker__dot {
  transform: scale(1.2);
  box-shadow: 0 0 20px var(--marker-color), 0 2px 12px rgba(0, 0, 0, 0.6);
}

.driver-marker.is-selected .driver-marker__pulse {
  opacity: 0.5;
  animation: pulse 1s ease-out infinite;
}

@keyframes pulse {
  0%   { transform: scale(1); opacity: 0.4; }
  100% { transform: scale(2.2); opacity: 0; }
}
</style>
