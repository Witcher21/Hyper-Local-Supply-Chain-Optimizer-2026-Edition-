<template>
  <q-page class="routes-page">

    <!-- ── Header strip ─────────────────────────────────────── -->
    <div class="routes-header">
      <div class="routes-kpis">
        <div v-for="kpi in routeKPIs" :key="kpi.label" class="route-kpi glass-panel">
          <q-icon :name="kpi.icon" size="18px" :style="{ color: kpi.color }" />
          <div>
            <p class="route-kpi__val">{{ kpi.value }}</p>
            <p class="route-kpi__label">{{ kpi.label }}</p>
          </div>
        </div>
      </div>

      <q-btn
        unelevated no-caps icon="auto_fix_high" label="Run AI Optimizer"
        color="primary" :loading="optimizing" @click="runOptimizer"
        class="optimizer-btn"
      />
    </div>

    <!-- ── Optimizer status banner ───────────────────────────── -->
    <Transition name="fade">
      <div v-if="optimizerMessage" class="optimizer-banner glass-panel" :class="optimizerClass">
        <q-icon :name="optimizerIcon" size="20px" />
        <span>{{ optimizerMessage }}</span>
        <q-btn flat round dense icon="close" size="sm" @click="optimizerMessage = ''" />
      </div>
    </Transition>

    <!-- ── Main content ──────────────────────────────────────── -->
    <div class="routes-body">

      <!-- Active routes list -->
      <div class="glass-panel routes-list-panel">
        <div class="panel-head">
          <q-icon name="alt_route" size="18px" color="primary" />
          <span class="panel-title">Active Routes</span>
          <q-badge :label="activeRoutes.length" color="primary" rounded class="q-ml-auto" />
        </div>

        <div class="route-list">
          <div
            v-for="route in activeRoutes"
            :key="route.driverId"
            class="route-item"
            :class="{ 'route-item--selected': selectedRoute === route.driverId }"
            @click="selectedRoute = selectedRoute === route.driverId ? null : route.driverId"
          >
            <div class="route-item__avatar" :style="{ '--s': statusColor(route.status) }">
              <q-icon :name="vehicleIcon(route.vehicleType)" size="16px" color="white" />
            </div>

            <div class="route-item__info">
              <p class="route-item__driver">{{ route.driverName }}</p>
              <p class="route-item__meta">{{ route.stops }} stop{{ route.stops !== 1 ? 's' : '' }} · {{ route.totalKm }} km · {{ route.eta }}</p>
            </div>

            <div class="route-item__status">
              <q-badge
                :label="STATUS_LABELS[route.status] ?? route.status"
                :style="{ background: statusBg(route.status), color: statusColor(route.status) }"
                class="status-badge"
              />
              <p class="route-item__progress">{{ route.completed }}/{{ route.stops }} done</p>
            </div>
          </div>

          <div v-if="loadingRoutes" class="route-empty">
            <q-spinner-dots size="30px" color="primary" />
            <p>Loading routes…</p>
          </div>

          <div v-else-if="!activeRoutes.length" class="route-empty">
            <q-icon name="route" size="36px" color="grey-8" />
            <p>No active routes — assign orders to drivers</p>
          </div>
        </div>
      </div>

      <!-- Route detail panel -->
      <div class="glass-panel route-detail-panel">
        <Transition name="fade" mode="out-in">
          <div v-if="selectedRouteData" :key="selectedRouteData.driverId">
            <div class="panel-head">
              <q-icon name="directions" size="18px" color="primary" />
              <span class="panel-title">{{ selectedRouteData.driverName }}</span>
              <q-btn flat round dense icon="close" size="sm" color="grey-6" class="q-ml-auto" @click="selectedRoute = null" />
            </div>

            <div class="detail-metrics">
              <div class="detail-metric">
                <q-icon name="straighten" size="14px" color="grey-5" />
                <span class="dm-val">{{ selectedRouteData.totalKm }} km</span>
                <span class="dm-key">Total distance</span>
              </div>
              <div class="detail-metric">
                <q-icon name="schedule" size="14px" color="grey-5" />
                <span class="dm-val">{{ selectedRouteData.eta }}</span>
                <span class="dm-key">ETA</span>
              </div>
              <div class="detail-metric">
                <q-icon name="local_gas_station" size="14px" color="grey-5" />
                <span class="dm-val">{{ selectedRouteData.fuelEst }} L</span>
                <span class="dm-key">Fuel est.</span>
              </div>
              <div class="detail-metric">
                <q-icon name="inventory_2" size="14px" color="grey-5" />
                <span class="dm-val">{{ selectedRouteData.totalWeight }} kg</span>
                <span class="dm-key">Load</span>
              </div>
            </div>

            <!-- Progress bar -->
            <div class="route-progress-section">
              <div class="route-progress-head">
                <span class="route-progress-label">Route progress</span>
                <span class="route-progress-pct">{{ selectedRouteData.stops > 0 ? Math.round(selectedRouteData.completed / selectedRouteData.stops * 100) : 0 }}%</span>
              </div>
              <div class="route-progress-bar">
                <div class="route-progress-fill" :style="{ width: (selectedRouteData.stops > 0 ? Math.round(selectedRouteData.completed / selectedRouteData.stops * 100) : 0) + '%' }" />
              </div>
            </div>

            <!-- Stop list -->
            <div class="stop-list">
              <div
                v-for="(stop, i) in selectedRouteData.stopList"
                :key="i" class="stop-item"
                :class="{ 'stop-done': stop.done, 'stop-current': stop.current }"
              >
                <div class="stop-item__index">
                  <q-icon v-if="stop.done" name="check_circle" size="16px" color="positive" />
                  <q-icon v-else-if="stop.current" name="radio_button_checked" size="16px" color="primary" />
                  <span v-else class="stop-num">{{ i + 1 }}</span>
                </div>
                <div class="stop-item__body">
                  <p class="stop-item__addr">{{ stop.address }}</p>
                  <p class="stop-item__weight">{{ stop.weight }} kg · <span :class="stop.done ? 'stop-delivered' : 'stop-pending'">{{ stop.done ? 'Delivered' : (stop.current ? 'In Transit' : 'Pending') }}</span></p>
                </div>
                <div class="stop-item__time">{{ stop.time }}</div>
              </div>
            </div>
          </div>

          <div v-else class="route-detail-empty">
            <q-icon name="touch_app" size="40px" color="grey-8" />
            <p>Select a route to see details</p>
          </div>
        </Transition>
      </div>

    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useTrackingStore } from 'src/stores/tracking-store'
