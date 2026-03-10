<template>
  <q-page class="dash-page">
    <!-- ── KPI cards ─────────────────────────────────────────── -->
    <div class="kpi-grid">
      <div v-for="(kpi, i) in kpis" :key="kpi.label" class="kpi-card glass-panel animate-fade-up" :style="{ animationDelay: (i * 100) + 'ms' }">
        <div class="kpi-card__icon" :style="{ background: kpi.bg }">
          <q-icon :name="kpi.icon" size="22px" :style="{ color: kpi.color }" />
        </div>
        <div class="kpi-card__body">
          <p class="kpi-card__val">
            <span v-if="loading">—</span>
            <span v-else>{{ kpi.value }}</span>
          </p>
          <p class="kpi-card__label">{{ kpi.label }}</p>
        </div>
        <div class="kpi-card__trend" :class="kpi.trendUp ? 'trend--up' : 'trend--down'">
          <q-icon :name="kpi.trendUp ? 'trending_up' : 'trending_down'" size="13px" />
          {{ kpi.trendPct }}%
        </div>
      </div>
    </div>

    <!-- ── Main two-column grid ──────────────────────────────── -->
    <div class="dash-grid">
      <!-- Recent Orders panel -->
      <div class="glass-panel dash-panel animate-fade-up delay-200">
        <div class="panel-head">
          <q-icon name="receipt_long" size="18px" color="primary" />
          <span class="panel-title">Recent Orders</span>
          <q-btn
            flat
            dense
            no-caps
            label="View all"
            color="primary"
            size="sm"
            to="/orders"
            class="q-ml-auto"
          />
        </div>

        <q-list separator class="order-list" v-if="!loading && recentOrders.length">
          <q-item v-for="order in recentOrders" :key="order.id" class="order-item">
            <q-item-section avatar>
              <div class="order-id">#{{ order.id }}</div>
            </q-item-section>
            <q-item-section>
              <q-item-label class="order-addr">
                {{ order.destination_address ?? `Order #${order.id}` }}
              </q-item-label>
              <q-item-label caption class="order-meta">
                {{ order.driver_name ?? 'Unassigned' }} · {{ order.weight }} kg
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-badge
                :label="STATUS_LABELS[order.status?.toLowerCase()] ?? order.status"
                :style="{ background: statusBg(order.status), color: statusColor(order.status) }"
                class="status-badge"
              />
            </q-item-section>
          </q-item>
        </q-list>

        <div v-else-if="loading" class="panel-empty">
          <q-spinner-dots color="primary" size="28px" />
        </div>
        <div v-else class="panel-empty">
          <q-icon name="inbox" size="32px" color="grey-8" />
          <p>No orders yet</p>
        </div>
      </div>

      <!-- Right column -->
      <div class="dash-right">
        <!-- Fleet status panel -->
        <div class="glass-panel dash-panel animate-fade-up delay-300">
          <div class="panel-head">
            <q-icon name="local_shipping" size="18px" color="primary" />
            <span class="panel-title">Fleet Status</span>
            <q-btn
              flat
              dense
              no-caps
              label="Live map"
              color="primary"
              size="sm"
              to="/tracking"
              class="q-ml-auto"
            />
          </div>

          <div class="fleet-stats-grid">
            <div v-for="fs in fleetStats" :key="fs.label" class="fleet-stat">
              <span class="fleet-stat__val" :style="{ color: fs.color }">{{ fs.value }}</span>
              <span class="fleet-stat__label">{{ fs.label }}</span>
              <div class="fleet-stat__bar">
                <div
                  class="fleet-stat__fill"
                  :style="{ width: fs.pct + '%', background: fs.color }"
                />
              </div>
            </div>
          </div>

          <!-- Driver list preview -->
          <div class="driver-previews">
            <div
              v-for="d in previewDrivers"
              :key="d.id"
              class="driver-chip"
              :style="{ '--chip-color': statusColorMap[d.status] ?? '#8892a4' }"
            >
              <span class="driver-chip__dot" />
              <span class="driver-chip__name">{{ d.name ?? `#${d.id}` }}</span>
              <span class="driver-chip__speed" v-if="d.speed !== null"
                >{{ Math.round(d.speed) }} km/h</span
              >
            </div>
          </div>
        </div>

        <!-- Order status breakdown -->
        <div class="glass-panel dash-panel animate-fade-up delay-400">
          <div class="panel-head">
            <q-icon name="donut_large" size="18px" color="primary" />
            <span class="panel-title">Order Breakdown</span>
          </div>
          <div class="breakdown-list">
            <div v-for="row in orderBreakdown" :key="row.label" class="breakdown-row">
              <span class="breakdown-row__dot" :style="{ background: row.color }" />
              <span class="breakdown-row__label">{{ row.label }}</span>
              <div class="breakdown-row__bar">
                <div
                  class="breakdown-row__fill"
                  :style="{ width: row.pct + '%', background: row.color }"
                />
              </div>
              <span class="breakdown-row__count">{{ row.count }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTrackingStore } from 'src/stores/tracking-store'
