<!--
  TrackingPage.vue — Live Fleet Tracking dashboard (Phase 1)

  Layout:
    ┌──────────────────────────────────┬──────────────┐
    │   Glassmorphism top status bar   │              │
    ├──────────────────────────────────┤  Fleet       │
    │                                  │  Sidebar     │
    │         Mapbox GL Map           │  (driver     │
    │      (grows to fill space)      │   list)      │
    │                                  │              │
    └──────────────────────────────────┴──────────────┘
    Vehicle Info Pane overlays the map on marker click.
-->
<template>
  <q-page class="tracking-page">
    <!-- ── Top status bar ───────────────────────────────────── -->
    <header class="status-bar glass-panel animate-fade-up">
      <div class="status-bar__brand">
        <q-icon name="hub" size="20px" color="primary" />
        <span class="status-bar__label">Live Fleet Tracking</span>
      </div>

      <!-- WS connection badge -->
      <div class="ws-badge" :class="`ws-badge--${store.wsStatus}`">
        <span class="ws-badge__dot" />
        <span class="ws-badge__text">{{ WS_LABELS[store.wsStatus] }}</span>
      </div>

      <div class="status-bar__metrics">
        <div class="sb-metric">
          <span class="sb-metric__val">{{ store.driverCount }}</span>
          <span class="sb-metric__key">Online</span>
        </div>
        <div class="sb-metric">
          <span class="sb-metric__val on-track">{{ store.onTrackCount }}</span>
          <span class="sb-metric__key">On Track</span>
        </div>
        <div class="sb-metric">
          <span class="sb-metric__val delayed">{{ store.delayedCount }}</span>
          <span class="sb-metric__key">Delayed</span>
        </div>
        <div class="sb-metric">
          <span class="sb-metric__val rerouting">{{ store.reroutingCount }}</span>
          <span class="sb-metric__key">Rerouting</span>
        </div>
      </div>

      <q-btn
        flat
        round
        dense
        :icon="store.isConnected ? 'wifi' : 'wifi_off'"
        :color="store.isConnected ? 'positive' : 'grey-6'"
        @click="toggleConnection"
      >
        <q-tooltip>{{ store.isConnected ? 'Disconnect' : 'Connect' }}</q-tooltip>
      </q-btn>
    </header>

    <!-- ── Main body ─────────────────────────────────────────── -->
    <div class="tracking-body animate-fade-up delay-200">
      <!-- Map + floating pane -->
      <div class="map-wrapper">
        <FleetMap
          :mapbox-token="mapboxToken"
          @driver-click="store.selectDriver($event)"
        />
        <VehicleInfoPane />
      </div>

      <!-- Sidebar -->
      <FleetSidebar />
    </div>
  </q-page>
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import { useTrackingStore } from 'src/stores/tracking-store'
import FleetMap from 'src/components/tracking/FleetMap.vue'
import VehicleInfoPane from 'src/components/tracking/VehicleInfoPane.vue'
import FleetSidebar from 'src/components/tracking/FleetSidebar.vue'

const store = useTrackingStore()

const mapboxToken = import.meta.env.VITE_MAPBOX_TOKEN ?? ''
const API_KEY     = import.meta.env.VITE_API_KEY      ?? 'demo-key'
const BUSINESS_ID = Number(import.meta.env.VITE_BUSINESS_ID ?? '1')

const WS_LABELS = {
  disconnected: 'Disconnected',
  connecting:   'Connecting…',
  connected:    'Live',
}

onMounted(async () => {
  // 1. Seed map with REST state for instant LCP
  await store.fetchInitialFleet(BUSINESS_ID, API_KEY)
  // 2. Open WebSocket for real-time updates
  store.connect(BUSINESS_ID, API_KEY)
})

onBeforeUnmount(() => {
  store.disconnect()
})

function toggleConnection() {
  if (store.isConnected) {
    store.disconnect()
  } else {
    store.connect(BUSINESS_ID, API_KEY)
  }
}
</script>

<style scoped>
.tracking-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px);
  background: transparent;
  overflow: hidden;
}

/* ── Top bar ── */
.status-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 0 20px;
  height: 56px;
  flex-shrink: 0;
  z-index: 30;
  border-radius: 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}

.status-bar__brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
  color: #e8eaf6;
  white-space: nowrap;
}

.status-bar__label {
  letter-spacing: 0.02em;
}

/* WS badge */
.ws-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.ws-badge--connected    { background: rgba(0,245,160,0.12); color: #00f5a0; }
.ws-badge--connecting   { background: rgba(255,184,0,0.12);  color: #ffb800; }
.ws-badge--disconnected { background: rgba(255,59,92,0.12);  color: #ff3b5c; }

.ws-badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.ws-badge--connected .ws-badge__dot {
  animation: blink 1.8s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}

/* Metrics */
.status-bar__metrics {
  display: flex;
  gap: 24px;
  margin-left: auto;
}

.sb-metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.1;
}

.sb-metric__val {
  font-size: 18px;
  font-weight: 700;
  color: #e8eaf6;
}

.sb-metric__val.on-track  { color: #00f5a0; }
.sb-metric__val.delayed   { color: #ffb800; }
.sb-metric__val.rerouting { color: #ff3b5c; }

.sb-metric__key {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
}

/* ── Body ── */
.tracking-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.map-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
}
</style>
