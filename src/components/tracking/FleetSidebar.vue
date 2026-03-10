<!--
  FleetSidebar.vue — Scrollable driver list panel beside the map.
-->
<template>
  <aside class="fleet-sidebar">
    <div class="fleet-sidebar__head">
      <span class="fleet-sidebar__title">Fleet</span>
      <q-badge :label="store.driverCount" color="primary" rounded />
    </div>

    <!-- Stats row -->
    <div class="fleet-sidebar__stats">
      <div class="stat on-track">
        <span class="stat__val">{{ store.onTrackCount }}</span>
        <span class="stat__key">On Track</span>
      </div>
      <div class="stat delayed">
        <span class="stat__val">{{ store.delayedCount }}</span>
        <span class="stat__key">Delayed</span>
      </div>
      <div class="stat rerouting">
        <span class="stat__val">{{ store.reroutingCount }}</span>
        <span class="stat__key">Rerouting</span>
      </div>
    </div>

    <!-- Driver list -->
    <div class="fleet-sidebar__list">
      <TransitionGroup name="list">
        <div
          v-for="driver in store.activeDrivers"
          :key="driver.id"
          class="driver-row"
          :class="{ 'driver-row--selected': store.selectedDriverId === driver.id }"
          @click="store.selectDriver(driver.id)"
        >
          <div class="driver-row__indicator" :style="{ background: STATUS_COLORS[driver.status] }" />
          <div class="driver-row__body">
            <p class="driver-row__name">{{ driver.name ?? `Driver #${driver.id}` }}</p>
            <p class="driver-row__meta">
              <span :class="`status-text--${driver.status}`">{{ STATUS_LABELS[driver.status] }}</span>
              <span v-if="driver.speed !== null">· {{ driver.speed }} km/h</span>
            </p>
          </div>
          <q-icon name="chevron_right" color="grey-7" size="18px" class="driver-row__chevron" />
        </div>
      </TransitionGroup>

      <div v-if="!store.driverCount" class="fleet-sidebar__empty">
        <q-icon name="wifi_off" color="grey-7" size="32px" />
        <p>No drivers online</p>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { useTrackingStore } from 'src/stores/tracking-store'

const store = useTrackingStore()

const STATUS_COLORS = {
  on_track:  '#00F5A0',
  delayed:   '#FFB800',
  rerouting: '#FF3B5C',
  idle:      '#8892A4',
}

const STATUS_LABELS = {
  on_track:  'On Track',
  delayed:   'Delayed',
  rerouting: 'Rerouting',
  idle:      'Idle',
}
</script>

<style scoped>
.fleet-sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #0c1120;
  border-left: 1px solid rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

.fleet-sidebar__head {
  padding: 16px 18px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.fleet-sidebar__title {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #8892a4;
  flex: 1;
}

/* Stats */
.fleet-sidebar__stats {
  display: flex;
  padding: 12px 18px;
  gap: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 4px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
}

.stat__val {
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
}

.stat__key {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
  margin-top: 4px;
}

.on-track  .stat__val { color: #00f5a0; }
.delayed   .stat__val { color: #ffb800; }
.rerouting .stat__val { color: #ff3b5c; }

/* List */
.fleet-sidebar__list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.driver-row {
  display: flex;
  align-items: center;
  padding: 10px 18px;
  gap: 12px;
  cursor: pointer;
  transition: background 0.15s ease;
  border-left: 3px solid transparent;
}

.driver-row:hover {
  background: rgba(255, 255, 255, 0.04);
}

.driver-row--selected {
  background: rgba(74, 108, 247, 0.1);
  border-left-color: #4a6cf7;
}

.driver-row__indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.driver-row__body {
  flex: 1;
  min-width: 0;
}

.driver-row__name {
  font-size: 13px;
  font-weight: 500;
  color: #d1d5db;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.driver-row__meta {
  font-size: 11px;
  color: #6b7280;
  margin: 2px 0 0;
  display: flex;
  gap: 4px;
}

.status-text--on_track  { color: #00f5a0; }
.status-text--delayed   { color: #ffb800; }
.status-text--rerouting { color: #ff3b5c; }
.status-text--idle      { color: #8892a4; }

.driver-row__chevron {
  opacity: 0;
  transition: opacity 0.15s;
}

.driver-row:hover .driver-row__chevron {
  opacity: 1;
}

.fleet-sidebar__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 10px;
  color: #4b5563;
  font-size: 13px;
}

/* List transition */
.list-enter-active,
.list-leave-active {
  transition: all 0.25s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}
</style>
