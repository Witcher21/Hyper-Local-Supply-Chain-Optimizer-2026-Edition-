<template>
  <q-page class="drivers-page">

    <!-- ── Toolbar ──────────────────────────────────────────── -->
    <div class="drivers-toolbar animate-fade-up">
      <q-input
        v-model="search"
        dense
        outlined
        placeholder="Search drivers…"
        class="search-input"
        dark
        bg-color="transparent"
      >
        <template #prepend><q-icon name="search" color="grey-6" /></template>
        <template #append>
          <q-icon v-if="search" name="close" color="grey-6" class="cursor-pointer" @click="search = ''" />
        </template>
      </q-input>

      <q-btn-toggle
        v-model="statusFilter"
        no-caps dense rounded
        toggle-color="primary" text-color="grey-5"
        :options="filterOptions"
        class="filter-toggle"
      />

      <q-btn
        unelevated no-caps icon="person_add" label="Add Driver"
        color="primary" class="q-ml-auto create-btn"
        @click="showCreateDialog = true"
      />

      <q-btn-toggle
        v-model="viewMode"
        no-caps dense rounded
        toggle-color="primary" text-color="grey-5"
        :options="[{ value: 'grid', icon: 'grid_view' }, { value: 'list', icon: 'list' }]"
      />
    </div>

    <!-- ── Loading state ─────────────────────────────────────── -->
    <div v-if="loading" class="text-center q-pa-xl">
      <q-spinner-dots size="40px" color="primary" />
      <p style="color:#6b7280;margin-top:8px">Loading drivers…</p>
    </div>

    <!-- ── Error banner ──────────────────────────────────────── -->
    <div v-if="error" class="error-banner glass-panel">
      <q-icon name="cloud_off" size="18px" />
      <span>{{ error }}</span>
      <q-btn flat dense no-caps size="sm" label="Retry" color="primary" @click="loadDrivers" />
    </div>

    <template v-if="!loading">
      <!-- ── Online indicator ──────────────────────────────────── -->
      <div class="online-strip animate-fade-up delay-100">
        <div class="online-strip__label">
          <span class="online-dot" />
          <span>{{ onlineCount }} driver{{ onlineCount !== 1 ? 's' : '' }} active</span>
        </div>
        <span class="online-strip__total">{{ filteredDrivers.length }} shown</span>
      </div>

      <!-- ── Grid view ─────────────────────────────────────────── -->
      <div v-if="viewMode === 'grid'" class="drivers-grid">
        <div
          v-for="(driver, i) in filteredDrivers"
          :key="driver.id"
          class="driver-card glass-panel animate-fade-up"
          :class="{ 'driver-card--selected': selectedId === driver.id }"
          :style="{ animationDelay: ((i % 10) * 50 + 100) + 'ms' }"
          @click="selectedId = selectedId === driver.id ? null : driver.id"
        >
          <!-- Status ring -->
          <div class="driver-card__avatar" :style="{ '--s': statusColor(driver.status) }">
            <q-icon :name="vehicleIcon(driver.vehicle_type)" size="24px" color="white" />
            <span class="driver-card__ring" />
          </div>

          <!-- Info -->
          <div class="driver-card__body">
            <p class="driver-card__name">{{ driver.name ?? `Driver #${driver.id}` }}</p>
            <p class="driver-card__vehicle">
              <q-icon :name="vehicleIcon(driver.vehicle_type)" size="12px" color="grey-6" />
              {{ capitalize(driver.vehicle_type ?? 'vehicle') }}
            </p>
          </div>

          <!-- Status badge -->
          <q-badge
            :label="STATUS_LABELS[driver.status] ?? driver.status"
            :style="{ background: statusBg(driver.status), color: statusColor(driver.status) }"
            class="status-badge"
          />

          <!-- Metrics row -->
          <div class="driver-card__metrics">
            <div class="metric">
              <q-icon name="speed" size="12px" color="grey-6" />
              <span>{{ driver.speed !== null && driver.speed !== undefined ? Math.round(driver.speed) + ' km/h' : '—' }}</span>
            </div>
            <div class="metric">
              <q-icon name="navigation" size="12px" color="grey-6" />
              <span>{{ driver.heading !== null && driver.heading !== undefined ? Math.round(driver.heading) + '°' : '—' }}</span>
            </div>
            <div class="metric">
              <q-icon name="my_location" size="12px" color="grey-6" />
              <span>{{ driver.lat ? Number(driver.lat).toFixed(3) + ', ' + Number(driver.lng).toFixed(3) : 'No GPS' }}</span>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="driver-card__actions" v-if="selectedId === driver.id">
            <q-btn flat dense no-caps size="sm" icon="map" label="View on map" color="primary" @click.stop="$router.push('/tracking')" />
            <q-btn flat dense no-caps size="sm" icon="edit" label="Edit" color="grey-5" @click.stop="openEditDriver(driver)" />
            <q-btn flat dense no-caps size="sm" icon="delete_outline" label="Remove" color="negative" @click.stop="removeDriver(driver)" />
          </div>
        </div>

        <div v-if="!filteredDrivers.length && !loading" class="no-drivers">
          <q-icon name="person_off" size="40px" color="grey-8" />
          <p>No drivers match your filter</p>
          <q-btn unelevated no-caps label="Add Driver" color="primary" @click="showCreateDialog = true" />
        </div>
      </div>

      <!-- ── List view ─────────────────────────────────────────── -->
      <div v-else class="glass-panel drivers-list-wrap animate-fade-up delay-200">
        <q-table
          :rows="filteredDrivers"
          :columns="listColumns"
          row-key="id"
          flat dark
          :loading="loading"
          no-data-label="No drivers found"
          class="drivers-table"
          table-header-class="drivers-table-head"
          :rows-per-page-options="[25, 50]"
        >
          <template #body-cell-name="props">
            <q-td :props="props">
              <div class="list-name">
                <div class="list-avatar" :style="{ '--s': statusColor(props.row.status) }">
                  <q-icon :name="vehicleIcon(props.row.vehicle_type)" size="14px" color="white" />
                </div>
                {{ props.row.name ?? `Driver #${props.row.id}` }}
              </div>
            </q-td>
          </template>

          <template #body-cell-status="props">
            <q-td :props="props">
              <q-badge
                :label="STATUS_LABELS[props.value] ?? props.value"
                :style="{ background: statusBg(props.value), color: statusColor(props.value) }"
                class="status-badge"
              />
            </q-td>
          </template>

          <template #body-cell-speed="props">
            <q-td :props="props">
              <span v-if="props.value !== null">{{ Math.round(props.value) }} <span style="color:#6b7280;font-size:10px">km/h</span></span>
              <span v-else style="color:#4b5563">—</span>
            </q-td>
          </template>

          <template #body-cell-actions="props">
            <q-td :props="props">
              <q-btn flat round dense icon="edit" color="grey-6" size="sm" @click.stop="openEditDriver(props.row)">
                <q-tooltip>Edit driver</q-tooltip>
              </q-btn>
              <q-btn flat round dense icon="delete_outline" color="negative" size="sm" @click.stop="removeDriver(props.row)">
                <q-tooltip>Remove driver</q-tooltip>
              </q-btn>
            </q-td>
          </template>
        </q-table>
      </div>
    </template>

    <!-- ── Create Driver Dialog ──────────────────────────────── -->
    <q-dialog v-model="showCreateDialog" persistent>
      <q-card class="dialog-card" dark>
        <q-card-section class="dialog-header">
          <q-icon name="person_add" size="22px" color="primary" />
          <span class="dialog-title">Add New Driver</span>
          <q-btn flat round dense icon="close" color="grey-6" v-close-popup />
        </q-card-section>
        <q-card-section class="dialog-body">
          <div class="dialog-form-grid">
            <div class="dialog-field">
              <label class="dialog-label">Name</label>
              <q-input v-model="newDriver.name" dense outlined dark bg-color="transparent" placeholder="Kasun Perera" />
            </div>
            <div class="dialog-field">
              <label class="dialog-label">Vehicle Type</label>
              <q-select v-model="newDriver.vehicle_type" :options="['van','truck','bike']" dense outlined dark bg-color="transparent" />
            </div>
            <div class="dialog-field">
              <label class="dialog-label">Latitude</label>
              <q-input v-model.number="newDriver.lat" dense outlined dark bg-color="transparent" type="number" step="0.0001" />
            </div>
            <div class="dialog-field">
              <label class="dialog-label">Longitude</label>
              <q-input v-model.number="newDriver.lng" dense outlined dark bg-color="transparent" type="number" step="0.0001" />
            </div>
          </div>
        </q-card-section>
        <q-card-actions class="dialog-actions" align="right">
          <q-btn flat no-caps label="Cancel" color="grey-5" v-close-popup />
          <q-btn unelevated no-caps label="Add Driver" color="primary" :loading="saving" @click="createDriver" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ── Edit Driver Dialog ────────────────────────────────── -->
    <q-dialog v-model="showEditDialog" persistent>
      <q-card class="dialog-card" dark>
        <q-card-section class="dialog-header">
          <q-icon name="edit" size="22px" color="primary" />
          <span class="dialog-title">Edit Driver</span>
          <q-btn flat round dense icon="close" color="grey-6" v-close-popup />
        </q-card-section>
        <q-card-section class="dialog-body">
          <div class="dialog-form-grid">
            <div class="dialog-field">
              <label class="dialog-label">Name</label>
              <q-input v-model="editDriver.name" dense outlined dark bg-color="transparent" />
            </div>
            <div class="dialog-field">
              <label class="dialog-label">Vehicle Type</label>
              <q-select v-model="editDriver.vehicle_type" :options="['van','truck','bike']" dense outlined dark bg-color="transparent" />
            </div>
            <div class="dialog-field">
              <label class="dialog-label">Status</label>
              <q-select v-model="editDriver.status" :options="['ON_TRACK','DELAYED','REROUTING','IDLE']" dense outlined dark bg-color="transparent" />
            </div>
          </div>
        </q-card-section>
        <q-card-actions class="dialog-actions" align="right">
          <q-btn flat no-caps label="Cancel" color="grey-5" v-close-popup />
          <q-btn unelevated no-caps label="Save Changes" color="primary" :loading="saving" @click="updateDriver" />
        </q-card-actions>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { driversApi } from 'src/utils/api'

