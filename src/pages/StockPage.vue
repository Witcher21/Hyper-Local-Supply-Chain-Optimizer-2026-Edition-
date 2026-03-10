<template>
  <q-page class="stock-page">

    <!-- ── KPI cards ─────────────────────────────────────────── -->
    <div class="stock-kpis animate-fade-up">
      <div v-for="(kpi, i) in stockKPIs" :key="kpi.label" class="stock-kpi glass-panel" :style="{ animationDelay: (i * 100) + 'ms' }">
        <div class="stock-kpi__icon-wrap" :style="{ background: kpi.bg }">
          <q-icon :name="kpi.icon" size="20px" :style="{ color: kpi.color }" />
        </div>
        <div>
          <p class="stock-kpi__val">{{ kpi.value }}</p>
          <p class="stock-kpi__label">{{ kpi.label }}</p>
        </div>
      </div>

      <!-- Alert banner -->
      <div class="low-stock-banner" v-if="lowStockCount > 0">
        <q-icon name="warning" size="18px" color="warning" />
        <span>{{ lowStockCount }} item{{ lowStockCount !== 1 ? 's' : '' }} below reorder threshold</span>
        <q-btn flat dense no-caps size="sm" label="Filter" color="warning" @click="categoryFilter = 'low'" />
      </div>
    </div>

    <!-- ── Toolbar ──────────────────────────────────────────── -->
    <div class="stock-toolbar animate-fade-up delay-200">
      <q-input
        v-model="search" dense outlined placeholder="Search inventory…"
        class="search-input" dark bg-color="transparent"
      >
        <template #prepend><q-icon name="search" color="grey-6" /></template>
        <template #append>
          <q-icon v-if="search" name="close" color="grey-6" class="cursor-pointer" @click="search = ''" />
        </template>
      </q-input>

      <q-btn-toggle
        v-model="categoryFilter" no-caps dense rounded
        toggle-color="primary" text-color="grey-5"
        :options="categoryOptions" class="cat-toggle"
      />

      <q-btn
        unelevated no-caps icon="add" label="Add Item"
        color="primary" class="q-ml-auto create-btn"
        @click="showCreateDialog = true"
      />

      <q-btn flat no-caps icon="refresh" label="Refresh" color="grey-5" :loading="loading" @click="loadInventory" />
    </div>

    <!-- ── Error banner ──────────────────────────────────────── -->
    <div v-if="error" class="error-banner glass-panel">
      <q-icon name="cloud_off" size="18px" />
      <span>{{ error }}</span>
      <q-btn flat dense no-caps size="sm" label="Retry" color="primary" @click="loadInventory" />
    </div>

    <!-- ── Inventory table ───────────────────────────────────── -->
    <div class="glass-panel stock-table-wrap animate-fade-up delay-300">
      <q-table
        :rows="filteredItems"
        :columns="columns"
        row-key="id"
        flat dark
        :loading="loading"
        class="stock-table"
        table-header-class="stock-table-head"
        :rows-per-page-options="[20, 50]"
        no-data-label="No inventory items — add some to get started"
      >
        <!-- Product column -->
        <template #body-cell-name="props">
          <q-td :props="props">
            <div class="product-cell">
              <div class="product-cell__icon" :style="{ background: categoryColor(props.row.category) + '20' }">
                <q-icon :name="categoryIcon(props.row.category)" size="16px" :style="{ color: categoryColor(props.row.category) }" />
              </div>
              <div>
                <p class="product-name">{{ props.value }}</p>
                <p class="product-sku">SKU: {{ props.row.sku }}</p>
              </div>
            </div>
          </q-td>
        </template>

        <!-- Category column -->
        <template #body-cell-category="props">
          <q-td :props="props">
            <q-badge
              :label="props.value"
              :style="{ background: categoryColor(props.value) + '20', color: categoryColor(props.value) }"
              class="cat-badge"
            />
          </q-td>
        </template>

        <!-- Stock level column -->
        <template #body-cell-stock="props">
          <q-td :props="props">
            <div class="stock-cell">
              <span :class="stockClass(props.row)" class="stock-val">{{ props.value }}</span>
              <span class="stock-unit">{{ props.row.unit }}</span>
              <div class="stock-bar">
                <div
                  class="stock-fill"
                  :style="{ width: stockPct(props.row) + '%', background: stockBarColor(props.row) }"
                />
              </div>
            </div>
          </q-td>
        </template>

        <!-- Status column -->
        <template #body-cell-stock_status="props">
          <q-td :props="props">
            <q-badge
              :label="props.value"
              :style="{ background: stockStatusBg(props.value), color: stockStatusColor(props.value) }"
              class="status-badge"
            />
          </q-td>
        </template>

        <!-- Reorder column -->
        <template #body-cell-reorder_point="props">
          <q-td :props="props">
            <span class="reorder-val">{{ props.value }} {{ props.row.unit }}</span>
          </q-td>
        </template>

        <!-- Value column -->
        <template #body-cell-value="props">
          <q-td :props="props">
            <span class="value-cell">LKR {{ (props.value ?? 0).toLocaleString() }}</span>
          </q-td>
        </template>

        <!-- Actions column -->
        <template #body-cell-actions="props">
          <q-td :props="props">
            <q-btn flat round dense icon="add_circle_outline" color="positive" size="sm" @click.stop="openRestock(props.row)">
              <q-tooltip>Restock</q-tooltip>
            </q-btn>
            <q-btn flat round dense icon="edit" color="grey-6" size="sm" @click.stop="openEdit(props.row)">
              <q-tooltip>Edit</q-tooltip>
            </q-btn>
            <q-btn flat round dense icon="delete_outline" color="negative" size="sm" @click.stop="deleteItem(props.row)">
              <q-tooltip>Delete</q-tooltip>
            </q-btn>
          </q-td>
        </template>

        <template #loading>
          <q-inner-loading showing color="primary" />
        </template>
      </q-table>
    </div>

    <!-- ── Create Item Dialog ────────────────────────────────── -->
    <q-dialog v-model="showCreateDialog" persistent>
      <q-card class="dialog-card" dark>
        <q-card-section class="dialog-header">
          <q-icon name="add_circle" size="22px" color="primary" />
          <span class="dialog-title">Add Inventory Item</span>
          <q-btn flat round dense icon="close" color="grey-6" v-close-popup />
        </q-card-section>
        <q-card-section class="dialog-body">
          <div class="dialog-form-grid">
            <div class="dialog-field"><label class="dialog-label">Product Name</label>
              <q-input v-model="formItem.name" dense outlined dark bg-color="transparent" /></div>
            <div class="dialog-field"><label class="dialog-label">SKU</label>
              <q-input v-model="formItem.sku" dense outlined dark bg-color="transparent" /></div>
            <div class="dialog-field"><label class="dialog-label">Category</label>
              <q-select v-model="formItem.category" :options="categoryNames" dense outlined dark bg-color="transparent" /></div>
            <div class="dialog-field"><label class="dialog-label">Unit</label>
              <q-input v-model="formItem.unit" dense outlined dark bg-color="transparent" placeholder="bags, bottles..." /></div>
            <div class="dialog-field"><label class="dialog-label">Initial Stock</label>
              <q-input v-model.number="formItem.stock" dense outlined dark bg-color="transparent" type="number" /></div>
            <div class="dialog-field"><label class="dialog-label">Reorder Point</label>
              <q-input v-model.number="formItem.reorder_point" dense outlined dark bg-color="transparent" type="number" /></div>
            <div class="dialog-field"><label class="dialog-label">Unit Cost (LKR)</label>
              <q-input v-model.number="formItem.unit_cost" dense outlined dark bg-color="transparent" type="number" /></div>
            <div class="dialog-field"><label class="dialog-label">Supplier</label>
              <q-input v-model="formItem.supplier" dense outlined dark bg-color="transparent" /></div>
          </div>
        </q-card-section>
        <q-card-actions class="dialog-actions" align="right">
          <q-btn flat no-caps label="Cancel" color="grey-5" v-close-popup />
          <q-btn unelevated no-caps label="Add Item" color="primary" :loading="saving" @click="createItem" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ── Edit Item Dialog ──────────────────────────────────── -->
    <q-dialog v-model="showEditDialog" persistent>
      <q-card class="dialog-card" dark>
        <q-card-section class="dialog-header">
          <q-icon name="edit" size="22px" color="primary" />
          <span class="dialog-title">Edit {{ formItem.name }}</span>
          <q-btn flat round dense icon="close" color="grey-6" v-close-popup />
        </q-card-section>
        <q-card-section class="dialog-body">
          <div class="dialog-form-grid">
            <div class="dialog-field"><label class="dialog-label">Product Name</label>
              <q-input v-model="formItem.name" dense outlined dark bg-color="transparent" /></div>
            <div class="dialog-field"><label class="dialog-label">SKU</label>
              <q-input v-model="formItem.sku" dense outlined dark bg-color="transparent" /></div>
            <div class="dialog-field"><label class="dialog-label">Category</label>
              <q-select v-model="formItem.category" :options="categoryNames" dense outlined dark bg-color="transparent" /></div>
            <div class="dialog-field"><label class="dialog-label">Unit</label>
              <q-input v-model="formItem.unit" dense outlined dark bg-color="transparent" /></div>
            <div class="dialog-field"><label class="dialog-label">Current Stock</label>
              <q-input v-model.number="formItem.stock" dense outlined dark bg-color="transparent" type="number" /></div>
            <div class="dialog-field"><label class="dialog-label">Reorder Point</label>
              <q-input v-model.number="formItem.reorder_point" dense outlined dark bg-color="transparent" type="number" /></div>
            <div class="dialog-field"><label class="dialog-label">Unit Cost (LKR)</label>
              <q-input v-model.number="formItem.unit_cost" dense outlined dark bg-color="transparent" type="number" /></div>
            <div class="dialog-field"><label class="dialog-label">Supplier</label>
              <q-input v-model="formItem.supplier" dense outlined dark bg-color="transparent" /></div>
          </div>
        </q-card-section>
        <q-card-actions class="dialog-actions" align="right">
          <q-btn flat no-caps label="Cancel" color="grey-5" v-close-popup />
          <q-btn unelevated no-caps label="Save Changes" color="primary" :loading="saving" @click="updateItem" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ── Restock Dialog ────────────────────────────────────── -->
    <q-dialog v-model="showRestockDialog" persistent>
      <q-card class="dialog-card" dark style="min-width:360px">
        <q-card-section class="dialog-header">
          <q-icon name="add_circle" size="22px" color="positive" />
          <span class="dialog-title">Restock {{ restockItem.name }}</span>
          <q-btn flat round dense icon="close" color="grey-6" v-close-popup />
        </q-card-section>
        <q-card-section class="dialog-body">
          <p style="color:#9ca3af;font-size:13px;margin:0 0 12px">Current: {{ restockItem.currentStock }} {{ restockItem.unit }}</p>
          <div class="dialog-field">
            <label class="dialog-label">Add Quantity</label>
            <q-input v-model.number="restockQty" dense outlined dark bg-color="transparent" type="number" :suffix="restockItem.unit" />
          </div>
        </q-card-section>
        <q-card-actions class="dialog-actions" align="right">
          <q-btn flat no-caps label="Cancel" color="grey-5" v-close-popup />
          <q-btn unelevated no-caps label="Restock" color="positive" :loading="saving" @click="doRestock" />
        </q-card-actions>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { inventoryApi } from 'src/utils/api'