import { storeToRefs } from 'pinia'

const store = useTrackingStore()
const { activeDrivers } = storeToRefs(store)

const API_KEY = import.meta.env.VITE_API_KEY ?? 'demo-key'
const BUSINESS_ID = Number(import.meta.env.VITE_BUSINESS_ID ?? '1')
const API_HOST = import.meta.env.VITE_API_HOST ?? 'localhost:8000'

const loading = ref(true)
const stats = ref(null)
const recentOrders = ref([])

const STATUS_LABELS = {
  pending: 'Pending',
  assigned: 'Assigned',
  in_transit: 'In Transit',
  delivered: 'Delivered',
  failed: 'Failed',
}

const STATUS_COLORS_MAP = {
  pending: { color: '#ffb800', bg: 'rgba(255,184,0,0.12)' },
  assigned: { color: '#4a6cf7', bg: 'rgba(74,108,247,0.12)' },
  in_transit: { color: '#00f5a0', bg: 'rgba(0,245,160,0.12)' },
  delivered: { color: '#8892a4', bg: 'rgba(136,146,164,0.12)' },
  failed: { color: '#ff3b5c', bg: 'rgba(255,59,92,0.12)' },
}

function statusColor(s) {
  return STATUS_COLORS_MAP[(s ?? '').toLowerCase()]?.color ?? '#8892a4'
}
function statusBg(s) {
  return STATUS_COLORS_MAP[(s ?? '').toLowerCase()]?.bg ?? 'rgba(136,146,164,0.12)'
}

const statusColorMap = {
  on_track: '#00f5a0',
  delayed: '#ffb800',
  rerouting: '#ff3b5c',
  idle: '#8892a4',
}

const kpis = computed(() => {
  const s = stats.value
  return [
    {
      label: 'Active Drivers',
      value: s ? s.online_drivers : '—',
      icon: 'local_shipping',
      color: '#4a6cf7',
      bg: 'rgba(74,108,247,0.15)',
      trendUp: true,
      trendPct: 12,
    },
    {
      label: 'In Transit',
      value: s ? (s.orders_by_status?.IN_TRANSIT ?? 0) : '—',
      icon: 'moving',
      color: '#00f5a0',
      bg: 'rgba(0,245,160,0.15)',
      trendUp: true,
      trendPct: 8,
    },
    {
      label: 'Delivered Today',
      value: s ? s.delivered_today : '—',
      icon: 'check_circle',
      color: '#00f5a0',
      bg: 'rgba(0,245,160,0.12)',
      trendUp: true,
      trendPct: 5,
    },
    {
      label: 'Pending',
      value: s ? (s.orders_by_status?.PENDING ?? 0) : '—',
      icon: 'pending_actions',
      color: '#ffb800',
      bg: 'rgba(255,184,0,0.12)',
      trendUp: false,
      trendPct: 3,
    },
  ]
})

const fleetStats = computed(() => {
  const drivers = activeDrivers.value
  const total = drivers.length || 1
  const counts = {
    on_track: drivers.filter((d) => d.status === 'on_track').length,
    delayed: drivers.filter((d) => d.status === 'delayed').length,
    rerouting: drivers.filter((d) => d.status === 'rerouting').length,
    idle: drivers.filter((d) => d.status === 'idle').length,
  }
  return [
    {
      label: 'On Track',
      value: counts.on_track,
      color: '#00f5a0',
      pct: Math.round((counts.on_track / total) * 100),
    },
    {
      label: 'Delayed',
      value: counts.delayed,
      color: '#ffb800',
      pct: Math.round((counts.delayed / total) * 100),
    },
    {
      label: 'Rerouting',
      value: counts.rerouting,
      color: '#ff3b5c',
      pct: Math.round((counts.rerouting / total) * 100),
    },
    {
      label: 'Idle',
      value: counts.idle,
      color: '#8892a4',
      pct: Math.round((counts.idle / total) * 100),
    },
  ]
})

const previewDrivers = computed(() => activeDrivers.value.slice(0, 5))

const orderBreakdown = computed(() => {
  const s = stats.value
  if (!s) return []
  const map = s.orders_by_status ?? {}
  const total = Object.values(map).reduce((a, b) => a + b, 0) || 1
  return [
    { label: 'In Transit', count: map.IN_TRANSIT ?? 0, color: '#00f5a0' },
    { label: 'Assigned', count: map.ASSIGNED ?? 0, color: '#4a6cf7' },
    { label: 'Pending', count: map.PENDING ?? 0, color: '#ffb800' },
    { label: 'Delivered', count: map.DELIVERED ?? 0, color: '#8892a4' },
    { label: 'Failed', count: map.FAILED ?? 0, color: '#ff3b5c' },
  ].map((r) => ({ ...r, pct: Math.round((r.count / total) * 100) }))
})