const $q = useQuasar()

const search       = ref('')
const statusFilter = ref('all')
const viewMode     = ref('grid')
const selectedId   = ref(null)
const saving       = ref(false)
const loading      = ref(false)
const error        = ref('')
const driversList  = ref([])   // ← loaded from REST API, not WebSocket

const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const newDriver = ref({ name: '', vehicle_type: 'van', lat: 6.9271, lng: 79.8612 })
const editDriver = ref({ id: null, name: '', vehicle_type: '', status: '' })

const STATUS_LABELS = {
  ON_TRACK: 'On Track', DELAYED: 'Delayed', REROUTING: 'Rerouting', IDLE: 'Idle',
  on_track: 'On Track', delayed: 'Delayed', rerouting: 'Rerouting', idle: 'Idle',
}

const STATUS_COLORS_MAP = {
  on_track:  { color: '#00f5a0', bg: 'rgba(0,245,160,0.15)'  },
  ON_TRACK:  { color: '#00f5a0', bg: 'rgba(0,245,160,0.15)'  },
  delayed:   { color: '#ffb800', bg: 'rgba(255,184,0,0.15)'  },
  DELAYED:   { color: '#ffb800', bg: 'rgba(255,184,0,0.15)'  },
  rerouting: { color: '#ff3b5c', bg: 'rgba(255,59,92,0.15)'  },
  REROUTING: { color: '#ff3b5c', bg: 'rgba(255,59,92,0.15)'  },
  idle:      { color: '#8892a4', bg: 'rgba(136,146,164,0.15)'},
  IDLE:      { color: '#8892a4', bg: 'rgba(136,146,164,0.15)'},
}