import { storeToRefs } from 'pinia'
import { driversApi, optimizerApi } from 'src/utils/api'

const store = useTrackingStore()
const { activeDrivers } = storeToRefs(store)

const selectedRoute    = ref(null)
const optimizing       = ref(false)
const optimizerMessage = ref('')
const optimizerClass   = ref('')
const optimizerIcon    = ref('check_circle')
const loadingRoutes    = ref(false)
const driverOrders     = ref({}) // { driverId: [orders] }

const STATUS_LABELS = { on_track: 'On Track', delayed: 'Delayed', rerouting: 'Rerouting', idle: 'Idle' }

const STATUS_COLORS_MAP = {
  on_track:  { color: '#00f5a0', bg: 'rgba(0,245,160,0.15)'  },
  delayed:   { color: '#ffb800', bg: 'rgba(255,184,0,0.15)'  },
  rerouting: { color: '#ff3b5c', bg: 'rgba(255,59,92,0.15)'  },
  idle:      { color: '#8892a4', bg: 'rgba(136,146,164,0.15)'},
}

function statusColor(s) { return STATUS_COLORS_MAP[s]?.color ?? '#8892a4' }
function statusBg(s)    { return STATUS_COLORS_MAP[s]?.bg    ?? 'rgba(136,146,164,0.12)' }
function vehicleIcon(t) {
  if (t === 'truck') return 'local_shipping'
  if (t === 'bike')  return 'two_wheeler'
  return 'airport_shuttle'
}

