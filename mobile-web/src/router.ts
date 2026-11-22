import { useEffect, useState } from 'react'

export function normalizeHash(hash: string): string {
  const value = hash.replace(/^#/, '')
  if (!value || value === '/') return '/'
  return value.startsWith('/') ? value : `/${value}`
}

export function navigate(path: string) {
  if (normalizeHash(window.location.hash) === path) return
  window.location.hash = path
}

export function useRoute(): string {
  const [route, setRoute] = useState<string>(() => normalizeHash(window.location.hash))

  useEffect(() => {
    const handler = () => {
      setRoute(normalizeHash(window.location.hash))
      window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior })
    }
    window.addEventListener('hashchange', handler)
    return () => window.removeEventListener('hashchange', handler)
  }, [])

  return route
}