function statusColor(s) { return STATUS_COLORS_MAP[s]?.color ?? '#8892a4' }
function statusBg(s)    { return STATUS_COLORS_MAP[s]?.bg    ?? 'rgba(136,146,164,0.12)' }
function capitalize(s)  { return s ? s.charAt(0).toUpperCase() + s.slice(1) : '' }
function vehicleIcon(t) {
  if (t === 'truck') return 'local_shipping'
  if (t === 'bike')  return 'two_wheeler'
  return 'airport_shuttle'
}

const filterOptions = [
  { value: 'all',       label: 'All'        },
  { value: 'ON_TRACK',  label: 'On Track'   },
  { value: 'DELAYED',   label: 'Delayed'    },
  { value: 'REROUTING', label: 'Rerouting'  },
  { value: 'IDLE',      label: 'Idle'       },
]

const filteredDrivers = computed(() => {
  let list = driversList.value
  if (statusFilter.value !== 'all') {
    list = list.filter(d => d.status === statusFilter.value)
  }
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    list = list.filter(d => (d.name ?? '').toLowerCase().includes(q) || String(d.id).includes(q))
  }
  return list
})

const onlineCount = computed(() =>
  driversList.value.filter(d => d.status !== 'IDLE' && d.status !== 'idle').length
)