const $q = useQuasar()

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const items = ref([])

const search         = ref('')
const categoryFilter = ref('all')

const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showRestockDialog = ref(false)
const editingId = ref(null)
const restockQty = ref(0)
const restockItem = ref({ name: '', currentStock: 0, unit: '', id: null })

const EMPTY_FORM = { name: '', sku: '', category: 'Grains', stock: 0, reorder_point: 0, unit: 'bags', unit_cost: 100, supplier: '' }
const formItem = ref({ ...EMPTY_FORM })

const CATEGORY_META = {
  Grains:     { color: '#ffb800', icon: 'grass'           },
  Oils:       { color: '#ff9500', icon: 'opacity'         },
  Canned:     { color: '#4a6cf7', icon: 'inventory_2'     },
  Dairy:      { color: '#00c4ff', icon: 'water_drop'      },
  Legumes:    { color: '#00f5a0', icon: 'eco'             },
  Condiments: { color: '#ff3b5c', icon: 'restaurant'      },
  Spices:     { color: '#c084fc', icon: 'spa'             },
  Beverages:  { color: '#22d3ee', icon: 'local_drink'     },
  Household:  { color: '#8892a4', icon: 'home'            },
}
const categoryNames = Object.keys(CATEGORY_META)

function categoryColor(c) { return CATEGORY_META[c]?.color ?? '#8892a4' }
function categoryIcon(c)  { return CATEGORY_META[c]?.icon  ?? 'inventory' }

