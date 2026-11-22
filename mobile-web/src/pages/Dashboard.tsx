import { useCallback, useEffect, useState } from 'react'
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Boxes,
  ClipboardList,
  Database,
  Package,
  Pill,
  RefreshCw,
  ShoppingBag,
  Sparkles,
  Target,
  TrendingUp,
  TriangleAlert,
  UserRound,
  Wallet,
} from 'lucide-react'
import { api } from '../services/api'
import type { DashboardData } from '../types'
import { navigate } from '../router'
import { HomeHeader, AppShell } from '../components/Layout'
import { DonutChart, Sparkline, TrendChart } from '../components/charts'
import {
  Badge,
  Button,
  Card,
  ErrorState,
  IconButton,
  SectionTitle,
  Skeleton,
} from '../components/ui'
import {
  cn,
  formatCompactRupiah,
  formatDate,
  formatNumber,
  formatPercent,
  relativeTime,
} from '../utils'

function KpiCard({
  icon,
  label,
  value,
  delta,
  hint,
  tone,
}: {
  icon: React.ReactNode
  label: string
  value: string
  delta?: number | null
  hint?: string
  tone: 'primary' | 'info' | 'warning' | 'accent'
}) {
  const tones = {
    primary: 'bg-primary/10 text-primary',
    info: 'bg-[#EAF3FC] text-info',
    warning: 'bg-[#FEF4E2] text-[#B47A16]',
    accent: 'bg-[#E7F6F0] text-[#0E8A5F]',
  }
  const positive = (delta ?? 0) >= 0
  return (
    <div className="rounded-[15px] border border-line bg-white p-3 shadow-card">
      <div className="flex items-center justify-between">
        <span className={cn('flex h-7 w-7 items-center justify-center rounded-[9px]', tones[tone])}>{icon}</span>
        {delta !== undefined && delta !== null && (
          <span
            className={cn(
              'inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[9px] font-bold',
              positive ? 'bg-[#E8F7F0] text-[#0E8A5F]' : 'bg-[#FDECEC] text-[#D14343]',
            )}
          >
            {positive ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
            {formatNumber(Math.abs(delta), 1)}%
          </span>
        )}
      </div>
      <p className="mt-2 text-[9px] font-semibold uppercase tracking-[0.08em] text-muted">{label}</p>
      <p className="mt-0.5 truncate text-[17px] font-extrabold leading-tight tracking-[-0.02em] text-ink">{value}</p>
      {hint && <p className="mt-0.5 truncate text-[9px] text-[#93A3AC]">{hint}</p>}
    </div>
  )
}

const activityStyles: Record<string, { icon: typeof Package; className: string }> = {
  sale: { icon: ShoppingBag, className: 'bg-[#E8F7F0] text-[#0E8A5F]' },
  stock: { icon: Boxes, className: 'bg-[#FEF4E2] text-[#B47A16]' },
  prediction: { icon: TrendingUp, className: 'bg-[#EAF3FC] text-[#2F73B9]' },
  procurement: { icon: ClipboardList, className: 'bg-[#E7F6F0] text-secondary' },
  login: { icon: UserRound, className: 'bg-slate-100 text-muted' },
  import: { icon: RefreshCw, className: 'bg-[#EAF3FC] text-[#2F73B9]' },
  backup: { icon: Database, className: 'bg-slate-100 text-muted' },
  medicine: { icon: Pill, className: 'bg-[#E7F6F0] text-secondary' },
}

function DashboardSkeleton() {
  return (
    <div className="px-4">
      <div className="-mt-8 grid grid-cols-2 gap-2.5">
        {[0, 1, 2, 3].map((index) => (
          <Skeleton key={index} className="h-[92px] rounded-[15px]" />
        ))}
      </div>
      <Skeleton className="mt-3 h-[240px] rounded-card" />
      <Skeleton className="mt-3 h-[132px] rounded-card" />
      <Skeleton className="mt-3 h-[210px] rounded-card" />
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [range, setRange] = useState<4 | 8 | 12>(12)

  const load = useCallback(async (silent = false) => {
    if (silent) setRefreshing(true)
    else setLoading(true)
    setError('')
    try {
      const result = await api.get<DashboardData>('/dashboard/overview')
      setData(result)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Gagal memuat ringkasan.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const trendSlice = data
    ? {
        labels: data.trend.labels.slice(-range),
        actual: data.trend.actual.slice(-range),
        predicted: data.trend.predicted.slice(-range),
      }
    : null

  const stockData = data
    ? [
        { name: 'Aman', value: data.stock.aman, color: '#16A36A' },
        { name: 'Perlu perhatian', value: data.stock.perlu_perhatian, color: '#F2A93B' },
        { name: 'Kritis', value: data.stock.kritis, color: '#E55353' },
      ]
    : []

  const maxForecast = Math.max(...(data?.prediction_summary.weeks.map((week) => week.value) || [1]))

  return (
    <AppShell active="home">
      <HomeHeader />
      {loading && !data ? (
        <DashboardSkeleton />
      ) : error && !data ? (
        <div className="px-4 pt-6">
          <ErrorState message={error} onRetry={() => load()} />
        </div>
      ) : data ? (
        <main className="px-4">
          {/* KPI */}
          <section className="-mt-8 relative z-10 grid grid-cols-2 gap-2.5">
            <KpiCard
              icon={<Wallet size={15} />}
              label="Estimasi Nilai"
              value={formatCompactRupiah(data.kpis.revenue)}
              delta={data.kpis.revenue_delta}
              hint={data.period.label}
              tone="primary"
            />
            <KpiCard
              icon={<ShoppingBag size={15} />}
              label="Permintaan"
              value={`${formatNumber(data.kpis.demand)} unit`}
              delta={data.kpis.demand_delta}
              hint="Dibanding pekan sebelumnya"
              tone="info"
            />
            <KpiCard
              icon={<Pill size={15} />}
              label="Obat Prioritas"
              value={`${data.kpis.priority_count} obat`}
              hint="Dipantau model prediksi"
              tone="warning"
            />
            <KpiCard
              icon={<Target size={15} />}
              label="Akurasi Prediksi"
              value={data.kpis.accuracy === null ? '—' : formatPercent(data.kpis.accuracy)}
              hint={`WAPE ${formatPercent(data.kpis.wape)} · ${data.kpis.wape_medicine_count} obat prioritas`}
              tone="accent"
            />
          </section>

          {/* Tren */}
          <Card className="mt-3">
            <SectionTitle
              title="Tren Permintaan & Prediksi"
              subtitle={data.period.label}
              action={
                <div className="flex rounded-full bg-[#EEF3F5] p-0.5">
                  {([4, 8, 12] as const).map((value) => (
                    <button
                      key={value}
                      onClick={() => setRange(value)}
                      className={cn(
                        'rounded-full px-2 py-1 text-[9.5px] font-semibold transition',
                        range === value ? 'bg-primary text-white shadow-sm' : 'text-muted',
                      )}
                    >
                      {value === 4 ? '1 bln' : value === 8 ? '2 bln' : '3 bln'}
                    </button>
                  ))}
                </div>
              }
            />
            <div className="mb-1 flex items-center gap-3 text-[9.5px] font-medium text-muted">
              <span className="inline-flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-primary" /> Aktual
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-accent" /> Prediksi
              </span>
              <button
                onClick={() => load(true)}
                className="ml-auto inline-flex items-center gap-1 text-[9.5px] font-semibold text-primary"
                aria-label="Muat ulang data"
              >
                <RefreshCw size={11} className={refreshing ? 'animate-spin' : ''} /> Segarkan
              </button>
            </div>
            {trendSlice && (
              <TrendChart labels={trendSlice.labels} actual={trendSlice.actual} predicted={trendSlice.predicted} />
            )}
          </Card>

          {/* Prediksi 4 pekan */}
          <Card className="mt-3 border-[#CFEDE2] bg-[#F4FBF8]">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-[9px] bg-white text-primary shadow-sm">
                  <Sparkles size={14} />
                </span>
                <div>
                  <p className="text-[12.5px] font-bold leading-tight text-ink">Prakiraan {data.prediction_summary.horizon} Pekan</p>
                  <p className="text-[9.5px] text-muted">Total kebutuhan seluruh obat</p>
                </div>
              </div>
              <button onClick={() => navigate('/prediction')} className="flex items-center gap-0.5 text-[10px] font-semibold text-primary">
                Detail <ArrowRight size={11} />
              </button>
            </div>

            <div className="mt-3 flex items-end justify-between gap-3">
              <div>
                <p className="text-[22px] font-extrabold leading-none tracking-[-0.02em] text-secondary">
                  {formatNumber(data.prediction_summary.total)}
                </p>
                <p className="mt-0.5 text-[9.5px] text-muted">unit</p>
              </div>
              <div className="flex flex-1 items-end justify-end gap-2">
                {data.prediction_summary.weeks.map((week) => (
                  <div key={week.label} className="flex w-9 flex-col items-center gap-1">
                    <span className="text-[8.5px] font-semibold text-secondary">{formatNumber(week.value)}</span>
                    <div className="flex h-10 w-full items-end rounded-[5px] bg-white/70">
                      <div
                        className="w-full rounded-[5px] bg-gradient-to-t from-primary to-accent"
                        style={{ height: `${Math.max(18, (week.value / maxForecast) * 100)}%` }}
                      />
                    </div>
                    <span className="text-[8px] text-muted">{week.label.replace('Minggu ', 'M')}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-3 flex items-start gap-1.5 rounded-[9px] border border-[#D8EFE6] bg-white/80 px-2.5 py-2">
              <TrendingUp size={12} className="mt-0.5 shrink-0 text-success" />
              <p className="text-[10px] leading-relaxed text-[#3E6B62]">{data.prediction_summary.insight}</p>
            </div>
          </Card>

          {/* Top obat */}
          <Card className="mt-3">
            <SectionTitle
              title="Obat Terlaris"
              subtitle="5 obat dengan permintaan tertinggi"
              action={
                <button onClick={() => navigate('/stock')} className="text-[10px] font-semibold text-primary">
                  Semua
                </button>
              }
            />
            <div className="divide-y divide-line">
              {data.top_medicines.slice(0, 5).map((medicine, index) => (
                <button
                  key={medicine.medicine_id}
                  onClick={() => navigate(`/prediction?medicine=${medicine.medicine_id}`)}
                  className="flex w-full items-center gap-2.5 py-2.5 text-left first:pt-0 last:pb-0"
                >
                  <span
                    className={cn(
                      'flex h-6 w-6 shrink-0 items-center justify-center rounded-[8px] text-[10px] font-bold',
                      index === 0
                        ? 'bg-[#FEF4E2] text-[#B47A16]'
                        : index === 1
                          ? 'bg-[#EEF3F5] text-[#5B7078]'
                          : index === 2
                            ? 'bg-[#FBEAE0] text-[#B4642F]'
                            : 'bg-[#F5F8FA] text-[#93A3AC]',
                    )}
                  >
                    {index + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[11.5px] font-semibold text-ink">{medicine.name}</p>
                    <p className="mt-0.5 text-[9px] text-muted">
                      {formatNumber(medicine.sold)} permintaan · prediksi {formatNumber(medicine.predicted)} {medicine.unit.toLowerCase()}
                    </p>
                  </div>
                  <Sparkline values={medicine.sparkline} width={58} height={24} />
                </button>
              ))}
            </div>
          </Card>

          {/* Stok */}
          <Card className="mt-3">
            <SectionTitle
              title="Status Stok"
              subtitle={`${data.stock.total} obat terdaftar`}
              action={
                <button onClick={() => navigate('/stock')} className="text-[10px] font-semibold text-primary">
                  Kelola
                </button>
              }
            />
            <div className="flex items-center gap-4">
              <DonutChart data={stockData} centerValue={String(data.stock.total)} centerLabel="obat" />
              <div className="min-w-0 flex-1 space-y-2">
                {stockData.map((item) => (
                  <div key={item.name} className="flex items-center gap-2">
                    <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: item.color }} />
                    <span className="min-w-0 flex-1 truncate text-[10.5px] text-muted">{item.name}</span>
                    <span className="text-[10.5px] font-bold text-ink">{item.value}</span>
                    <span className="w-9 text-right text-[9px] text-[#93A3AC]">
                      {formatNumber((item.value / Math.max(data.stock.total, 1)) * 100)}%
                    </span>
                  </div>
                ))}
                {data.stock.kritis > 0 && (
                  <div className="flex items-start gap-1.5 rounded-[8px] bg-[#FDF3F3] px-2 py-1.5">
                    <TriangleAlert size={11} className="mt-0.5 shrink-0 text-danger" />
                    <p className="text-[9.5px] leading-snug text-[#A64848]">
                      {data.stock.kritis} obat berada pada level kritis dan perlu segera dipesan.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Aktivitas */}
          <Card className="mt-3">
            <SectionTitle
              title="Aktivitas Terbaru"
              action={
                <button onClick={() => navigate('/activity')} className="text-[10px] font-semibold text-primary">
                  Lihat semua
                </button>
              }
            />
            <div className="space-y-2.5">
              {data.activities.slice(0, 4).map((activity) => {
                const style = activityStyles[activity.type] || { icon: Activity, className: 'bg-slate-100 text-muted' }
                const Icon = style.icon
                return (
                  <div key={activity.id} className="flex items-start gap-2.5">
                    <span className={cn('flex h-7 w-7 shrink-0 items-center justify-center rounded-[9px]', style.className)}>
                      <Icon size={13} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-[10.5px] leading-snug text-ink">{activity.description}</p>
                      <p className="mt-0.5 text-[9px] text-[#93A3AC]">
                        {activity.user} · {relativeTime(activity.created_at)}
                      </p>
                    </div>
                  </div>
                )
              })}
              {data.activities.length === 0 && (
                <p className="py-2 text-center text-[10.5px] text-muted">Belum ada aktivitas tercatat.</p>
              )}
            </div>
          </Card>

          <div className="mt-4 flex flex-col items-center gap-1 pb-2 text-center">
            <Badge tone="success" dot>
              Data aktual Apotek Pahala
            </Badge>
            <p className="text-[9px] text-[#9AA9B2]">
              Periode {formatDate(data.period.start)} – {formatDate(data.period.end)} · {data.period.weeks} pekan
            </p>
          </div>
        </main>
      ) : null}
    </AppShell>
  )
}