// Fetch orders for each active driver from the real API
async function loadDriverOrders() {
  loadingRoutes.value = true
  const result = {}
  for (const d of activeDrivers.value.filter(d => d.status !== 'idle')) {
    try {
      const orders = await driversApi.orders(d.id)
      result[d.id] = orders
    } catch {
      result[d.id] = []
    }
  }
  driverOrders.value = result
  loadingRoutes.value = false
}

// Build route data from live driver + real API orders
const activeRoutes = computed(() => {
  return activeDrivers.value
    .filter(d => d.status !== 'idle')
    .map(d => {
      const orders = driverOrders.value[d.id] ?? []
      const completed = orders.filter(o => (o.status ?? '').toLowerCase() === 'delivered').length
      const totalWeight = orders.reduce((s, o) => s + (o.weight ?? 0), 0)
      const totalKm = (orders.length * 2.2).toFixed(1)
      const etaMinutes = Math.round((totalKm / 35) * 60)
      const eta = `${Math.floor(etaMinutes / 60)}h ${etaMinutes % 60}m`
      return {
        driverId:    d.id,
        driverName:  d.name ?? `Driver #${d.id}`,
        vehicleType: d.vehicleType ?? 'van',
        status:      d.status,
        stops:       orders.length,
        completed,
        totalKm,
        totalWeight: totalWeight.toFixed(1),
        eta,
        fuelEst:     (totalKm * 0.08).toFixed(1),
        stopList:    orders.map((o, i) => ({
          address: o.destination_address ?? 'Unknown address',
          weight:  o.weight ?? 0,
          done:    (o.status ?? '').toLowerCase() === 'delivered',
          current: i === completed,
          time:    i === completed ? 'Now' : (i < completed ? '—' : `+${((i - completed + 1) * 12)}m`),
        })),
      }
    })
})

const selectedRouteData = computed(() =>
  activeRoutes.value.find(r => r.driverId === selectedRoute.value) ?? null
)

const routeKPIs = computed(() => [
  { label: 'Active Routes', value: activeRoutes.value.length,      icon: 'alt_route',       color: '#4a6cf7' },
  { label: 'Total Stops',   value: activeRoutes.value.reduce((s, r) => s + r.stops, 0),    icon: 'pin_drop',        color: '#00f5a0' },
  { label: 'Km Today',      value: activeRoutes.value.reduce((s, r) => s + Number(r.totalKm), 0).toFixed(0), icon: 'straighten', color: '#ffb800' },
  { label: 'Avg Speed',
    value: activeDrivers.value.filter(d => d.speed).length
      ? Math.round(activeDrivers.value.filter(d => d.speed).reduce((s, d) => s + d.speed, 0) / activeDrivers.value.filter(d => d.speed).length) + ' km/h'
      : '—',
    icon: 'speed', color: '#ff3b5c' },
])

async function runOptimizer() {
  optimizing.value = true
  optimizerMessage.value = ''
  try {
    const result = await optimizerApi.run()
    optimizerMessage.value = result.message
    optimizerClass.value = 'banner--success'
    optimizerIcon.value = 'auto_fix_high'
  } catch (e) {
    optimizerMessage.value = 'Optimization failed: ' + e.message
    optimizerClass.value = 'banner--error'
    optimizerIcon.value = 'error'
  } finally {
    optimizing.value = false
  }
}

watch(activeDrivers, () => {
  if (activeDrivers.value.length) loadDriverOrders()
}, { immediate: true })
</script>

<style scoped>
.routes-page { padding: 20px 24px; display: flex; flex-direction: column; gap: 16px; min-height: 100vh; background: var(--color-bg-primary); }

