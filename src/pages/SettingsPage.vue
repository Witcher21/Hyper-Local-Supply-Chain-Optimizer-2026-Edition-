<template>
  <q-page class="settings-page">
    <div class="settings-grid">

      <!-- ── Left nav ──────────────────────────────────────── -->
      <div class="settings-nav glass-panel animate-fade-up">
        <div
          v-for="section in sections"
          :key="section.id"
          class="settings-nav__item"
          :class="{ 'settings-nav__item--active': activeSection === section.id }"
          @click="activeSection = section.id"
        >
          <q-icon :name="section.icon" size="18px" />
          <span>{{ section.label }}</span>
        </div>
      </div>

      <!-- ── Content panels ────────────────────────────────── -->
      <div class="settings-content glass-panel animate-fade-up delay-200">

        <!-- Loading state -->
        <div v-if="loadingSettings" class="settings-panel glass-panel" style="display:flex;align-items:center;justify-content:center;min-height:300px">
          <q-spinner-dots size="36px" color="primary" />
        </div>

        <!-- Error state -->
        <div v-else-if="loadError" class="settings-panel glass-panel error-banner">
          <q-icon name="cloud_off" size="18px" />
          <span>{{ loadError }}</span>
          <q-btn flat dense no-caps size="sm" label="Retry" color="primary" @click="loadSettings" />
        </div>

        <template v-else>

        <!-- Business Profile -->
        <div v-if="activeSection === 'profile'" class="settings-panel glass-panel">
          <div class="panel-head">
            <q-icon name="business" size="20px" color="primary" />
            <span class="panel-title">Business Profile</span>
          </div>

          <div class="form-grid">
            <div class="form-field">
              <label class="form-label">Business Name</label>
              <q-input v-model="profile.name" dense outlined dark bg-color="transparent" class="form-input" />
            </div>
            <div class="form-field">
              <label class="form-label">Subscription Tier</label>
              <q-select
                v-model="profile.tier"
                :options="tierOptions"
                dense outlined dark bg-color="transparent"
                class="form-input"
              >
                <template #selected-item="{ opt }">
                  <q-badge :label="opt" :color="tierColor(opt)" />
                </template>
              </q-select>
            </div>
            <div class="form-field full-width">
              <label class="form-label">Business Address</label>
              <q-input v-model="profile.address" dense outlined dark bg-color="transparent" class="form-input" />
            </div>
            <div class="form-field">
              <label class="form-label">Contact Email</label>
              <q-input v-model="profile.email" dense outlined dark bg-color="transparent" type="email" class="form-input" />
            </div>
            <div class="form-field">
              <label class="form-label">Phone</label>
              <q-input v-model="profile.phone" dense outlined dark bg-color="transparent" class="form-input" />
            </div>
          </div>

          <div class="form-actions">
            <q-btn unelevated no-caps label="Save Changes" color="primary" :loading="saving" @click="saveAllSettings" />
            <q-btn flat no-caps label="Reset" color="grey-6" @click="loadSettings" />
          </div>
        </div>

        <!-- API Configuration -->
        <div v-if="activeSection === 'api'" class="settings-panel glass-panel">
          <div class="panel-head">
            <q-icon name="vpn_key" size="20px" color="primary" />
            <span class="panel-title">API Configuration</span>
          </div>

          <div class="api-key-box">
            <label class="form-label">Business API Key</label>
            <div class="api-key-row">
              <q-input
                :value="showKey ? apiKey : '•'.repeat(apiKey.length)"
                dense outlined dark bg-color="transparent"
                readonly
                class="form-input flex-1"
              >
                <template #append>
                  <q-btn flat round dense :icon="showKey ? 'visibility_off' : 'visibility'" size="sm" color="grey-6" @click="showKey = !showKey" />
                  <q-btn flat round dense icon="copy_all" size="sm" color="grey-6" @click="copyKey">
                    <q-tooltip>Copy API key</q-tooltip>
                  </q-btn>
                </template>
              </q-input>
            </div>
            <p class="form-hint">Used to authenticate WebSocket and REST API requests. Never share this key publicly.</p>
          </div>

          <div class="settings-divider" />

          <div class="form-grid">
            <div class="form-field full-width">
              <label class="form-label">API Host</label>
              <q-input :model-value="apiHost" dense outlined dark bg-color="transparent" class="form-input" readonly>
                <template #prepend><q-icon name="dns" color="grey-6" size="16px" /></template>
              </q-input>
            </div>
            <div class="form-field full-width">
              <label class="form-label">WebSocket Endpoint</label>
              <q-input :model-value="`ws://${apiHost}/ws/tracking/${businessId}`" dense outlined dark bg-color="transparent" class="form-input" readonly>
                <template #prepend><q-icon name="hub" color="grey-6" size="16px" /></template>
              </q-input>
            </div>
          </div>

          <div class="api-status-row">
            <div class="api-status-indicator" :class="wsStore.isConnected ? 'connected' : 'disconnected'">
              <span class="api-status-dot" />
              <span>{{ wsStore.isConnected ? 'WebSocket connected' : 'WebSocket disconnected' }}</span>
            </div>
            <q-btn
              flat dense no-caps size="sm"
              :icon="wsStore.isConnected ? 'wifi_off' : 'wifi'"
              :label="wsStore.isConnected ? 'Disconnect' : 'Connect'"
              :color="wsStore.isConnected ? 'negative' : 'positive'"
              @click="toggleWs"
            />
          </div>
        </div>

        <!-- Alerts & Thresholds -->
        <div v-if="activeSection === 'alerts'" class="settings-panel glass-panel">
          <div class="panel-head">
            <q-icon name="notifications_active" size="20px" color="primary" />
            <span class="panel-title">Alerts & Thresholds</span>
          </div>

          <div class="alert-rows">
            <div v-for="alert in alertsDef" :key="alert.key" class="alert-row">
              <div class="alert-row__info">
                <q-icon :name="alert.icon" size="18px" :color="alert.color" />
                <div>
                  <p class="alert-row__label">{{ alert.label }}</p>
                  <p class="alert-row__desc">{{ alert.desc }}</p>
                </div>
              </div>
              <div class="alert-row__controls">
                <q-input
                  v-if="alert.type === 'number'"
                  v-model.number="alertValues[alert.key]"
                  dense outlined dark bg-color="transparent"
                  type="number"
                  :suffix="alert.suffix"
                  style="width:120px"
                />
                <q-toggle v-else v-model="alertValues[alert.key]" color="primary" />
              </div>
            </div>
          </div>

          <div class="form-actions">
            <q-btn unelevated no-caps label="Save Alert Settings" color="primary" :loading="saving" @click="saveAllSettings" />
          </div>
        </div>

        <!-- AI & Optimization -->
        <div v-if="activeSection === 'ai'" class="settings-panel glass-panel">
          <div class="panel-head">
            <q-icon name="auto_fix_high" size="20px" color="primary" />
            <span class="panel-title">AI & Route Optimization</span>
          </div>

          <div class="alert-rows">
            <div class="alert-row">
              <div class="alert-row__info">
                <q-icon name="schedule" size="18px" color="primary" />
                <div>
                  <p class="alert-row__label">Auto-optimize interval</p>
                  <p class="alert-row__desc">How often the AI re-evaluates and adjusts routes</p>
                </div>
              </div>
              <q-select v-model="aiSettings.optimizeInterval" :options="['5 minutes','10 minutes','15 minutes','30 minutes','1 hour','Manual only']" dense outlined dark bg-color="transparent" style="width:150px" />
            </div>
            <div class="alert-row">
              <div class="alert-row__info">
                <q-icon name="traffic" size="18px" color="warning" />
                <div>
                  <p class="alert-row__label">Traffic data source</p>
                  <p class="alert-row__desc">Real-time traffic provider used for route optimization</p>
                </div>
              </div>
              <q-select v-model="aiSettings.trafficSource" :options="['Mapbox Traffic', 'Google Maps', 'HERE Maps', 'None']" dense outlined dark bg-color="transparent" style="width:160px" />
            </div>
            <div class="alert-row">
              <div class="alert-row__info">
                <q-icon name="psychology" size="18px" color="purple-4" />
                <div>
                  <p class="alert-row__label">AI model</p>
                  <p class="alert-row__desc">Language model used for agentic route decisions</p>
                </div>
              </div>
              <q-select v-model="aiSettings.model" :options="['GPT-4o (Recommended)', 'GPT-4o-mini', 'Claude 3.5 Sonnet', 'Gemini 1.5 Pro']" dense outlined dark bg-color="transparent" style="width:210px" />
            </div>
            <div class="alert-row">
              <div class="alert-row__info">
                <q-icon name="smart_toy" size="18px" color="positive" />
                <div>
                  <p class="alert-row__label">Autonomous rerouting</p>
                  <p class="alert-row__desc">Allow AI to push reroute commands directly to drivers</p>
                </div>
              </div>
              <q-toggle v-model="aiSettings.autonomousRerouting" color="primary" />
            </div>
          </div>

          <div class="form-actions">
            <q-btn unelevated no-caps label="Save AI Settings" color="primary" :loading="saving" @click="saveAllSettings" />
          </div>
        </div>

        </template>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useTrackingStore } from 'src/stores/tracking-store'
