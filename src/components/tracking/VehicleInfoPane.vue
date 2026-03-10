<!--
  VehicleInfoPane.vue — Glassmorphism slide-in panel for selected driver details.
-->
<template>
  <Transition name="slide-in">
    <div v-if="driver" class="info-pane glass-panel">
      <!-- Header -->
      <div class="info-pane__header">
        <div class="info-pane__avatar" :style="{ background: statusColor }">
          <q-icon name="local_shipping" color="white" size="22px" />
        </div>
        <div class="info-pane__title">
          <p class="info-pane__name">{{ driver.name ?? `Driver #${driver.id}` }}</p>
          <p class="info-pane__vehicle">{{ driver.vehicleType ?? 'Vehicle' }}</p>
        </div>
        <q-btn flat round dense icon="close" color="white" @click="store.clearSelectedDriver()" />
      </div>

      <!-- Status badge -->
      <div class="info-pane__status" :style="{ '--status-color': statusColor }">
        <span class="status-dot" />
        <span class="status-label">{{ statusLabel }}</span>
      </div>

      <!-- Telemetry -->
      <div class="info-pane__metrics">
        <div class="metric-card">
          <q-icon name="speed" size="18px" color="grey-5" />
          <span class="metric-value">{{
            driver.speed !== null ? `${driver.speed} km/h` : '—'
          }}</span>
          <span class="metric-key">Speed</span>
        </div>
        <div class="metric-card">
          <q-icon name="navigation" size="18px" color="grey-5" />
          <span class="metric-value">{{
            driver.heading !== null ? `${Math.round(driver.heading)}°` : '—'
          }}</span>
          <span class="metric-key">Heading</span>
        </div>
        <div class="metric-card">
          <q-icon name="my_location" size="18px" color="grey-5" />
          <span class="metric-value">{{ driver.lat !== null ? driver.lat.toFixed(4) : '—' }}</span>
          <span class="metric-key">Latitude</span>
        </div>
        <div class="metric-card">
          <q-icon name="my_location" size="18px" color="grey-5" />
          <span class="metric-value">{{ driver.lng !== null ? driver.lng.toFixed(4) : '—' }}</span>
          <span class="metric-key">Longitude</span>
        </div>
      </div>

      <!-- Active orders -->
      <div class="info-pane__section">
        <p class="info-pane__section-title">Active Orders</p>
        <div v-if="orders.length" class="order-list">
          <div v-for="order in orders" :key="order.id" class="order-item">
            <q-icon name="inventory_2" size="16px" color="grey-5" />
            <div>
              <p class="order-item__addr">
                {{ order.destination_address ?? `Order #${order.id}` }}
              </p>
              <p class="order-item__weight">
                {{ order.weight }} kg ·
                <span :class="`status--${order.status}`">{{ order.status }}</span>
              </p>
            </div>
          </div>
        </div>
        <p v-else class="info-pane__empty">No active orders</p>
      </div>

      <!-- Last seen -->
      <p v-if="driver.lastSeen" class="info-pane__lastseen">
        Last update: {{ formatTime(driver.lastSeen) }}
      </p>
    </div>
  </Transition>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useTrackingStore } from 'src/stores/tracking-store'
import { storeToRefs } from 'pinia'

const store = useTrackingStore()
const { selectedDriver: driver } = storeToRefs(store)

const orders = ref([])

const STATUS_META = {
  on_track: { label: 'On Track', color: '#00F5A0' },
  delayed: { label: 'Delayed', color: '#FFB800' },
  rerouting: { label: 'Rerouting', color: '#FF3B5C' },
  idle: { label: 'Idle', color: '#8892A4' },
}

const statusColor = computed(() => STATUS_META[driver.value?.status]?.color ?? '#8892A4')
const statusLabel = computed(() => STATUS_META[driver.value?.status]?.label ?? 'Unknown')

// Fetch orders whenever selected driver changes
watch(driver, async (d) => {
  orders.value = []
  if (!d) return
  const host = import.meta.env.VITE_API_HOST ?? 'localhost:8000'
  const apiKey = import.meta.env.VITE_API_KEY ?? ''
  const businessId = import.meta.env.VITE_BUSINESS_ID ?? '1'
  try {
    const res = await fetch(
      `${window.location.protocol}//${host}/api/businesses/${businessId}/drivers/${d.id}/orders?api_key=${encodeURIComponent(apiKey)}`,
    )
    if (res.ok) {
      orders.value = await res.json()
    }
    // If API fails, orders stay empty — no demo fallback
  } catch {
    // Backend unreachable — show empty orders
    orders.value = []
  }
})

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}
</script>

<style scoped>
.info-pane {
  position: absolute;
  top: 80px;
  right: 16px;
  width: 300px;
  padding: 20px;
  z-index: 20;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Header */
.info-pane__header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-pane__avatar {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.info-pane__title {
  flex: 1;
  min-width: 0;
}

.info-pane__name {
  font-weight: 600;
  font-size: 15px;
  color: #e8eaf6;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.info-pane__vehicle {
  font-size: 12px;
  color: #8892a4;
  margin: 2px 0 0;
  text-transform: capitalize;
}

/* Status */
.info-pane__status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.07);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--status-color);
  box-shadow: 0 0 6px var(--status-color);
  flex-shrink: 0;
}

.status-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--status-color);
}

/* Metrics grid */
.info-pane__metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.metric-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-value {
  font-size: 15px;
  font-weight: 600;
  color: #e8eaf6;
}

.metric-key {
  font-size: 11px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Orders section */
.info-pane__section-title {
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin: 0 0 8px;
}

.order-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.order-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.order-item__addr {
  font-size: 13px;
  color: #c5cae9;
  margin: 0;
}

.order-item__weight {
  font-size: 11px;
  color: #8892a4;
  margin: 2px 0 0;
}

.status--in_transit {
  color: #4a6cf7;
}
.status--assigned {
  color: #00f5a0;
}
.status--delivered {
  color: #8892a4;
}

.info-pane__empty {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

.info-pane__lastseen {
  font-size: 11px;
  color: #4b5563;
  margin: 0;
  text-align: right;
}

/* Slide-in transition */
.slide-in-enter-active,
.slide-in-leave-active {
  transition:
    opacity 0.25s ease,
    transform 0.25s ease;
}

.slide-in-enter-from,
.slide-in-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