/* Header */
.routes-header { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.routes-kpis { display: flex; gap: 10px; flex: 1; flex-wrap: wrap; }
.route-kpi { display: flex; align-items: center; gap: 10px; padding: 12px 16px; min-width: 140px; }
.route-kpi__val { font-size: 20px; font-weight: 700; color: #e8eaf6; margin: 0; line-height: 1; }
.route-kpi__label { font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.07em; margin: 3px 0 0; }
.optimizer-btn { border-radius: 10px !important; padding: 0 20px !important; height: 40px; background: linear-gradient(135deg, #4a6cf7, #7c3aed) !important; }

/* Optimizer banner */
.optimizer-banner { display: flex; align-items: center; gap: 10px; padding: 12px 16px; font-size: 13px; }
.banner--success { color: #00f5a0; border-color: rgba(0,245,160,0.2) !important; background: rgba(0,245,160,0.06) !important; }
.banner--error   { color: #ff3b5c; border-color: rgba(255,59,92,0.2) !important; background: rgba(255,59,92,0.06) !important; }

/* Body grid */
.routes-body { display: grid; grid-template-columns: 380px 1fr; gap: 14px; flex: 1; }

/* Routes list */
.routes-list-panel { padding: 18px; display: flex; flex-direction: column; gap: 14px; }
.panel-head { display: flex; align-items: center; gap: 8px; }
.panel-title { font-size: 13px; font-weight: 600; color: #c5cae9; }
.route-list { display: flex; flex-direction: column; gap: 8px; overflow-y: auto; flex: 1; }

.route-item {
  display: flex; align-items: center; gap: 12px; padding: 12px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px; cursor: pointer; transition: background 0.15s ease, border-color 0.15s ease;
}
.route-item:hover { background: rgba(255,255,255,0.06); }
.route-item--selected { background: rgba(74,108,247,0.1) !important; border-color: rgba(74,108,247,0.3) !important; }

.route-item__avatar { width: 36px; height: 36px; border-radius: 10px; background: rgba(255,255,255,0.07); border: 1px solid var(--s); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.route-item__info { flex: 1; min-width: 0; }
.route-item__driver { font-size: 13px; font-weight: 600; color: #e8eaf6; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.route-item__meta { font-size: 11px; color: #6b7280; margin: 3px 0 0; }
.route-item__status { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.status-badge { font-size: 10px !important; font-weight: 600 !important; padding: 3px 8px !important; border-radius: 20px !important; }
.route-item__progress { font-size: 10px; color: #6b7280; margin: 0; }
.route-empty { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 40px; color: #4b5563; font-size: 13px; }

/* Detail panel */
.route-detail-panel { padding: 18px; overflow-y: auto; }
.detail-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 14px 0; }
.detail-metric { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 10px 12px; display: flex; flex-direction: column; gap: 3px; }
.dm-val { font-size: 18px; font-weight: 700; color: #e8eaf6; }
.dm-key { font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.06em; }

/* Progress */
.route-progress-section { margin-bottom: 16px; }
.route-progress-head { display: flex; justify-content: space-between; margin-bottom: 6px; }
.route-progress-label { font-size: 12px; color: #9ca3af; }
.route-progress-pct { font-size: 12px; font-weight: 600; color: #4a6cf7; }
.route-progress-bar { height: 5px; background: rgba(255,255,255,0.06); border-radius: 3px; overflow: hidden; }
.route-progress-fill { height: 100%; background: linear-gradient(90deg, #4a6cf7, #00f5a0); border-radius: 3px; transition: width 0.6s ease; }

/* Stops */
.stop-list { display: flex; flex-direction: column; gap: 2px; }
.stop-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 8px; transition: background 0.15s; }
.stop-item:hover { background: rgba(255,255,255,0.04); }
.stop-done   { opacity: 0.5; }
.stop-current { background: rgba(74,108,247,0.08); border: 1px solid rgba(74,108,247,0.2); }
.stop-item__index { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.stop-num { width: 20px; height: 20px; border-radius: 50%; background: rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: center; font-size: 10px; color: #6b7280; }
.stop-item__body { flex: 1; min-width: 0; }
.stop-item__addr { font-size: 12px; color: #c5cae9; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stop-item__weight { font-size: 11px; color: #6b7280; margin: 2px 0 0; }
.stop-delivered { color: #00f5a0; }
.stop-pending   { color: #6b7280; }
.stop-item__time { font-size: 11px; color: #6b7280; flex-shrink: 0; }
.route-detail-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 300px; gap: 10px; color: #4b5563; font-size: 13px; }

/* Transitions */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (max-width: 900px) { .routes-body { grid-template-columns: 1fr; } }
</style>