import { useQuasar } from 'quasar'
import { settingsApi, API_KEY, API_HOST, BUSINESS_ID } from 'src/utils/api'

const $q = useQuasar()
const wsStore = useTrackingStore()

const activeSection = ref('profile')
const saving = ref(false)
const showKey = ref(false)
const loadingSettings = ref(true)
const loadError = ref('')

const apiKey     = API_KEY
const apiHost    = API_HOST
const businessId = BUSINESS_ID

const sections = [
  { id: 'profile', icon: 'business',           label: 'Business Profile' },
  { id: 'api',     icon: 'vpn_key',            label: 'API & WebSocket'  },
  { id: 'alerts',  icon: 'notifications_active',label: 'Alerts'          },
  { id: 'ai',      icon: 'auto_fix_high',       label: 'AI & Optimizer'  },
]

const tierOptions = ['FREE', 'STARTER', 'PRO', 'ENTERPRISE']
function tierColor(t) {
  return { FREE: 'grey-7', STARTER: 'blue-6', PRO: 'purple-6', ENTERPRISE: 'amber-7' }[t] ?? 'grey-7'
}

const profile = ref({ name: '', tier: 'FREE', address: '', email: '', phone: '' })

const alertsDef = [
  { key: 'delayThreshold', label: 'Delay alert threshold',    desc: 'Alert when a driver is delayed by this many minutes',      icon: 'schedule',       color: 'warning', type: 'number', suffix: 'min' },
  { key: 'speedLimit',     label: 'Speeding threshold',       desc: 'Alert when a driver exceeds this speed',                    icon: 'speed',          color: 'negative',type: 'number', suffix: 'km/h' },
  { key: 'lowStock',       label: 'Low stock notifications',  desc: 'Notify when inventory drops below reorder point',           icon: 'warehouse',      color: 'warning', type: 'toggle' },
  { key: 'driverOffline',  label: 'Driver offline alert',     desc: 'Alert when a driver loses GPS connectivity for >5 min',     icon: 'wifi_off',       color: 'negative',type: 'toggle' },
  { key: 'orderFailed',    label: 'Failed order alerts',      desc: 'Instant notification when an order is marked as failed',    icon: 'cancel',         color: 'negative',type: 'toggle' },
  { key: 'dailyReport',    label: 'Daily summary report',     desc: 'Send end-of-day performance report to business email',      icon: 'summarize',      color: 'primary', type: 'toggle' },
]

