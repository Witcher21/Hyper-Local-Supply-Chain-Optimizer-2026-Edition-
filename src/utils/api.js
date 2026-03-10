/**
 * Central API helper — all REST calls go through here.
 * Reads config from environment variables or localStorage overrides.
 */

const API_KEY     = import.meta.env.VITE_API_KEY      ?? 'demo-key'
const BUSINESS_ID = Number(import.meta.env.VITE_BUSINESS_ID ?? '1')
const API_HOST    = import.meta.env.VITE_API_HOST     ?? 'localhost:8000'

function baseUrl() {
  const protocol = window.location.protocol
  return `${protocol}//${API_HOST}`
}

/**
 * Generic fetch wrapper with auth. Returns parsed JSON or throws.
 */
async function apiFetch(path, options = {}) {
  const sep = path.includes('?') ? '&' : '?'
  const url = `${baseUrl()}${path}${sep}api_key=${encodeURIComponent(API_KEY)}`

  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })

  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText)
    throw new Error(`API ${res.status}: ${detail}`)
  }

  return res.json()
}

// ── Drivers ──────────────────────────────────────────────────

export const driversApi = {
  list: () =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/drivers`),

  create: (data) =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/drivers`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (driverId, data) =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/drivers/${driverId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (driverId) =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/drivers/${driverId}`, {
      method: 'DELETE',
    }),

  orders: (driverId) =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/drivers/${driverId}/orders`),
}

// ── Orders ───────────────────────────────────────────────────

export const ordersApi = {
  list: (limit = 200) =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/orders?limit=${limit}`),

  create: (data) =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/orders`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (orderId, data) =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/orders/${orderId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (orderId) =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/orders/${orderId}`, {
      method: 'DELETE',
    }),
}

// ── Inventory ────────────────────────────────────────────────

export const inventoryApi = {
  list: (category = null) => {
    const extra = category ? `&category=${encodeURIComponent(category)}` : ''
    return apiFetch(`/api/businesses/${BUSINESS_ID}/inventory` + extra)
  },

  create: (data) =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/inventory`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (itemId, data) =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/inventory/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (itemId) =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/inventory/${itemId}`, {
      method: 'DELETE',
    }),
}

// ── Settings ─────────────────────────────────────────────────

export const settingsApi = {
  load: () =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/settings`),

  save: (settings) =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/settings`, {
      method: 'PUT',
      body: JSON.stringify({ settings }),
    }),
}

// ── Route Optimizer ──────────────────────────────────────────

export const optimizerApi = {
  run: () =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/optimize`, {
      method: 'POST',
    }),
}

// ── Dashboard ────────────────────────────────────────────────

export const dashboardApi = {
  kpis: () =>
    apiFetch(`/api/businesses/${BUSINESS_ID}/dashboard`),
}

// ── Health ───────────────────────────────────────────────────

export const healthApi = {
  check: () =>
    apiFetch('/health'),
}

export { API_KEY, BUSINESS_ID, API_HOST, baseUrl }