function stockPct(item) {
  const max = (item.reorder_point || 1) * 4
  return Math.min(100, Math.round(item.stock / max * 100))
}

function stockBarColor(item) {
  const s = item.stock_status || ''
  if (s === 'Out of Stock') return '#ff3b5c'
  if (s === 'Low Stock')    return '#ffb800'
  if (s === 'Watch')        return '#f97316'
  return '#00f5a0'
}

function stockClass(item) {
  const s = item.stock_status || ''
  if (s === 'Out of Stock') return 'stock-out'
  if (s === 'Low Stock')    return 'stock-low'
  return 'stock-ok'
}

const STOCK_STATUS_COLORS = {
  'In Stock':    { color: '#00f5a0', bg: 'rgba(0,245,160,0.15)'   },
  'Watch':       { color: '#f97316', bg: 'rgba(249,115,22,0.15)'  },
  'Low Stock':   { color: '#ffb800', bg: 'rgba(255,184,0,0.15)'   },
  'Out of Stock':{ color: '#ff3b5c', bg: 'rgba(255,59,92,0.15)'   },
}

function stockStatusColor(s) { return STOCK_STATUS_COLORS[s]?.color ?? '#8892a4' }
function stockStatusBg(s)    { return STOCK_STATUS_COLORS[s]?.bg    ?? 'rgba(136,146,164,0.12)' }