const alertValues = ref({
  delayThreshold: 15,
  speedLimit: 80,
  lowStock: true,
  driverOffline: true,
  orderFailed: true,
  dailyReport: false,
})

const aiSettings = ref({
  optimizeInterval:      '10 minutes',
  trafficSource:         'Mapbox Traffic',
  model:                 'GPT-4o (Recommended)',
  autonomousRerouting:   false,
})

async function loadSettings() {
  loadingSettings.value = true
  loadError.value = ''
  try {
    const data = await settingsApi.load()
    if (data.profile) {
      profile.value = { ...profile.value, ...data.profile }
    }
    if (data.alerts) {
      alertValues.value = { ...alertValues.value, ...data.alerts }
    }
    if (data.ai) {
      aiSettings.value = { ...aiSettings.value, ...data.ai }
    }
  } catch {
    loadError.value = 'Could not load settings — check backend connection'
  } finally {
    loadingSettings.value = false
  }
}

async function saveAllSettings() {
  saving.value = true
  try {
    await settingsApi.save({
      profile: profile.value,
      alerts: alertValues.value,
      ai: aiSettings.value,
    })
    $q.notify({ type: 'positive', message: 'Settings saved successfully', position: 'top-right', timeout: 2000 })
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Failed to save: ' + e.message, position: 'top-right' })
  } finally {
    saving.value = false
  }
}

