<template>
  <q-page class="orders-page">

    <!-- ── Toolbar ──────────────────────────────────────────── -->
    <div class="orders-toolbar animate-fade-up">
      <q-input
        v-model="search"
        dense
        outlined
        placeholder="Search by address, driver or ID…"
        class="search-input"
        dark
        bg-color="transparent"
      >
        <template #prepend><q-icon name="search" color="grey-6" /></template>
        <template #append>
          <q-icon v-if="search" name="close" color="grey-6" class="cursor-pointer" @click="search = ''" />
        </template>
      </q-input>

      <q-tabs
        v-model="statusFilter"
        dense
        no-caps
        active-color="primary"
        indicator-color="primary"
        class="status-tabs"
      >
        <q-tab name="all"        label="All" />
        <q-tab name="PENDING"    label="Pending" />
        <q-tab name="ASSIGNED"   label="Assigned" />
        <q-tab name="IN_TRANSIT" label="In Transit" />
        <q-tab name="DELIVERED"  label="Delivered" />
        <q-tab name="FAILED"     label="Failed" />
      </q-tabs>

      <q-btn
        unelevated no-caps icon="add" label="New Order"
        color="primary" class="q-ml-auto create-btn"
        @click="showCreateDialog = true"
      />
      <q-btn flat no-caps icon="refresh" label="Refresh" color="grey-5" :loading="loading" @click="loadOrders" />
    </div>

    <!-- ── Stats strip ───────────────────────────────────────── -->
    <div class="stats-strip">
      <div v-for="(s, i) in statusCounts" :key="s.label" class="stat-pill animate-fade-up" :style="{ '--c': s.color, animationDelay: (i * 100 + 100) + 'ms' }">
        <span class="stat-pill__val">{{ s.count }}</span>
        <span class="stat-pill__label">{{ s.label }}</span>
      </div>
    </div>

    <!-- ── Error banner ──────────────────────────────────────── -->
    <div v-if="error" class="error-banner glass-panel">
      <q-icon name="cloud_off" size="18px" />
      <span>{{ error }}</span>
      <q-btn flat dense no-caps size="sm" label="Retry" color="primary" @click="loadOrders" />
    </div>

    <!-- ── Orders table ──────────────────────────────────────── -->
    <div class="glass-panel orders-table-wrap animate-fade-up delay-200">
      <q-table
        :rows="filteredOrders"
        :columns="columns"
        row-key="id"
        flat
        dark
        :loading="loading"
        :rows-per-page-options="[20, 50, 100]"
        rows-per-page-label="Per page"
        class="orders-table"
        table-header-class="orders-table-head"
        no-data-label="No orders found — create one to get started"
      >
        <!-- ID column -->
        <template #body-cell-id="props">
          <q-td :props="props">
            <span class="order-id-badge">#{{ props.value }}</span>
          </q-td>
        </template>

        <!-- Status column -->
        <template #body-cell-status="props">
          <q-td :props="props">
            <q-badge
              :label="STATUS_LABELS[props.value?.toLowerCase()] ?? props.value"
              :style="{ background: statusBg(props.value), color: statusColor(props.value) }"
              class="status-badge"
            />
          </q-td>
        </template>

        <!-- Driver column -->
        <template #body-cell-driver_name="props">
          <q-td :props="props">
            <span v-if="props.value" class="driver-name">
              <q-icon name="person" size="14px" color="grey-6" class="q-mr-xs" />
              {{ props.value }}
            </span>
            <span v-else class="unassigned">Unassigned</span>
          </q-td>
        </template>

        <!-- Address column -->
        <template #body-cell-destination_address="props">
          <q-td :props="props">
            <span class="address-cell">
              <q-icon name="place" size="14px" color="grey-7" class="q-mr-xs" />
              {{ props.value ?? '—' }}
            </span>
          </q-td>
        </template>

        <!-- Weight column -->
        <template #body-cell-weight="props">
          <q-td :props="props">
            <span class="weight-cell">{{ props.value }} <span class="unit">kg</span></span>
          </q-td>
        </template>

        <!-- Created column -->
        <template #body-cell-created_at="props">
          <q-td :props="props">
            <span class="time-cell">{{ fmtDate(props.value) }}</span>
            <br />
            <span class="time-sub">{{ fmtTime(props.value) }}</span>
          </q-td>
        </template>

        <!-- Actions column -->
        <template #body-cell-actions="props">
          <q-td :props="props">
            <q-btn flat round dense icon="edit" color="grey-6" size="sm" @click.stop="openEdit(props.row)">
              <q-tooltip>Edit order</q-tooltip>
            </q-btn>
            <q-btn flat round dense icon="delete_outline" color="negative" size="sm" @click.stop="cancelOrder(props.row)">
              <q-tooltip>Cancel order</q-tooltip>
            </q-btn>
          </q-td>
        </template>

        <!-- Loading state -->
        <template #loading>
          <q-inner-loading showing color="primary" />
        </template>
      </q-table>
    </div>

    <!-- ── Create Order Dialog ───────────────────────────────── -->
    <q-dialog v-model="showCreateDialog" persistent>
      <q-card class="dialog-card" dark>
        <q-card-section class="dialog-header">
          <q-icon name="add_circle" size="22px" color="primary" />
          <span class="dialog-title">New Delivery Order</span>
          <q-btn flat round dense icon="close" color="grey-6" v-close-popup />
        </q-card-section>

        <q-card-section class="dialog-body">
          <div class="dialog-form-grid">
            <div class="dialog-field full-width">
              <label class="dialog-label">Destination Address</label>
              <q-input v-model="newOrder.destination_address" dense outlined dark bg-color="transparent" placeholder="42 Galle Road, Colombo 03" />
            </div>
            <div class="dialog-field">
              <label class="dialog-label">Latitude</label>
              <q-input v-model.number="newOrder.lat" dense outlined dark bg-color="transparent" type="number" step="0.0001" />
            </div>
            <div class="dialog-field">
              <label class="dialog-label">Longitude</label>
              <q-input v-model.number="newOrder.lng" dense outlined dark bg-color="transparent" type="number" step="0.0001" />
            </div>
            <div class="dialog-field">
              <label class="dialog-label">Weight (kg)</label>
              <q-input v-model.number="newOrder.weight" dense outlined dark bg-color="transparent" type="number" step="0.1" />
            </div>
            <div class="dialog-field">
              <label class="dialog-label">Assign to Driver (ID)</label>
              <q-input v-model.number="newOrder.driver_id" dense outlined dark bg-color="transparent" type="number" placeholder="Optional" />
            </div>
          </div>
        </q-card-section>

        <q-card-actions class="dialog-actions" align="right">
          <q-btn flat no-caps label="Cancel" color="grey-5" v-close-popup />
          <q-btn unelevated no-caps label="Create Order" color="primary" :loading="creating" @click="createOrder" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ── Edit Order Dialog ─────────────────────────────────── -->
    <q-dialog v-model="showEditDialog" persistent>
      <q-card class="dialog-card" dark>
        <q-card-section class="dialog-header">
          <q-icon name="edit" size="22px" color="primary" />
          <span class="dialog-title">Edit Order #{{ editOrder.id }}</span>
          <q-btn flat round dense icon="close" color="grey-6" v-close-popup />
        </q-card-section>

        <q-card-section class="dialog-body">
          <div class="dialog-form-grid">
            <div class="dialog-field">
              <label class="dialog-label">Status</label>
              <q-select v-model="editOrder.status" :options="['PENDING','ASSIGNED','IN_TRANSIT','DELIVERED','FAILED']" dense outlined dark bg-color="transparent" />
            </div>
            <div class="dialog-field">
              <label class="dialog-label">Assign to Driver (ID)</label>
              <q-input v-model.number="editOrder.driver_id" dense outlined dark bg-color="transparent" type="number" />
            </div>
            <div class="dialog-field full-width">
              <label class="dialog-label">Destination Address</label>
              <q-input v-model="editOrder.destination_address" dense outlined dark bg-color="transparent" />
            </div>
            <div class="dialog-field">
              <label class="dialog-label">Weight (kg)</label>
              <q-input v-model.number="editOrder.weight" dense outlined dark bg-color="transparent" type="number" />
            </div>
          </div>
        </q-card-section>

        <q-card-actions class="dialog-actions" align="right">
          <q-btn flat no-caps label="Cancel" color="grey-5" v-close-popup />
          <q-btn unelevated no-caps label="Save Changes" color="primary" :loading="creating" @click="updateOrder" />
        </q-card-actions>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { ordersApi } from 'src/utils/api'