const categories = ['all', ...categoryNames, 'low']
const categoryOptions = categories.map(c => ({
  value: c,
  label: c === 'all' ? 'All' : c === 'low' ? '⚠ Low' : c,
}))

const lowStockCount = computed(() =>
  items.value.filter(i => i.stock_status === 'Low Stock' || i.stock_status === 'Out of Stock').length
)

const filteredItems = computed(() => {
  let list = [...items.value]
  if (categoryFilter.value === 'low') {
    list = list.filter(i => i.stock_status === 'Low Stock' || i.stock_status === 'Out of Stock')
  } else if (categoryFilter.value !== 'all') {
    list = list.filter(i => i.category === categoryFilter.value)
  }
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    list = list.filter(i =>
      i.name.toLowerCase().includes(q) ||
      i.sku.toLowerCase().includes(q) ||
      (i.supplier ?? '').toLowerCase().includes(q)
    )
  }
  return list
})

const stockKPIs = computed(() => [
  { label: 'Total SKUs',    value: items.value.length,  icon: 'inventory_2', color: '#4a6cf7', bg: 'rgba(74,108,247,0.15)' },
  { label: 'In Stock',      value: items.value.filter(i => i.stock_status === 'In Stock').length,     icon: 'check_circle',       color: '#00f5a0', bg: 'rgba(0,245,160,0.15)'  },
  { label: 'Low / Out',     value: lowStockCount.value,                                            icon: 'warning',            color: '#ffb800', bg: 'rgba(255,184,0,0.15)'  },
  { label: 'Stock Value',   value: 'LKR ' + Math.round(items.value.reduce((s, i) => s + (i.value ?? 0), 0) / 1000) + 'K', icon: 'payments', color: '#c084fc', bg: 'rgba(192,132,252,0.15)' },
])