onMounted(async () => {
  try {
    const protocol = window.location.protocol
    const res = await fetch(
      `${protocol}//${API_HOST}/api/businesses/${BUSINESS_ID}/dashboard?api_key=${encodeURIComponent(API_KEY)}`,
    )
    if (res.ok) {
      const data = await res.json()
      stats.value = data
      recentOrders.value = data.recent_orders ?? []
    }
  } catch {
    // Backend unreachable — show empty state, no fake data
    stats.value = {
      online_drivers: activeDrivers.value.length,
      delivered_today: 0,
      orders_by_status: {},
    }
    recentOrders.value = []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dash-page {
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 28px;
  min-height: 100vh;
}

/* ── KPI grid ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.kpi-card {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 24px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(20, 25, 45, 0.7), rgba(8, 12, 25, 0.9)) !important;
  border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.kpi-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(circle at top right, var(--color-accent-glow), transparent 60%);
  opacity: 0.15;
  pointer-events: none;
}

.kpi-card__icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}

.kpi-card__body {
  flex: 1;
  z-index: 1;
}

.kpi-card__val {
  font-size: 36px;
  font-weight: 800;
  color: #ffffff;
  margin: 0;
  line-height: 1;
  letter-spacing: -0.02em;
}

.kpi-card__label {
  font-size: 12px;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin: 6px 0 0;
}

.kpi-card__trend {
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 30px;
  z-index: 1;
}

.trend--up {
  color: #00f5a0;
  background: rgba(0, 245, 160, 0.15);
  border: 1px solid rgba(0, 245, 160, 0.2);
}
.trend--down {
  color: #ff3b5c;
  background: rgba(255, 59, 92, 0.15);
  border: 1px solid rgba(255, 59, 92, 0.2);
}

/* ── Main grid ── */
.dash-grid {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 24px;
  flex: 1;
}

.dash-right {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.dash-panel {
  padding: 24px;
  min-height: 180px;
  background: linear-gradient(135deg, rgba(16, 21, 38, 0.6), rgba(8, 12, 25, 0.85)) !important;
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: #c5cae9;
  letter-spacing: 0.02em;
}

.panel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 30px;
  color: #4b5563;
  font-size: 13px;
}

/* ── Orders list ── */
.order-list {
  margin: 0 -20px;
}

.order-item {
  padding: 10px 20px;
  min-height: auto;
}

.order-id {
  font-size: 11px;
  font-weight: 700;
  color: #4a6cf7;
  font-family: monospace;
  background: rgba(74, 108, 247, 0.1);
  padding: 3px 7px;
  border-radius: 6px;
}

.order-addr {
  font-size: 13px;
  color: #c5cae9;
}

.order-meta {
  font-size: 11px;
  color: #6b7280 !important;
}

.status-badge {
  font-size: 10px !important;
  font-weight: 600 !important;
  padding: 3px 8px !important;
  border-radius: 20px !important;
  letter-spacing: 0.04em;
}

/* ── Fleet stats ── */
.fleet-stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 14px;
}

.fleet-stat {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 10px 12px;
}

.fleet-stat__val {
  font-size: 22px;
  font-weight: 700;
  display: block;
  line-height: 1;
}

.fleet-stat__label {
  font-size: 10px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  display: block;
  margin: 4px 0 6px;
}

.fleet-stat__bar {
  height: 3px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 2px;
  overflow: hidden;
}

.fleet-stat__fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.6s ease;
}

/* ── Driver chips ── */
.driver-previews {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.driver-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 20px;
  font-size: 11px;
  color: #c5cae9;
}

.driver-chip__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--chip-color);
  box-shadow: 0 0 5px var(--chip-color);
  flex-shrink: 0;
}

.driver-chip__speed {
  color: #6b7280;
  font-size: 10px;
}

/* ── Order breakdown ── */
.breakdown-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.breakdown-row {
  display: grid;
  grid-template-columns: 8px 90px 1fr 36px;
  align-items: center;
  gap: 8px;
}

.breakdown-row__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.breakdown-row__label {
  font-size: 12px;
  color: #9ca3af;
}

.breakdown-row__bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 2px;
  overflow: hidden;
}

.breakdown-row__fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.6s ease;
}

.breakdown-row__count {
  font-size: 12px;
  font-weight: 600;
  color: #e8eaf6;
  text-align: right;
}

@media (max-width: 1100px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .dash-grid {
    grid-template-columns: 1fr;
  }
}
</style>