const $q = useQuasar()

const loading = ref(true)
const creating = ref(false)
const error = ref('')
const orders  = ref([])
const search  = ref('')
const statusFilter = ref('all')

const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const newOrder = ref({ destination_address: '', lat: 6.9271, lng: 79.8612, weight: 10, driver_id: null })
const editOrder = ref({ id: null, status: '', driver_id: null, destination_address: '', weight: 0 })

const STATUS_LABELS = {
  pending:    'Pending',
  assigned:   'Assigned',
  in_transit: 'In Transit',
  delivered:  'Delivered',
  failed:     'Failed',
}

const STATUS_COLORS_MAP = {
  pending:    { color: '#ffb800', bg: 'rgba(255,184,0,0.15)'   },
  assigned:   { color: '#4a6cf7', bg: 'rgba(74,108,247,0.15)'  },
  in_transit: { color: '#00f5a0', bg: 'rgba(0,245,160,0.15)'   },
  delivered:  { color: '#8892a4', bg: 'rgba(136,146,164,0.15)' },
  failed:     { color: '#ff3b5c', bg: 'rgba(255,59,92,0.15)'   },
}

function statusColor(s) { return STATUS_COLORS_MAP[(s ?? '').toLowerCase()]?.color ?? '#8892a4' }
function statusBg(s)    { return STATUS_COLORS_MAP[(s ?? '').toLowerCase()]?.bg    ?? 'rgba(136,146,164,0.12)' }

