import { useCallback, useEffect, useState, type ReactNode } from 'react'
import {
  Bell,
  CalendarDays,
  CheckCheck,
  ChevronLeft,
  Home,
  LayoutGrid,
  Package,
  TrendingUp,
} from 'lucide-react'
import { navigate } from '../router'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import type { NotificationItem } from '../types'
import { cn, formatDateTime, formatNumber, greeting } from '../utils'
import { HeaderOrnaments, LogoMark } from './Illustration'
import { Badge, Button, EmptyState, IconButton, Modal } from './ui'

export type NavKey = 'home' | 'prediction' | 'stock' | 'more'

const navItems: { key: NavKey; label: string; icon: typeof Home; path: string }[] = [
  { key: 'home', label: 'Beranda', icon: Home, path: '/' },
  { key: 'prediction', label: 'Prediksi', icon: TrendingUp, path: '/prediction' },
  { key: 'stock', label: 'Stok', icon: Package, path: '/stock' },
  { key: 'more', label: 'Lainnya', icon: LayoutGrid, path: '/more' },
]

export function BottomNav({ active }: { active?: NavKey }) {
  return (
    <nav className="bottom-nav fixed inset-x-0 bottom-0 z-40 mx-auto w-full max-w-[480px] border-t border-line/80 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-xl">
      <div className="grid grid-cols-4 px-2 pb-1.5 pt-2">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = active === item.key
          return (
            <button
              key={item.key}
              onClick={() => navigate(item.path)}
              aria-current={isActive ? 'page' : undefined}
              className="group flex flex-col items-center gap-1 rounded-xl py-0.5 text-[9.5px] font-semibold transition"
            >
              <span
                className={cn(
                  'flex h-8 w-11 items-center justify-center rounded-[11px] transition',
                  isActive ? 'bg-primary text-white shadow-[0_5px_14px_rgba(8,127,107,.28)]' : 'text-[#8A9AA5] group-hover:bg-slate-100',
                )}
              >
                <Icon size={17} strokeWidth={isActive ? 2.4 : 2} />
              </span>
              <span className={isActive ? 'text-primary' : 'text-[#8A9AA5]'}>{item.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}

export function AppShell({ active, children }: { active?: NavKey; children: ReactNode }) {
  return (
    <div className="phone-shell flex min-h-dvh flex-col">
      <div className="flex-1 pb-[calc(74px+env(safe-area-inset-bottom))]">{children}</div>
      <BottomNav active={active} />
    </div>
  )
}

/* ------------------------------- Home header ------------------------------ */
export function HomeHeader() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState<NotificationItem[]>([])
  const [unread, setUnread] = useState(0)
  const [marking, setMarking] = useState(false)

  const load = useCallback(async () => {
    try {
      const result = await api.get<{ unread: number; items: NotificationItem[] }>('/notifications?limit=25')
      setItems(result.items)
      setUnread(result.unread)
    } catch {
      // notifikasi bukan fitur kritis; biarkan senyap bila gagal
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const markAll = async () => {
    setMarking(true)
    try {
      await api.post('/notifications/read-all')
      setItems((current) => current.map((item) => ({ ...item, is_read: true })))
      setUnread(0)
    } finally {
      setMarking(false)
    }
  }

  const today = new Intl.DateTimeFormat('id-ID', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date())

  return (
    <>
      <header className="relative overflow-hidden rounded-b-[26px] bg-gradient-to-br from-[#0B5F52] via-[#087F6B] to-[#20B58A] px-4 pb-12 pt-4 text-white">
        <HeaderOrnaments />
        <div className="relative flex items-center gap-2.5">
          <span className="flex h-10 w-10 items-center justify-center rounded-[13px] bg-white/95 shadow-sm">
            <LogoMark size={30} />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[13.5px] font-bold leading-tight">Apotek Pahala</p>
            <p className="mt-0.5 text-[9.5px] font-medium uppercase tracking-[0.13em] text-white/70">
              Pharmacy Intelligence
            </p>
          </div>
          <button
            onClick={() => setOpen(true)}
            aria-label="Notifikasi"
            className="relative flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white backdrop-blur transition active:scale-95"
          >
            <Bell size={17} />
            {unread > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-[#F2A93B] px-1 text-[9px] font-bold text-[#3B2A08] ring-2 ring-[#0C6B5C]">
                {unread > 9 ? '9+' : unread}
              </span>
            )}
          </button>
        </div>

        <div className="relative mt-5">
          <p className="text-[11px] font-medium text-white/75">{greeting()},</p>
          <h1 className="mt-0.5 truncate text-[20px] font-extrabold leading-tight tracking-[-0.01em]">
            {user?.full_name || 'Pengguna'}
          </h1>
          <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/12 px-2.5 py-1 text-[10px] font-medium text-white/90 backdrop-blur">
              <CalendarDays size={11} />
              {today}
            </span>
            <Badge className="border border-white/25 bg-white/15 !text-[9px] !text-white" tone="neutral">
              Data Aktual
            </Badge>
          </div>
        </div>
      </header>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Notifikasi"
        subtitle={unread ? `${formatNumber(unread)} belum dibaca` : 'Semua sudah dibaca'}
        footer={
          <Button variant="outline" className="w-full" onClick={markAll} loading={marking} disabled={!unread}>
            <CheckCheck size={16} /> Tandai semua dibaca
          </Button>
        }
      >
        {items.length === 0 ? (
          <EmptyState icon={<Bell size={22} />} title="Belum ada notifikasi" description="Pemberitahuan stok, prediksi, dan pengadaan akan muncul di sini." compact />
        ) : (
          <div className="space-y-2">
            {items.map((item) => (
              <div
                key={item.id}
                className={cn(
                  'rounded-xl border px-3 py-2.5',
                  item.is_read ? 'border-line bg-white' : 'border-[#CFEDE2] bg-[#F4FBF8]',
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-[12px] font-semibold text-ink">{item.title}</p>
                  {!item.is_read && <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />}
                </div>
                <p className="mt-0.5 text-[11px] leading-relaxed text-muted">{item.message}</p>
                <p className="mt-1 text-[9.5px] text-[#9AA9B2]">{formatDateTime(item.created_at)}</p>
              </div>
            ))}
          </div>
        )}
      </Modal>
    </>
  )
}

/* ------------------------------- Page header ------------------------------ */
export function PageHeader({
  title,
  subtitle,
  action,
  back = true,
  sticky = true,
}: {
  title: string
  subtitle?: string
  action?: ReactNode
  back?: boolean
  sticky?: boolean
}) {
  return (
    <header
      className={cn(
        'z-30 flex items-center gap-2.5 border-b border-line/70 bg-canvas/90 px-4 pb-3 pt-3 backdrop-blur-xl',
        sticky && 'sticky top-0',
      )}
    >
      {back ? (
        <IconButton
          label="Kembali"
          onClick={() => (window.history.length > 1 ? window.history.back() : navigate('/'))}
          className="border border-line bg-white text-ink shadow-card"
        >
          <ChevronLeft size={18} />
        </IconButton>
      ) : (
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary">
          <LogoMark size={24} />
        </span>
      )}
      <div className="min-w-0 flex-1">
        <h1 className="truncate text-[15px] font-bold leading-tight text-ink">{title}</h1>
        {subtitle && <p className="mt-0.5 truncate text-[10.5px] text-muted">{subtitle}</p>}
      </div>
      {action}
    </header>
  )
}