function copyKey() {
  navigator.clipboard.writeText(apiKey)
  $q.notify({ type: 'positive', message: 'API key copied to clipboard', position: 'top-right', timeout: 1500 })
}

function toggleWs() {
  if (wsStore.isConnected) {
    wsStore.disconnect()
  } else {
    wsStore.connect(Number(businessId), apiKey)
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.settings-page { padding: 20px 24px; min-height: 100vh; background: var(--color-bg-primary); }
.settings-grid { display: grid; grid-template-columns: 220px 1fr; gap: 16px; align-items: start; }

/* Nav */
.settings-nav { padding: 8px; display: flex; flex-direction: column; gap: 2px; position: sticky; top: 20px; }
.settings-nav__item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 8px; font-size: 13px; font-weight: 500; color: #8892a4; cursor: pointer; transition: background 0.15s ease, color 0.15s ease; }
.settings-nav__item:hover { background: rgba(255,255,255,0.05); color: #d1d5db; }
.settings-nav__item--active { background: rgba(74,108,247,0.15); color: #4a6cf7; }

/* Content */
.settings-panel { padding: 22px 24px; display: flex; flex-direction: column; gap: 20px; }
.panel-head { display: flex; align-items: center; gap: 10px; }
.panel-title { font-size: 15px; font-weight: 600; color: #e8eaf6; }

.error-banner { color: #ff3b5c; border-color: rgba(255,59,92,0.2) !important; background: rgba(255,59,92,0.06) !important; flex-direction: row; align-items: center; gap: 10px; font-size: 13px; }

/* Form fields */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.full-width { grid-column: 1 / -1; }
.form-field { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; color: #6b7280; }
:deep(.form-input .q-field__control) { background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.09) !important; border-radius: 9px !important; color: #e8eaf6 !important; }
:deep(.form-input .q-field__control:hover) { border-color: rgba(74,108,247,0.4) !important; }
.form-hint { font-size: 11px; color: #6b7280; margin: 4px 0 0; }
.form-actions { display: flex; gap: 10px; padding-top: 4px; border-top: 1px solid rgba(255,255,255,0.06); }

/* API key */
.api-key-box { display: flex; flex-direction: column; gap: 8px; }
.api-key-row { display: flex; gap: 8px; align-items: center; }
.flex-1 { flex: 1; }
.settings-divider { height: 1px; background: rgba(255,255,255,0.06); }
.api-status-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; }
.api-status-indicator { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.api-status-dot { width: 8px; height: 8px; border-radius: 50%; }
.connected    .api-status-dot { background: #00f5a0; box-shadow: 0 0 6px #00f5a0; }
.disconnected .api-status-dot { background: #ff3b5c; }
.connected    { color: #00f5a0; }
.disconnected { color: #6b7280; }

/* Alert rows */
.alert-rows { display: flex; flex-direction: column; gap: 4px; }
.alert-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 12px 14px; border-radius: 10px; transition: background 0.15s; }
.alert-row:hover { background: rgba(255,255,255,0.03); }
.alert-row__info { display: flex; align-items: flex-start; gap: 12px; flex: 1; }
.alert-row__label { font-size: 13px; font-weight: 500; color: #d1d5db; margin: 0; }
.alert-row__desc { font-size: 11px; color: #6b7280; margin: 3px 0 0; }

@media (max-width: 768px) {
  .settings-grid { grid-template-columns: 1fr; }
  .form-grid { grid-template-columns: 1fr; }
}
</style>
