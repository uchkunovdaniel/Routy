// Data layer backed by the FastAPI backend (backend/). Every function is async and returns plain
// data in the same shapes the pages already use. Validation and sanitising happen on the server.

// Empty base = same origin; in dev, Vite proxies /api to the backend (see vite.config.ts).
const BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')
const TOKEN_KEY = 'tg_token'

let onUnauthorized = () => {}

export const session = {
  getToken: () => { try { return localStorage.getItem(TOKEN_KEY) } catch { return null } },
  setToken: (t) => { try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY) } catch { /* ignore */ } },
  // AuthProvider registers this so an expired/invalid token logs the user out.
  onUnauthorized: (fn) => { onUnauthorized = fn },
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, { method = 'GET', body, auth = false } = {}) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const token = session.getToken()
  if (auth && token) headers.Authorization = `Bearer ${token}`

  let res
  try {
    res = await fetch(`${BASE}${path}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) })
  } catch {
    throw new ApiError('Няма връзка със сървъра. Опитайте отново.', 0)
  }

  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    if (res.status === 401 && auth) onUnauthorized()
    // FastAPI: our errors carry a string detail; schema (422) errors carry a list.
    const message = typeof data?.detail === 'string' ? data.detail : 'Невалидни данни. Проверете полетата и опитайте отново.'
    throw new ApiError(message, res.status)
  }
  return data
}

const qs = (params) => {
  const p = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined && v !== ''))
  const s = p.toString()
  return s ? `?${s}` : ''
}

export const api = {
  listRoutes({ q = '', sort = 'new', author } = {}) {
    return request(`/api/routes${qs({ q: q.trim(), sort, author })}`)
  },
  async getRoute(id) {
    try {
      return await request(`/api/routes/${encodeURIComponent(id)}`)
    } catch (err) {
      if (err.status === 404) return null
      throw err
    }
  },
  createRoute(data) {
    return request('/api/routes', { method: 'POST', body: data, auth: true })
  },
  updateRoute(id, data) {
    return request(`/api/routes/${encodeURIComponent(id)}`, { method: 'PUT', body: data, auth: true })
  },
  deleteRoute(id) {
    return request(`/api/routes/${encodeURIComponent(id)}`, { method: 'DELETE', auth: true })
  },
  addReview(routeId, { rating, text }) {
    return request(`/api/routes/${encodeURIComponent(routeId)}/reviews`, { method: 'POST', body: { rating, text }, auth: true })
  },
  register({ name, email, password }) {
    return request('/api/auth/register', { method: 'POST', body: { name, email, password } })
  },
  login({ email, password }) {
    return request('/api/auth/login', { method: 'POST', body: { email, password } })
  },
  me() {
    return request('/api/auth/me', { auth: true })
  },
}