const listColumns = [
  { name: 'name',       label: 'Driver',       field: 'name',         sortable: true,  align: 'left'  },
  { name: 'vehicleType',label: 'Vehicle',      field: 'vehicle_type', sortable: true,  align: 'left'  },
  { name: 'status',     label: 'Status',       field: 'status',       sortable: true,  align: 'center'},
  { name: 'speed',      label: 'Speed',        field: 'speed',        sortable: true,  align: 'right' },
  { name: 'heading',    label: 'Heading',      field: 'heading',      sortable: true,  align: 'right',
    format: (v) => v !== null ? Math.round(v) + '°' : '—' },
  { name: 'actions',    label: '',             field: 'id',           align: 'right',  style: 'width:90px' },
]

async function loadDrivers() {
  loading.value = true
  error.value = ''
  try {
    driversList.value = await driversApi.list()
  } catch {
    error.value = 'Could not load drivers — check backend connection'
    driversList.value = []
  } finally {
    loading.value = false
  }
}

async function createDriver() {
  if (!newDriver.value.name) {
    $q.notify({ type: 'warning', message: 'Please enter driver name', position: 'top-right' })
    return
  }
  saving.value = true
  try {
    await driversApi.create(newDriver.value)
    showCreateDialog.value = false
    newDriver.value = { name: '', vehicle_type: 'van', lat: 6.9271, lng: 79.8612 }
    $q.notify({ type: 'positive', message: 'Driver added successfully', position: 'top-right' })
    await loadDrivers()
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Failed: ' + e.message, position: 'top-right' })
  } finally {
    saving.value = false
  }
}

function openEditDriver(driver) {
  editDriver.value = { id: driver.id, name: driver.name, vehicle_type: driver.vehicle_type, status: (driver.status ?? 'IDLE').toUpperCase() }
  showEditDialog.value = true
}

async function updateDriver() {
  saving.value = true
  try {
    await driversApi.update(editDriver.value.id, editDriver.value)
    showEditDialog.value = false
    $q.notify({ type: 'positive', message: 'Driver updated', position: 'top-right' })
    await loadDrivers()
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Failed: ' + e.message, position: 'top-right' })
  } finally {
    saving.value = false
  }
}

async function removeDriver(driver) {
  $q.dialog({
    title: 'Remove Driver',
    message: `Deactivate ${driver.name ?? 'this driver'}?`,
    dark: true,
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      await driversApi.delete(driver.id)
      $q.notify({ type: 'positive', message: 'Driver deactivated', position: 'top-right' })
      await loadDrivers()
    } catch (e) {
      $q.notify({ type: 'negative', message: 'Failed: ' + e.message, position: 'top-right' })
    }
  })
}

onMounted(loadDrivers)
</script>

<style scoped>
.drivers-page {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 100vh;
  background: var(--color-bg-primary);
}

.drivers-toolbar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.search-input { width: 260px; flex-shrink: 0; }

:deep(.search-input .q-field__control) {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.09) !important;
  border-radius: 10px !important;
}

.filter-toggle, :deep(.q-btn-toggle) {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  border-radius: 10px !important;
  overflow: hidden;
}

