import { useCallback, useEffect, useState } from 'react'
import {
  Bell,
  BellRing,
  Boxes,
  CheckCheck,
  ClipboardList,
  Database,
  History,
  Package,
  Pill,
  RefreshCw,
  ShoppingBag,
  TrendingUp,
  UserRound,
} from 'lucide-react'
import { api } from '../services/api'
import type { NotificationItem } from '../types'
import { AppShell, PageHeader } from '../components/Layout'
import { Badge, Button, Card, EmptyState, ErrorState, Skeleton } from '../components/ui'
import { cn, formatDateTime, formatNumber, relativeTime } from '../utils'

interface ActivityRow {
  id: number
  type: string
  description: string
  object_type: string
  object_id: number | null
  user: string
  created_at: string
}

const styles: Record<string, { icon: typeof Package; className: string; label: string }> = {
  sale: { icon: ShoppingBag, className: 'bg-[#E8F7F0] text-[#0E8A5F]', label: 'Penjualan' },
  stock: { icon: Boxes, className: 'bg-[#FEF4E2] text-[#B47A16]', label: 'Stok' },
  prediction: { icon: TrendingUp, className: 'bg-[#EAF3FC] text-[#2F73B9]', label: 'Prediksi' },
  training: { icon: TrendingUp, className: 'bg-[#EAF3FC] text-[#2F73B9]', label: 'Training' },
  procurement: { icon: ClipboardList, className: 'bg-[#E7F6F0] text-secondary', label: 'Pengadaan' },
  login: { icon: UserRound, className: 'bg-[#EEF3F5] text-[#5B7078]', label: 'Akun' },
  import: { icon: RefreshCw, className: 'bg-[#EAF3FC] text-[#2F73B9]', label: 'Import' },
  backup: { icon: Database, className: 'bg-[#EEF3F5] text-[#5B7078]', label: 'Database' },
  medicine: { icon: Pill, className: 'bg-[#E7F6F0] text-secondary', label: 'Obat' },
  settings: { icon: RefreshCw, className: 'bg-[#EEF3F5] text-[#5B7078]', label: 'Pengaturan' },
}

export default function Activity() {
  const [tab, setTab] = useState<'activity' | 'notification'>('activity')
  const [activities, setActivities] = useState<ActivityRow[]>([])
  const [notifications, setNotifications] = useState<NotificationItem[]>([])
  const [unread, setUnread] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [marking, setMarking] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [log, notif] = await Promise.all([
        api.get<{ items: ActivityRow[]; total: number }>('/activities?page_size=60'),
        api.get<{ unread: number; items: NotificationItem[] }>('/notifications?limit=40'),
      ])
      setActivities(log.items)
      setNotifications(notif.items)
      setUnread(notif.unread)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Gagal memuat aktivitas.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const markAll = async () => {
    setMarking(true)
    try {
      await api.post('/notifications/read-all')
      setNotifications((current) => current.map((item) => ({ ...item, is_read: true })))
      setUnread(0)
    } finally {
      setMarking(false)
    }
  }

  return (
    <AppShell active="more">
      <PageHeader
        title="Aktivitas & Notifikasi"
        subtitle="Jejak audit penggunaan aplikasi"
        action={
          <button onClick={load} className="rounded-full border border-line bg-white p-2 text-muted shadow-card" aria-label="Muat ulang">
            <RefreshCw size={14} />
          </button>
        }
      />
      <main className="px-4 pt-3">
        <div className="grid grid-cols-2 gap-1 rounded-full bg-[#EEF3F5] p-1">
          {[
            { key: 'activity', label: 'Aktivitas', icon: History },
            { key: 'notification', label: 'Notifikasi', icon: Bell },
          ].map((item) => {
            const Icon = item.icon
            const active = tab === item.key
            return (
              <button
                key={item.key}
                onClick={() => setTab(item.key as 'activity' | 'notification')}
                className={cn(
                  'flex items-center justify-center gap-1.5 rounded-full py-2 text-[10.5px] font-semibold transition',
                  active ? 'bg-white text-primary shadow-sm' : 'text-muted',
                )}
              >
                <Icon size={13} /> {item.label}
                {item.key === 'notification' && unread > 0 && (
                  <span className="rounded-full bg-danger px-1.5 text-[8px] font-bold text-white">{unread}</span>
                )}
              </button>
            )
          })}
        </div>

        {loading ? (
          <div className="mt-3 space-y-2">
            {[0, 1, 2, 3, 4].map((index) => <Skeleton key={index} className="h-[54px] rounded-[12px]" />)}
          </div>
        ) : error ? (
          <div className="mt-3"><ErrorState message={error} onRetry={load} /></div>
        ) : tab === 'activity' ? (
          <div className="mt-3 space-y-2">
            {activities.length === 0 ? (
              <Card><EmptyState icon={<History size={20} />} title="Belum ada aktivitas" description="Setiap perubahan data akan tercatat di sini." compact /></Card>
            ) : (
              activities.map((row) => {
                const style = styles[row.type] || styles.settings
                const Icon = style.icon
                return (
                  <div key={row.id} className="flex items-start gap-2.5 rounded-[12px] border border-line bg-white px-3 py-2.5 shadow-card">
                    <span className={cn('flex h-8 w-8 shrink-0 items-center justify-center rounded-[9px]', style.className)}>
                      <Icon size={14} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5">
                        <Badge tone="neutral" className="!text-[8px]">{style.label}</Badge>
                        <span className="text-[8.5px] text-[#9AA9B2]">{relativeTime(row.created_at)}</span>
                      </div>
                      <p className="mt-1 text-[10.5px] leading-snug text-ink">{row.description}</p>
                      <p className="mt-0.5 text-[8.5px] text-muted">{row.user}</p>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        ) : (
          <div className="mt-3">
            {unread > 0 && (
              <Button variant="outline" size="sm" className="mb-2 w-full" onClick={markAll} loading={marking}>
                <CheckCheck size={14} /> Tandai semua dibaca
              </Button>
            )}
            <div className="space-y-2">
              {notifications.length === 0 ? (
                <Card><EmptyState icon={<BellRing size={20} />} title="Belum ada notifikasi" description="Pemberitahuan stok kritis, prediksi, dan pengadaan muncul di sini." compact /></Card>
              ) : (
                notifications.map((item) => (
                  <div
                    key={item.id}
                    className={cn(
                      'rounded-[12px] border px-3 py-2.5',
                      item.is_read ? 'border-line bg-white' : 'border-[#CFEDE2] bg-[#F4FBF8]',
                    )}
                  >
                    <div className="flex items-center gap-1.5">
                      <span
                        className={cn(
                          'h-1.5 w-1.5 rounded-full',
                          item.level === 'danger' ? 'bg-danger' : item.level === 'warning' ? 'bg-warning' : item.level === 'success' ? 'bg-success' : 'bg-info',
                        )}
                      />
                      <p className="flex-1 text-[11px] font-semibold text-ink">{item.title}</p>
                      <span className="text-[8.5px] text-[#9AA9B2]">{formatDateTime(item.created_at)}</span>
                    </div>
                    <p className="mt-1 text-[10px] leading-relaxed text-muted">{item.message}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {!loading && !error && (
          <p className="mt-3 pb-2 text-center text-[9px] text-[#9AA9B2]">
            {tab === 'activity'
              ? `${formatNumber(activities.length)} aktivitas terakhir`
              : `${formatNumber(notifications.length)} notifikasi · ${unread} belum dibaca`}
          </p>
        )}
      </main>
    </AppShell>
  )
}
