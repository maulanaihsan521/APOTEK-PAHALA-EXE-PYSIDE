const BASE = import.meta.env.VITE_API_URL || '/api'
const TOKEN_KEY = 'apotek_token'
const USER_KEY = 'apotek_user'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setSession(token: string, user: unknown) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers = new Headers(options.headers || {})
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (!(options.body instanceof FormData) && options.body) {
    headers.set('Content-Type', 'application/json')
  }
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, { ...options, headers })
  } catch {
    throw new Error('Tidak dapat terhubung ke server. Periksa koneksi Anda.')
  }
  if (response.status === 401) {
    clearSession()
    window.dispatchEvent(new Event('apotek-auth-expired'))
  }
  if (!response.ok) {
    let message = 'Terjadi kesalahan. Silakan coba lagi.'
    try {
      const payload = await response.json()
      if (typeof payload.detail === 'string') message = payload.detail
      else if (Array.isArray(payload.detail)) {
        message = payload.detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join(', ')
      }
    } catch {
      // biarkan pesan default
    }
    throw new Error(message)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body === undefined ? undefined : JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body === undefined ? undefined : JSON.stringify(body) }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
  postForm: <T>(path: string, data: FormData) => request<T>(path, { method: 'POST', body: data }),
  login: async (username: string, password: string) => {
    const body = new URLSearchParams({ username, password })
    const response = await fetch(`${BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    })
    if (!response.ok) {
      let message = 'Nama pengguna atau password salah.'
      try {
        const payload = await response.json()
        if (typeof payload.detail === 'string') message = payload.detail
      } catch {
        // abaikan
      }
      throw new Error(message)
    }
    return response.json() as Promise<{ access_token: string; user: unknown }>
  },
  download: async (path: string, filename: string) => {
    const token = getToken()
    let response: Response
    try {
      response = await fetch(`${BASE}${path}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
    } catch {
      throw new Error('Tidak dapat terhubung ke server. Periksa koneksi Anda.')
    }
    if (!response.ok) {
      let message = 'Unduhan gagal.'
      try {
        const payload = await response.json()
        if (typeof payload.detail === 'string') message = payload.detail
      } catch {
        // abaikan
      }
      throw new Error(message)
    }
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(url)
  },
}
