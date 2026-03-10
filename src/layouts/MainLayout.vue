<template>
  <q-layout view="hHh lpR fFf" class="main-layout">
    <!-- ── Left navigation drawer ───────────────────────────── -->
    <q-drawer
      v-model="drawerOpen"
      :width="220"
      :breakpoint="768"
      class="main-nav"
      side="left"
      bordered
    >
      <!-- Logo -->
      <div class="nav-logo">
        <q-icon name="hub" size="28px" color="primary" />
        <div class="nav-logo__text">
          <span class="nav-logo__name">HyperLocal</span>
          <span class="nav-logo__sub">Supply Chain</span>
        </div>
      </div>

      <!-- Navigation links -->
      <q-list class="nav-list">
        <q-item
          v-for="link in navLinks"
          :key="link.to"
          :to="link.to"
          exact
          active-class="nav-item--active"
          class="nav-item"
          clickable
          v-ripple
        >
          <q-item-section avatar>
            <q-icon :name="link.icon" size="20px" />
          </q-item-section>
          <q-item-section class="nav-item__label">{{ link.label }}</q-item-section>
          <q-item-section v-if="link.badge" side>
            <q-badge :label="link.badge" color="primary" rounded />
          </q-item-section>
        </q-item>
      </q-list>

      <!-- Bottom: WS status + version -->
      <div class="nav-footer" style="flex-direction: column; align-items: flex-start; gap: 8px;">
        <div style="display:flex; justify-content:space-between; width:100%;">
          <div class="ws-status" :class="trackingStore.isConnected ? 'ws-online' : 'ws-offline'">
            <span class="ws-dot" />
            <span>{{ trackingStore.isConnected ? 'Live' : 'Offline' }}</span>
          </div>
          <span class="nav-footer__ver">v2026.1.0</span>
        </div>
        <div style="font-size: 10px; color: #a8b2c1; background: rgba(74, 108, 247, 0.15); padding: 4px 8px; border-radius: 4px; border: 1px solid rgba(74, 108, 247, 0.3); width: 100%; text-align: center; font-weight: 500; letter-spacing: 0.05em;">
          Made by <b style="color:#00f5a0;">G.nawod Sanjana</b>
        </div>
      </div>
    </q-drawer>

    <!-- ── Top header ─────────────────────────────────────────── -->
    <q-header class="main-header" elevated>
      <q-toolbar>
        <q-btn flat round dense icon="menu" color="grey-4" @click="drawerOpen = !drawerOpen" />
        <q-toolbar-title class="main-header__title">
          {{ currentPageTitle }}
        </q-toolbar-title>

        <!-- Notifications button -->
        <q-btn flat round dense icon="notifications_none" color="grey-4">
          <q-badge v-if="alerts.length > 0" floating color="negative" :label="alerts.length" />
          <q-menu class="notification-menu" dark anchor="bottom right" self="top right" :offset="[0, 8]">
            <div class="notif-panel">
              <div class="notif-header">
                <span class="notif-header__title">Notifications</span>
                <q-btn flat dense no-caps size="xs" label="Clear all" color="grey-6" @click="alerts = []" v-if="alerts.length" />
              </div>
              <div v-if="alerts.length" class="notif-list">
                <div v-for="(alert, i) in alerts" :key="i" class="notif-item">
                  <q-icon :name="alert.icon" size="16px" :color="alert.color" />
                  <div class="notif-item__body">
                    <p class="notif-item__text">{{ alert.text }}</p>
                    <p class="notif-item__time">{{ alert.time }}</p>
                  </div>
                </div>
              </div>
              <div v-else class="notif-empty">
                <q-icon name="notifications_off" size="28px" color="grey-8" />
                <p>All clear — no new alerts</p>
              </div>
            </div>
          </q-menu>
        </q-btn>

        <!-- Profile button -->
        <q-btn flat round dense icon="account_circle" color="grey-4" class="q-ml-sm">
          <q-menu class="profile-menu" dark anchor="bottom right" self="top right" :offset="[0, 8]">
            <div class="profile-panel">
              <div class="profile-info">
                <div class="profile-avatar">
                  <q-icon name="person" size="24px" color="white" />
                </div>
                <div>
                  <p class="profile-name">Admin User</p>
                  <p class="profile-email">ops@demodistributor.lk</p>
                </div>
              </div>
              <div class="profile-divider" />
              <div class="profile-links">
                <q-item clickable v-ripple class="profile-link" to="/settings" v-close-popup>
                  <q-item-section avatar><q-icon name="settings" size="16px" /></q-item-section>
                  <q-item-section>Settings</q-item-section>
                </q-item>
                <q-item clickable v-ripple class="profile-link" @click="showLogoutDialog = true" v-close-popup>
                  <q-item-section avatar><q-icon name="logout" size="16px" color="negative" /></q-item-section>
                  <q-item-section style="color:#ff3b5c">Log out</q-item-section>
                </q-item>
              </div>
            </div>
          </q-menu>
        </q-btn>
      </q-toolbar>
    </q-header>

    <!-- ── Page content ───────────────────────────────────────── -->
    <q-page-container>
      <router-view />
    </q-page-container>

    <!-- Logout confirmation -->
    <q-dialog v-model="showLogoutDialog">
      <q-card dark style="min-width:300px;background:#12182b;border:1px solid rgba(255,255,255,0.09);border-radius:14px">
        <q-card-section>
          <div class="text-h6" style="color:#e8eaf6">Log Out</div>
          <p style="color:#9ca3af;font-size:13px;margin:8px 0 0">Are you sure you want to log out?</p>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat no-caps label="Cancel" color="grey-5" v-close-popup />
          <q-btn unelevated no-caps label="Log Out" color="negative" v-close-popup @click="handleLogout" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-layout>
