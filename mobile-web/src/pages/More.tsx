import { useEffect, useState } from 'react'
import {
  BadgeInfo,
  ChevronRight,
  CloudRain,
  ClipboardList,
  FileBarChart,
  History,
  LogOut,
  MonitorSmartphone,
  Moon,
  ReceiptText,
  Settings2,
  ShieldCheck,
  Sun,
} from 'lucide-react'
import { api } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { navigate } from '../router'
import { AppShell, PageHeader } from '../components/Layout'
import { Badge, Button, Card, ConfirmDialog, SectionTitle } from '../components/ui'
import { cn, initials } from '../utils'
import type { User } from '../types'

const THEMES = [
  { value: 'light', label: 'Terang', icon: Sun },
  { value: 'dark', label: 'Gelap', icon: Moon },
  { value: 'auto', label: 'Otomatis', icon: MonitorSmartphone },
]

const groups = [
  {
    title: 'Operasional',
    items: [
      { label: 'Data Penjualan', description: 'Riwayat permintaan dan penjualan manual', icon: ReceiptText, path: '/sales', className: 'bg-[#E7F6F0] text-secondary' },
      { label: 'Data Cuaca', description: 'Suhu, curah hujan, dan kelembapan', icon: CloudRain, path: '/weather', className: 'bg-[#EAF3FC] text-[#2F73B9]' },
      { label: 'Rekomendasi Pengadaan', description: 'Usulan pembelian dari prakiraan', icon: ClipboardList, path: '/procurement', className: 'bg-[#FEF4E2] text-[#B47A16]' },
    ],
  },
  {
    title: 'Analitik & Laporan',
    items: [
      { label: 'Laporan', description: 'PDF, Excel, dan CSV siap cetak', icon: FileBarChart, path: '/reports', className: 'bg-[#E7F6F0] text-secondary' },
      { label: 'Aktivitas & Notifikasi', description: 'Jejak audit dan pemberitahuan', icon: History, path: '/activity', className: 'bg-[#EEF3F5] text-[#5B7078]' },
    ],
  },
  {
    title: 'Sistem',
    items: [
      { label: 'Pengaturan', description: 'Profil, model, dan database', icon: Settings2, path: '/settings', className: 'bg-[#EEF3F5] text-[#5B7078]' },
    ],
  },
]