const columns = [
  { name: 'name',         label: 'Product',       field: 'name',         sortable: true,  align: 'left'   },
  { name: 'sku',          label: 'SKU',           field: 'sku',          sortable: true,  align: 'left',  style: 'width:110px' },
  { name: 'category',     label: 'Category',      field: 'category',     sortable: true,  align: 'left',  style: 'width:130px' },
  { name: 'stock',        label: 'Current Stock', field: 'stock',        sortable: true,  align: 'left',  style: 'width:180px' },
  { name: 'reorder_point', label: 'Reorder At',    field: 'reorder_point', sortable: false, align: 'right', style: 'width:110px' },
  { name: 'stock_status',  label: 'Status',        field: 'stock_status',  sortable: true,  align: 'center',style: 'width:130px' },
  { name: 'supplier',     label: 'Supplier',      field: 'supplier',     sortable: true,  align: 'left'   },
  { name: 'value',        label: 'Total Value',   field: 'value',        sortable: true,  align: 'right', style: 'width:140px' },
  { name: 'actions',      label: '',              field: 'id',           align: 'right',  style: 'width:110px' },
]

async function loadInventory() {
  loading.value = true
  error.value = ''
  try {
    items.value = await inventoryApi.list()
  } catch {
    error.value = 'Could not load inventory — check backend connection'
    items.value = []
  } finally {
    loading.value = false
  }
}

async function createItem() {
  if (!formItem.value.name || !formItem.value.sku) {
    $q.notify({ type: 'warning', message: 'Name and SKU are required', position: 'top-right' })
    return
  }
  saving.value = true
  try {
    await inventoryApi.create(formItem.value)
    showCreateDialog.value = false
    formItem.value = { ...EMPTY_FORM }
    $q.notify({ type: 'positive', message: 'Item added', position: 'top-right' })
    await loadInventory()
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Failed: ' + e.message, position: 'top-right' })
  } finally {
    saving.value = false
  }
}

function openEdit(row) {
  editingId.value = row.id
  formItem.value = { name: row.name, sku: row.sku, category: row.category, stock: row.stock, reorder_point: row.reorder_point, unit: row.unit, unit_cost: row.unit_cost, supplier: row.supplier }
  showEditDialog.value = true
}

async function updateItem() {
  saving.value = true
  try {
    await inventoryApi.update(editingId.value, formItem.value)
    showEditDialog.value = false
    $q.notify({ type: 'positive', message: 'Item updated', position: 'top-right' })
    await loadInventory()
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Failed: ' + e.message, position: 'top-right' })
  } finally {
    saving.value = false
  }
}

function openRestock(row) {
  restockItem.value = { id: row.id, name: row.name, currentStock: row.stock, unit: row.unit }
  restockQty.value = 0
  showRestockDialog.value = true
}

async function doRestock() {
  if (!restockQty.value || restockQty.value <= 0) {
    $q.notify({ type: 'warning', message: 'Enter a valid quantity', position: 'top-right' })
    return
  }
  saving.value = true
  try {
    await inventoryApi.update(restockItem.value.id, { stock: restockItem.value.currentStock + restockQty.value })
    showRestockDialog.value = false
    $q.notify({ type: 'positive', message: `Restocked +${restockQty.value} ${restockItem.value.unit}`, position: 'top-right' })
    await loadInventory()
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Failed: ' + e.message, position: 'top-right' })
  } finally {
    saving.value = false
  }
}

async function deleteItem(row) {
  $q.dialog({ title: 'Delete Item', message: `Delete "${row.name}"?`, dark: true, cancel: true, persistent: true })
    .onOk(async () => {
      try {
        await inventoryApi.delete(row.id)
        $q.notify({ type: 'positive', message: 'Item deleted', position: 'top-right' })
        await loadInventory()
      } catch (e) {
        $q.notify({ type: 'negative', message: 'Failed: ' + e.message, position: 'top-right' })
      }
    })
}

onMounted(loadInventory)
</script>

<style scoped>
.stock-page { padding: 20px 24px; display: flex; flex-direction: column; gap: 14px; min-height: 100vh; background: var(--color-bg-primary); }