const columns = [
  { name: 'id',                  label: 'ID',      field: 'id',                  sortable: true,  align: 'left',  style: 'width:80px' },
  { name: 'destination_address', label: 'Address', field: 'destination_address', sortable: false, align: 'left'                      },
  { name: 'driver_name',         label: 'Driver',  field: 'driver_name',         sortable: true,  align: 'left',  style: 'width:180px' },
  { name: 'weight',              label: 'Weight',  field: 'weight',              sortable: true,  align: 'right', style: 'width:100px' },
  { name: 'status',              label: 'Status',  field: 'status',              sortable: true,  align: 'center', style: 'width:130px' },
  { name: 'created_at',          label: 'Created', field: 'created_at',          sortable: true,  align: 'left',  style: 'width:130px' },
  { name: 'actions',             label: '',         field: 'id',                 align: 'right',  style: 'width:90px' },
]

const filteredOrders = computed(() => {
  let list = orders.value
  if (statusFilter.value !== 'all') {
    list = list.filter(o => o.status === statusFilter.value)
  }
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    list = list.filter(o =>
      String(o.id).includes(q) ||
      (o.destination_address ?? '').toLowerCase().includes(q) ||
      (o.driver_name ?? '').toLowerCase().includes(q)
    )
  }
  return list
})

const statusCounts = computed(() => {
  const all = orders.value
  const cnt = (s) => all.filter(o => o.status === s).length
  return [
    { label: 'In Transit', count: cnt('IN_TRANSIT'), color: '#00f5a0' },
    { label: 'Assigned',   count: cnt('ASSIGNED'),   color: '#4a6cf7' },
    { label: 'Pending',    count: cnt('PENDING'),     color: '#ffb800' },
    { label: 'Delivered',  count: cnt('DELIVERED'),  color: '#8892a4' },
    { label: 'Failed',     count: cnt('FAILED'),      color: '#ff3b5c' },
  ]
})

function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}
function fmtTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

async function loadOrders() {
  loading.value = true
  error.value = ''
  try {
    orders.value = await ordersApi.list()
  } catch {
    error.value = 'Could not load orders — check backend connection'
    orders.value = []
  } finally {
    loading.value = false
  }
}

async function createOrder() {
  if (!newOrder.value.weight || !newOrder.value.lat || !newOrder.value.lng) {
    $q.notify({ type: 'warning', message: 'Please fill in all required fields', position: 'top-right' })
    return
  }
  creating.value = true
  try {
    await ordersApi.create(newOrder.value)
    showCreateDialog.value = false
    newOrder.value = { destination_address: '', lat: 6.9271, lng: 79.8612, weight: 10, driver_id: null }
    $q.notify({ type: 'positive', message: 'Order created successfully', position: 'top-right' })
    await loadOrders()
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Failed to create order: ' + e.message, position: 'top-right' })
  } finally {
    creating.value = false
  }
}

function openEdit(row) {
  editOrder.value = { id: row.id, status: row.status, driver_id: row.driver_id, destination_address: row.destination_address, weight: row.weight }
  showEditDialog.value = true
}

async function updateOrder() {
  creating.value = true
  try {
    await ordersApi.update(editOrder.value.id, editOrder.value)
    showEditDialog.value = false
    $q.notify({ type: 'positive', message: 'Order updated', position: 'top-right' })
    await loadOrders()
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Failed to update: ' + e.message, position: 'top-right' })
  } finally {
    creating.value = false
  }
}