.create-btn {
  border-radius: 10px !important;
  background: linear-gradient(135deg, #4a6cf7, #7c3aed) !important;
}

.error-banner {
  display: flex; align-items: center; gap: 10px; padding: 12px 16px;
  font-size: 13px; color: #ff3b5c;
  border-color: rgba(255,59,92,0.2) !important;
  background: rgba(255,59,92,0.06) !important;
}

/* Online strip */
.online-strip {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 14px;
  background: rgba(0,245,160,0.05); border: 1px solid rgba(0,245,160,0.12); border-radius: 10px;
}
.online-strip__label { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #00f5a0; }
.online-dot {
  width: 8px; height: 8px; border-radius: 50%; background: #00f5a0;
  box-shadow: 0 0 8px #00f5a0; animation: blink 1.8s ease-in-out infinite;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
.online-strip__total { font-size: 12px; color: #6b7280; }

/* Grid */
.drivers-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }

.driver-card {
  padding: 16px; display: flex; flex-direction: column; gap: 10px;
  cursor: pointer; transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.driver-card:hover { transform: translateY(-2px); box-shadow: 0 12px 40px rgba(0,0,0,0.5); }
.driver-card--selected { border-color: rgba(74,108,247,0.4) !important; box-shadow: 0 0 20px rgba(74,108,247,0.15); }

.driver-card__avatar {
  position: relative; width: 48px; height: 48px; border-radius: 14px;
  background: rgba(255,255,255,0.08); display: flex; align-items: center;
  justify-content: center; align-self: flex-start;
}
.driver-card__ring {
  position: absolute; bottom: -3px; right: -3px; width: 12px; height: 12px;
  border-radius: 50%; background: var(--s); border: 2px solid #0c1120; box-shadow: 0 0 6px var(--s);
}
.driver-card__name { font-size: 14px; font-weight: 600; color: #e8eaf6; margin: 0; }
.driver-card__vehicle { font-size: 11px; color: #8892a4; margin: 3px 0 0; display: flex; align-items: center; gap: 4px; }
.status-badge { font-size: 10px !important; font-weight: 600 !important; padding: 4px 10px !important; border-radius: 20px !important; align-self: flex-start; }

.driver-card__metrics { display: flex; flex-direction: column; gap: 5px; }
.metric { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #9ca3af; }

.driver-card__actions { display: flex; gap: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.06); flex-wrap: wrap; }

.no-drivers {
  grid-column: 1 / -1; display: flex; flex-direction: column; align-items: center;
  gap: 10px; padding: 60px; color: #4b5563; font-size: 14px;
}

/* List view */
.drivers-list-wrap { overflow: hidden; padding: 0; }
:deep(.drivers-table) { background: transparent !important; color: #e8eaf6 !important; }
:deep(.drivers-table-head th) {
  background: rgba(255,255,255,0.03) !important; color: #6b7280 !important;
  font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase !important;
  letter-spacing: 0.06em !important; border-bottom: 1px solid rgba(255,255,255,0.06) !important;
}
:deep(.q-table td) { border-bottom: 1px solid rgba(255,255,255,0.04) !important; color: #c5cae9 !important; }
:deep(.q-table tbody tr:hover) { background: rgba(255,255,255,0.04) !important; }
:deep(.q-table__bottom) { background: transparent !important; color: #6b7280 !important; border-top: 1px solid rgba(255,255,255,0.06) !important; }
.list-name { display: flex; align-items: center; gap: 10px; font-size: 13px; font-weight: 500; }
.list-avatar {
  width: 30px; height: 30px; border-radius: 8px; background: rgba(255,255,255,0.07);
  border: 1px solid var(--s); display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}

/* Dialog styles */
.dialog-card { min-width: 480px; background: var(--color-bg-elevated) !important; border: 1px solid rgba(255,255,255,0.09); border-radius: 16px !important; }
.dialog-header { display: flex; align-items: center; gap: 10px; border-bottom: 1px solid rgba(255,255,255,0.06); }
.dialog-title { font-size: 15px; font-weight: 600; color: #e8eaf6; flex: 1; }
.dialog-body { padding: 16px 20px; }
.dialog-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.dialog-field { display: flex; flex-direction: column; gap: 5px; }
.dialog-field.full-width { grid-column: 1 / -1; }
.dialog-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; color: #6b7280; }
:deep(.dialog-body .q-field__control) { background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.09) !important; border-radius: 9px !important; }
.dialog-actions { border-top: 1px solid rgba(255,255,255,0.06); }
</style>