/* KPIs */
.stock-kpis { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.stock-kpi { display: flex; align-items: center; gap: 12px; padding: 12px 16px; min-width: 160px; }
.stock-kpi__icon-wrap { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.stock-kpi__val { font-size: 22px; font-weight: 700; color: #e8eaf6; margin: 0; line-height: 1; }
.stock-kpi__label { font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.07em; margin: 3px 0 0; }
.low-stock-banner { flex: 1; display: flex; align-items: center; gap: 8px; padding: 10px 14px; background: rgba(255,184,0,0.07); border: 1px solid rgba(255,184,0,0.2); border-radius: 10px; font-size: 13px; color: #ffb800; min-width: 0; }

/* Toolbar */
.stock-toolbar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.search-input { width: 280px; flex-shrink: 0; }
:deep(.search-input .q-field__control) { background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.09) !important; border-radius: 10px !important; }
.cat-toggle,:deep(.q-btn-toggle) { background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.07) !important; border-radius: 10px !important; }
.create-btn { border-radius: 10px !important; background: linear-gradient(135deg, #4a6cf7, #7c3aed) !important; }

.error-banner { display: flex; align-items: center; gap: 10px; padding: 12px 16px; font-size: 13px; color: #ff3b5c; border-color: rgba(255,59,92,0.2) !important; background: rgba(255,59,92,0.06) !important; }

/* Table */
.stock-table-wrap { overflow: hidden; padding: 0; }
:deep(.stock-table) { background: transparent !important; color: #e8eaf6 !important; }
:deep(.stock-table-head th) { background: rgba(255,255,255,0.03) !important; color: #6b7280 !important; font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; border-bottom: 1px solid rgba(255,255,255,0.06) !important; }
:deep(.q-table td) { border-bottom: 1px solid rgba(255,255,255,0.04) !important; color: #c5cae9 !important; }
:deep(.q-table tbody tr:hover) { background: rgba(255,255,255,0.04) !important; }
:deep(.q-table__bottom) { background: transparent !important; color: #6b7280 !important; border-top: 1px solid rgba(255,255,255,0.06) !important; }

.product-cell { display: flex; align-items: center; gap: 10px; }
.product-cell__icon { width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.product-name { font-size: 13px; font-weight: 500; color: #e8eaf6; margin: 0; }
.product-sku  { font-size: 10px; color: #6b7280; font-family: monospace; margin: 2px 0 0; }
.cat-badge    { font-size: 10px !important; padding: 3px 8px !important; border-radius: 20px !important; }
.status-badge { font-size: 10px !important; padding: 4px 10px !important; border-radius: 20px !important; font-weight: 600 !important; }
.stock-cell { display: flex; align-items: center; gap: 6px; }
.stock-val  { font-size: 14px; font-weight: 700; }
.stock-unit { font-size: 10px; color: #6b7280; }
.stock-ok   { color: #00f5a0; }
.stock-low  { color: #ffb800; }
.stock-out  { color: #ff3b5c; }
.stock-bar { width: 60px; height: 4px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow: hidden; flex-shrink: 0; }
.stock-fill { height: 100%; border-radius: 2px; transition: width 0.4s ease; }
.reorder-val { font-size: 12px; color: #9ca3af; }
.value-cell  { font-size: 12px; font-weight: 600; color: #c084fc; }

/* Dialogs */
.dialog-card { min-width: 480px; background: var(--color-bg-elevated) !important; border: 1px solid rgba(255,255,255,0.09); border-radius: 16px !important; }
.dialog-header { display: flex; align-items: center; gap: 10px; border-bottom: 1px solid rgba(255,255,255,0.06); }
.dialog-title { font-size: 15px; font-weight: 600; color: #e8eaf6; flex: 1; }
.dialog-body { padding: 16px 20px; }
.dialog-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.dialog-field { display: flex; flex-direction: column; gap: 5px; }
.dialog-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; color: #6b7280; }
:deep(.dialog-body .q-field__control) { background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.09) !important; border-radius: 9px !important; }
.dialog-actions { border-top: 1px solid rgba(255,255,255,0.06); }
</style>
