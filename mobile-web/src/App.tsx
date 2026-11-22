import { useEffect } from 'react'
import { Loader2, MapPinOff } from 'lucide-react'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import { navigate, useRoute } from './router'
import { LogoMark } from './components/Illustration'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Prediction from './pages/Prediction'
import Stock from './pages/Stock'
import More from './pages/More'
import Sales from './pages/Sales'
import Weather from './pages/Weather'
import Procurement from './pages/Procurement'
import Reports from './pages/Reports'
import Activity from './pages/Activity'
import Settings from './pages/Settings'
import { AppShell, PageHeader } from './components/Layout'
import { Button, EmptyState } from './components/ui'

function Splash() {
  return (
    <div className="phone-shell flex min-h-dvh flex-col items-center justify-center bg-gradient-to-br from-[#0B5F52] via-[#087F6B] to-[#149C80] text-white">
      <div className="flex h-20 w-20 items-center justify-center rounded-[24px] bg-white shadow-[0_18px_40px_rgba(3,40,34,.3)]">
        <LogoMark size={56} />
      </div>
      <p className="mt-4 text-[19px] font-extrabold tracking-[-0.01em]">Apotek Pahala</p>
      <p className="mt-1 text-[9.5px] font-medium uppercase tracking-[0.22em] text-white/65">Pharmacy Intelligence</p>
      <div className="mt-6 flex items-center gap-2 text-[10.5px] text-white/75">
        <Loader2 size={15} className="animate-spin" /> Menyiapkan data...
      </div>
    </div>
  )
}

function NotFound() {
  return (
    <AppShell active="more">
      <PageHeader title="Halaman tidak ditemukan" subtitle="Periksa kembali alamat tujuan" />
      <main className="px-4 pt-6">
        <EmptyState
          icon={<MapPinOff size={22} />}
          title="Halaman tidak tersedia"
          description="Menu yang Anda tuju mungkin sudah dipindahkan. Kembali ke beranda untuk melanjutkan."
          action={<Button onClick={() => navigate('/')}>Kembali ke Beranda</Button>}
        />
      </main>
    </AppShell>
  )
}

function Router() {
  const { user, ready } = useAuth()
  const route = useRoute()
  const path = route.split('?')[0]

  useEffect(() => {
    if (!ready) return
    if (!user && path !== '/login') navigate('/login')
    if (user && path === '/login') navigate('/')
  }, [ready, user, path])

  useEffect(() => {
    if ('serviceWorker' in navigator && import.meta.env.PROD) {
      navigator.serviceWorker.register('/sw.js').catch(() => undefined)
    }
  }, [])

  if (!ready) return <Splash />
  if (!user) return <Login />
  if (path === '/login') return <Splash />

  switch (path) {
    case '/':
      return <Dashboard />
    case '/prediction':
      return <Prediction />
    case '/stock':
      return <Stock />
    case '/more':
      return <More />
    case '/sales':
      return <Sales />
    case '/weather':
      return <Weather />
    case '/procurement':
      return <Procurement />
    case '/reports':
      return <Reports />
    case '/activity':
      return <Activity />
    case '/settings':
      return <Settings />
    default:
      return <NotFound />
  }
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Router />
      </ToastProvider>
    </AuthProvider>
  )
}
