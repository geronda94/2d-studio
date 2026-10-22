// AUTH_PLAN Ф1: состояние пользователя, вход/регистрация/выход.
// currentUser/authMode — модульные синглтоны (шарится между компонентами).
import { ref } from 'vue'

const currentUser = ref(null)
const authMode = ref('off')
const ready = ref(false)
let loadPromise = null

function readCookie(name) {
  const m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'))
  return m ? decodeURIComponent(m[1]) : null
}

async function authRequest(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase()
  const headers = new Headers(options.headers || {})
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrf = readCookie('csrf')
    if (csrf) headers.set('X-CSRF-Token', csrf)
  }
  if (options.body) headers.set('Content-Type', 'application/json')
  const res = await fetch(`/api/auth${path}`, {
    credentials: 'include',
    method,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : 'Ошибка запроса'
    throw new Error(detail)
  }
  return data
}

async function refresh() {
  try {
    const data = await authRequest('/me')
    currentUser.value = data.user || null
    authMode.value = data.mode || 'off'
  } catch {
    currentUser.value = null
  } finally {
    ready.value = true
  }
}

// Глобальная реакция на протухшую сессию (см. services/api.js)
if (typeof window !== 'undefined') {
  window.addEventListener('auth:unauthorized', () => { currentUser.value = null })
}

export function useAuth() {
  const ensureLoaded = async () => {
    if (ready.value) return
    if (!loadPromise) loadPromise = refresh()
    await loadPromise
  }

  const login = async (email, password) => {
    const data = await authRequest('/login', { method: 'POST', body: { email, password } })
    currentUser.value = data.user
    authMode.value = data.mode || 'on'
    ready.value = true
    return data.user
  }

  const register = async (email, password, displayName) => {
    const data = await authRequest('/register', {
      method: 'POST',
      body: { email, password, display_name: displayName || undefined },
    })
    currentUser.value = data.user
    authMode.value = data.mode || 'on'
    ready.value = true
    return data.user
  }

  const logout = async () => {
    try { await authRequest('/logout', { method: 'POST' }) } catch { /* ignore */ }
    currentUser.value = null
    loadPromise = null
  }

  return { currentUser, authMode, ready, ensureLoaded, refresh, login, register, logout }
}
