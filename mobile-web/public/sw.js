/* Service worker: cache shell untuk offline, tapi selalu utamakan jaringan
   agar pembaruan aplikasi langsung terlihat. Response API tidak pernah
   disimpan. */
const CACHE = 'apotek-pahala-shell-v2'
const SHELL = ['/', '/index.html', '/manifest.webmanifest', '/logo.svg', '/icon-192.png', '/icon-512.png']

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL).catch(() => undefined)),
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))),
    ),
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return
  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return
  if (url.pathname.startsWith('/api/')) return

  event.respondWith(
    caches.open(CACHE).then(async (cache) => {
      try {
        const response = await fetch(request)
        if (response.ok) cache.put(request, response.clone())
        return response
      } catch {
        const cached = await cache.match(request)
        if (cached) return cached
        if (request.mode === 'navigate') {
          return (await cache.match('/')) || (await cache.match('/index.html')) || Response.error()
        }
        return Response.error()
      }
    }),
  )
})
