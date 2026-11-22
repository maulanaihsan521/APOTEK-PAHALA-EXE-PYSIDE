import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, clearSession, getToken, setSession } from '../services/api'
import type { User } from '../types'

interface AuthValue {
  user: User | null
  ready: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refresh: () => Promise<void>
  updateUser: (patch: Partial<User>) => void
}

const AuthContext = createContext<AuthValue | null>(null)

function applyTheme(theme: string) {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const dark = theme === 'dark' || (theme === 'auto' && prefersDark)
  document.documentElement.classList.toggle('dark', dark)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const stored = localStorage.getItem('apotek_user')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })
  const [ready, setReady] = useState(false)

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setUser(null)
      return
    }
    try {
      const profile = await api.get<User>('/auth/me')
      setUser(profile)
      localStorage.setItem('apotek_user', JSON.stringify(profile))
      applyTheme(profile.theme || 'light')
    } catch {
      // 401 is handled by the auth-expired event. Keep the cached profile for
      // transient/offline failures so the app shell stays usable.
      try {
        const stored = localStorage.getItem('apotek_user')
        setUser(stored ? JSON.parse(stored) : null)
      } catch {
        setUser(null)
      }
    }
  }, [])

  useEffect(() => {
    refresh().finally(() => setReady(true))
    const expired = () => {
      setUser(null)
      clearSession()
    }
    window.addEventListener('apotek-auth-expired', expired)
    return () => window.removeEventListener('apotek-auth-expired', expired)
  }, [refresh])

  useEffect(() => {
    if (user?.theme) applyTheme(user.theme)
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const listener = () => {
      if (user?.theme === 'auto') applyTheme('auto')
    }
    media.addEventListener('change', listener)
    return () => media.removeEventListener('change', listener)
  }, [user?.theme])

  const login = useCallback(async (username: string, password: string) => {
    const result = await api.login(username.trim(), password)
    setSession(result.access_token, result.user)
    setUser(result.user as User)
    applyTheme((result.user as User).theme || 'light')
  }, [])

  const logout = useCallback(() => {
    api.post('/auth/logout').catch(() => undefined)
    clearSession()
    setUser(null)
    window.location.hash = '/login'
  }, [])

  const updateUser = useCallback((patch: Partial<User>) => {
    setUser((current) => {
      if (!current) return current
      const next = { ...current, ...patch }
      localStorage.setItem('apotek_user', JSON.stringify(next))
      if (patch.theme) applyTheme(patch.theme)
      return next
    })
  }, [])

  const value = useMemo(
    () => ({ user, ready, login, logout, refresh, updateUser }),
    [user, ready, login, logout, refresh, updateUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth harus dipakai di dalam AuthProvider')
  return context
}