async function cancelOrder(row) {
  $q.dialog({
    title: 'Cancel Order',
    message: `Cancel order #${row.id}? This will mark it as failed.`,
    dark: true,
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      await ordersApi.delete(row.id)
      $q.notify({ type: 'positive', message: `Order #${row.id} cancelled`, position: 'top-right' })
      await loadOrders()
    } catch (e) {
      $q.notify({ type: 'negative', message: 'Failed to cancel: ' + e.message, position: 'top-right' })
    }
  })
}

onMounted(loadOrders)
</script>

<style scoped>
.orders-page {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 100vh;
  background: var(--color-bg-primary);
}

/* ── Toolbar ── */
.orders-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.search-input { width: 300px; flex-shrink: 0; }

:deep(.search-input .q-field__control) {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.09) !important;
  border-radius: 10px !important;
  color: #e8eaf6 !important;
}

:deep(.search-input .q-field__control:hover) {
  border-color: rgba(74,108,247,0.5) !important;
}

.status-tabs {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 10px;
  overflow: hidden;
}

:deep(.status-tabs .q-tab) {
  font-size: 12px;
  font-weight: 500;
  color: #8892a4;
  min-height: 36px;
  padding: 0 14px;
}

:deep(.status-tabs .q-tab--active) {
  color: #e8eaf6;
}

.create-btn {
  border-radius: 10px !important;
  background: linear-gradient(135deg, #4a6cf7, #7c3aed) !important;
}

/* ── Error banner ── */
.error-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  font-size: 13px;
  color: #ff3b5c;
  border-color: rgba(255,59,92,0.2) !important;
  background: rgba(255,59,92,0.06) !important;
}

/* ── Stats strip ── */
.stats-strip { display: flex; gap: 10px; flex-wrap: wrap; }

.stat-pill {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 14px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 20px;
}

.stat-pill__val { font-size: 15px; font-weight: 700; color: var(--c); }
.stat-pill__label { font-size: 11px; color: #6b7280; }

/* ── Table ── */
.orders-table-wrap { flex: 1; overflow: hidden; padding: 0; }

:deep(.orders-table) { background: transparent !important; color: #e8eaf6 !important; }

:deep(.orders-table-head th) {
  background: rgba(255,255,255,0.03) !important;
  color: #6b7280 !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
  border-bottom: 1px solid rgba(255,255,255,0.06) !important;
}

:deep(.q-table tbody tr) {
  border-bottom: 1px solid rgba(255,255,255,0.04) !important;
  transition: background 0.15s ease;
}
:deep(.q-table tbody tr:hover) { background: rgba(255,255,255,0.04) !important; }
:deep(.q-table td) { border-bottom: none !important; color: #c5cae9 !important; }
:deep(.q-table__bottom) {
  background: transparent !important;
  color: #6b7280 !important;
  border-top: 1px solid rgba(255,255,255,0.06) !important;
}

.order-id-badge {
  font-size: 11px; font-weight: 700; color: #4a6cf7; font-family: monospace;
  background: rgba(74,108,247,0.1); padding: 3px 8px; border-radius: 6px;
}

.status-badge { font-size: 10px !important; font-weight: 600 !important; padding: 4px 10px !important; border-radius: 20px !important; letter-spacing: 0.04em; }
.driver-name { font-size: 13px; display: flex; align-items: center; }
.unassigned { font-size: 12px; color: #4b5563; font-style: italic; }
.address-cell { font-size: 12px; display: flex; align-items: center; }
.weight-cell { font-size: 13px; font-weight: 600; }
.unit { font-size: 10px; color: #6b7280; font-weight: 400; }
.time-cell { font-size: 12px; color: #c5cae9; }
.time-sub { font-size: 11px; color: #6b7280; }

/* ── Dialogs ── */
.dialog-card {
  min-width: 480px;
  background: var(--color-bg-elevated) !important;
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 16px !important;
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.dialog-title { font-size: 15px; font-weight: 600; color: #e8eaf6; flex: 1; }
.dialog-body { padding: 16px 20px; }

.dialog-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.dialog-field { display: flex; flex-direction: column; gap: 5px; }
.dialog-field.full-width { grid-column: 1 / -1; }
.dialog-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; color: #6b7280; }

:deep(.dialog-body .q-field__control) {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.09) !important;
  border-radius: 9px !important;
}

.dialog-actions { border-top: 1px solid rgba(255,255,255,0.06); }
</style>