</template>

<script setup>
import { ref, computed, watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import { useTrackingStore } from 'src/stores/tracking-store'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const drawerOpen = ref(true)
const route = useRoute()
const showLogoutDialog = ref(false)

const navLinks = [
  { to: '/dashboard', icon: 'dashboard',      label: 'Dashboard'     },
  { to: '/tracking',  icon: 'location_on',    label: 'Live Tracking' },
  { to: '/orders',    icon: 'inventory_2',    label: 'Orders'        },
  { to: '/routes',    icon: 'alt_route',      label: 'Routes'        },
  { to: '/drivers',   icon: 'local_shipping', label: 'Drivers'       },
  { to: '/stock',     icon: 'warehouse',      label: 'Stock Engine'  },
  { to: '/settings',  icon: 'settings',       label: 'Settings'      },
]

const currentPageTitle = computed(
  () => navLinks.find((l) => route.path.startsWith(l.to))?.label ?? 'HyperLocal SCM',
)

const trackingStore = useTrackingStore()

// Real-time alerts from driver statuses
const alerts = ref([])

watchEffect(() => {
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  const newAlerts = []
  trackingStore.activeDrivers.forEach(d => {
    if (d.status === 'delayed') {
      newAlerts.push({ icon: 'warning', color: 'warning', text: `${d.name ?? 'Driver #' + d.id} is delayed`, time: now })
    }
    if (d.status === 'rerouting') {
      newAlerts.push({ icon: 'alt_route', color: 'negative', text: `${d.name ?? 'Driver #' + d.id} rerouting`, time: now })
    }
  })
  if (!trackingStore.isConnected && trackingStore.wsStatus !== 'disconnected') {
    newAlerts.push({ icon: 'cloud_off', color: 'grey-6', text: 'Backend connection lost', time: now })
  }
  alerts.value = newAlerts
})

function handleLogout() {
  trackingStore.disconnect()
  $q.notify({ type: 'info', message: 'Logged out — reconnect via Settings', position: 'top-right' })
}
</script>

<style scoped>
.main-layout {
  background: transparent !important;
}

/* ── Header ── */
.main-header {
  background: rgba(10, 15, 30, 0.4) !important;
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.main-header__title {
  font-size: 16px;
  font-weight: 600;
  color: #e8eaf6;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

/* ── Nav drawer ── */
.main-nav {
  background: rgba(10, 15, 30, 0.45) !important;
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 18px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.nav-logo__text {
  display: flex;
  flex-direction: column;
}

.nav-logo__name {
  font-size: 14px;
  font-weight: 700;
  color: #e8eaf6;
  letter-spacing: 0.02em;
  line-height: 1.1;
}

.nav-logo__sub {
  font-size: 10px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.07em;
}

.nav-list {
  padding: 12px 8px;
}

.nav-item {
  border-radius: 10px;
  margin-bottom: 2px;
  min-height: 40px;
  color: #8892a4 !important;
  transition: background 0.15s ease, color 0.15s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05) !important;
  color: #d1d5db !important;
}

.nav-item--active {
  background: rgba(74, 108, 247, 0.15) !important;
  color: #4a6cf7 !important;
}

.nav-item__label {
  font-size: 13px;
  font-weight: 500;
}

.nav-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-footer__ver {
  font-size: 10px;
  color: #374151;
  letter-spacing: 0.05em;
}

.ws-status { display: flex; align-items: center; gap: 5px; font-size: 10px; }
.ws-dot { width: 6px; height: 6px; border-radius: 50%; }
.ws-online { color: #00f5a0; }
.ws-online .ws-dot { background: #00f5a0; box-shadow: 0 0 6px #00f5a0; }
.ws-offline { color: #6b7280; }
.ws-offline .ws-dot { background: #6b7280; }

/* ── Notification panel ── */
:deep(.notification-menu) {
  background: #12182b !important;
  border: 1px solid rgba(255,255,255,0.09) !important;
  border-radius: 14px !important;
  box-shadow: 0 20px 60px rgba(0,0,0,0.6) !important;
  min-width: 320px;
}

.notif-panel { padding: 14px 16px; }
.notif-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.notif-header__title { font-size: 13px; font-weight: 600; color: #e8eaf6; }
.notif-list { display: flex; flex-direction: column; gap: 6px; max-height: 300px; overflow-y: auto; }
.notif-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px; background: rgba(255,255,255,0.03); border-radius: 8px; }
.notif-item__text { font-size: 12px; color: #c5cae9; margin: 0; }
.notif-item__time { font-size: 10px; color: #6b7280; margin: 2px 0 0; }
.notif-empty { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 30px; color: #4b5563; font-size: 12px; }

/* ── Profile panel ── */
:deep(.profile-menu) {
  background: #12182b !important;
  border: 1px solid rgba(255,255,255,0.09) !important;
  border-radius: 14px !important;
  box-shadow: 0 20px 60px rgba(0,0,0,0.6) !important;
  min-width: 220px;
}

.profile-panel { padding: 14px 16px; }
.profile-info { display: flex; align-items: center; gap: 12px; }
.profile-avatar { width: 40px; height: 40px; border-radius: 10px; background: linear-gradient(135deg, #4a6cf7, #7c3aed); display: flex; align-items: center; justify-content: center; }
.profile-name { font-size: 13px; font-weight: 600; color: #e8eaf6; margin: 0; }
.profile-email { font-size: 11px; color: #6b7280; margin: 2px 0 0; }
.profile-divider { height: 1px; background: rgba(255,255,255,0.06); margin: 12px 0; }
.profile-links { display: flex; flex-direction: column; gap: 2px; }
.profile-link { border-radius: 8px; min-height: 36px; color: #9ca3af !important; font-size: 13px; }
.profile-link:hover { background: rgba(255,255,255,0.05) !important; }
</style>