export default function More() {
  const { user, updateUser, logout } = useAuth()
  const [theme, setTheme] = useState(user?.theme || 'light')
  const [savingTheme, setSavingTheme] = useState(false)
  const [logoutOpen, setLogoutOpen] = useState(false)
  const [aboutOpen, setAboutOpen] = useState(false)
  const [appInfo, setAppInfo] = useState<{ version: string; developer: string; technology: string[] } | null>(null)

  useEffect(() => {
    api
      .get<{ version: string; developer: string; technology: string[] }>('/app-info')
      .then(setAppInfo)
      .catch(() => undefined)
  }, [])

  const changeTheme = async (value: string) => {
    setTheme(value)
    setSavingTheme(true)
    try {
      await api.put('/settings/display', { theme: value })
      updateUser({ theme: value } as Partial<User>)
    } catch {
      setTheme(user?.theme || 'light')
    } finally {
      setSavingTheme(false)
    }
  }

  return (
    <AppShell active="more">
      <PageHeader title="Lainnya" subtitle="Menu, profil, dan pengaturan" back={false} />
      <main className="px-4 pt-3">
        <Card className="overflow-hidden !p-0">
          <div className="relative overflow-hidden bg-gradient-to-br from-[#0B5F52] via-[#087F6B] to-[#20B58A] px-4 py-4 text-white">
            <div aria-hidden className="absolute -right-8 -top-10 h-32 w-32 rounded-full border border-white/10" />
            <div className="relative flex items-center gap-3">
              <span className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-white/30 bg-white/15 text-[15px] font-extrabold backdrop-blur">
                {initials(user?.full_name || 'Pengguna')}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[14px] font-bold">{user?.full_name}</p>
                <p className="truncate text-[10px] text-white/70">@{user?.username} · {user?.email || 'tanpa email'}</p>
                <div className="mt-1 flex gap-1.5">
                  <Badge className="border border-white/25 bg-white/15 !text-white" tone="neutral">
                    <ShieldCheck size={9} /> {user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1).toLowerCase() : ''}
                  </Badge>
                  <Badge className="border border-white/25 bg-white/15 !text-white" tone="neutral">AKTUAL</Badge>
                </div>
              </div>
            </div>
          </div>
          <div className="px-3.5 py-3">
            <div className="mb-2 flex items-center justify-between">
              <p className="text-[11px] font-bold text-ink">Tampilan</p>
              {savingTheme && <span className="text-[8.5px] text-muted">Menyimpan...</span>}
            </div>
            <div className="grid grid-cols-3 gap-1.5">
              {THEMES.map((item) => {
                const Icon = item.icon
                return (
                  <button
                    key={item.value}
                    onClick={() => changeTheme(item.value)}
                    className={cn(
                      'flex flex-col items-center gap-1 rounded-[10px] border px-2 py-2 text-[9.5px] font-semibold transition',
                      theme === item.value
                        ? 'border-primary bg-[#F0FAF6] text-primary'
                        : 'border-line bg-white text-muted',
                    )}
                  >
                    <Icon size={14} />
                    {item.label}
                  </button>
                )
              })}
            </div>
          </div>
        </Card>

        {groups.map((group) => (
          <div key={group.title} className="mt-3">
            <p className="mb-1.5 px-1 text-[9px] font-bold uppercase tracking-[0.1em] text-[#93A3AC]">{group.title}</p>
            <Card className="!px-0 !py-1">
              {group.items.map((item, index) => {
                const Icon = item.icon
                return (
                  <button
                    key={item.path}
                    onClick={() => navigate(item.path)}
                    className={cn(
                      'flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left transition hover:bg-[#F8FBFC]',
                      index !== group.items.length - 1 && 'border-b border-line',
                    )}
                  >
                    <span className={cn('flex h-8 w-8 shrink-0 items-center justify-center rounded-[9px]', item.className)}>
                      <Icon size={15} />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-[11.5px] font-semibold text-ink">{item.label}</span>
                      <span className="block truncate text-[9px] text-muted">{item.description}</span>
                    </span>
                    <ChevronRight size={14} className="shrink-0 text-[#C3CDD3]" />
                  </button>
                )
              })}
            </Card>
          </div>
        ))}

        <Card className="mt-3">
          <SectionTitle title="Tentang Aplikasi" icon={<BadgeInfo size={15} />} />
          <div className="space-y-1 text-[10px] text-muted">
            <p className="font-semibold text-ink">Apotek Pahala — Pharmacy Intelligence</p>
            <p>Solusi analitik untuk persediaan obat yang lebih tepat.</p>
            <p>Versi {appInfo?.version || '1.0.0'} · {appInfo?.developer || 'Capstone Project'}</p>
          </div>
          <button onClick={() => setAboutOpen(true)} className="mt-2 text-[10px] font-semibold text-primary">
            Lihat detail teknologi
          </button>
        </Card>

        <Button variant="outline" className="mt-3 w-full !border-[#F6DADA] !text-danger" onClick={() => setLogoutOpen(true)}>
          <LogOut size={15} /> Keluar dari akun
        </Button>

        <p className="mt-3 pb-2 text-center text-[9px] leading-relaxed text-[#9AA9B2]">
          Data aktual Apotek Pahala: stok opname dan pembelian 2022–2026.<br />
          Permintaan merupakan estimasi, bukan transaksi kasir.
        </p>
      </main>

      <ConfirmDialog
        open={logoutOpen}
        onClose={() => setLogoutOpen(false)}
        onConfirm={logout}
        title="Keluar dari aplikasi?"
        message="Anda perlu memasukkan nama pengguna dan password kembali untuk mengakses data."
        confirmLabel="Ya, keluar"
        danger
      />

      {aboutOpen && (
        <div className="fixed inset-0 z-[70] flex items-center justify-center px-5">
          <div className="absolute inset-0 bg-[#08231E]/45 backdrop-blur-[2px]" onClick={() => setAboutOpen(false)} />
          <div className="relative w-full max-w-[360px] rounded-[20px] bg-white p-5 shadow-float">
            <p className="text-[14px] font-bold text-ink">Teknologi</p>
            <p className="mt-1 text-[10.5px] leading-relaxed text-muted">
              Backend FastAPI dan SQLite menjadi sumber data tunggal bagi aplikasi desktop PySide6 dan mobile web ini.
            </p>
            <ul className="mt-3 space-y-1.5">
              {(appInfo?.technology || [
                'Python 3.14', 'FastAPI', 'SQLite', 'Scikit-learn (Random Forest, Decision Tree, Linear Regression)',
                'React + TypeScript', 'Recharts', 'PySide6', 'ReportLab', 'OpenPyXL',
              ]).map((item) => (
                <li key={item} className="flex items-center gap-1.5 text-[10.5px] text-ink">
                  <span className="h-1 w-1 rounded-full bg-primary" /> {item}
                </li>
              ))}
            </ul>
            <Button variant="outline" className="mt-4 w-full" onClick={() => setAboutOpen(false)}>Tutup</Button>
          </div>
        </div>
      )}
    </AppShell>
  )
}
