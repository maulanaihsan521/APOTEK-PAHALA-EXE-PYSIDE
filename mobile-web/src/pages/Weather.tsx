import { useEffect, useState } from 'react'
import { CloudRain, Droplets, Sun, Thermometer } from 'lucide-react'
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../services/api'
import { AppShell, PageHeader } from '../components/Layout'
import { Badge, Card, ErrorState, SectionTitle, Skeleton } from '../components/ui'
import { cn, formatDate, formatNumber } from '../utils'

interface WeatherSummary {
  temperature: number | null
  rainfall: number | null
  humidity: number | null
  labels: string[]
  temperature_series: number[]
  rainfall_series: number[]
  humidity_series: number[]
  source: string
  updated_at: string | null
  daily_count: number
  is_demo: boolean
}

interface WeatherRow {
  id: number
  weather_date: string
  temperature: number
  rainfall: number
  humidity: number
  source: string
}

function WeatherTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl border border-line bg-white px-2.5 py-2 text-[10px] shadow-float backdrop-blur">
      <p className="mb-1 font-semibold text-ink">{label}</p>
      {payload.map((entry: any) => (
        <div key={entry.dataKey} className="flex items-center gap-1.5 py-0.5 text-muted">
          <span className="h-1.5 w-1.5 rounded-full" style={{ background: entry.color || entry.fill }} />
          <span>{entry.dataKey === 'temperature' ? 'Suhu' : 'Curah hujan'}</span>
          <span className="ml-auto pl-2 font-semibold text-ink">
            {formatNumber(entry.value, 1)}{entry.dataKey === 'temperature' ? '°C' : ' mm'}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function Weather() {
  const [summary, setSummary] = useState<WeatherSummary | null>(null)
  const [rows, setRows] = useState<WeatherRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [stats, list] = await Promise.all([
        api.get<WeatherSummary>('/weather/summary?weeks=12'),
        api.get<{ items: WeatherRow[] }>('/weather?page_size=10'),
      ])
      setSummary(stats)
      setRows(list.items)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Gagal memuat data cuaca.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const chartData = summary
    ? summary.labels.map((label, index) => ({
        label,
        temperature: summary.temperature_series[index],
        rainfall: summary.rainfall_series[index],
      }))
    : []

  return (
    <AppShell active="more">
      <PageHeader title="Data Cuaca" subtitle="Faktor pendukung permintaan obat" />
      <main className="px-4 pt-3">
        {loading && !summary ? (
          <div className="space-y-3">
            <Skeleton className="h-[100px] rounded-card" />
            <Skeleton className="h-[230px] rounded-card" />
            <Skeleton className="h-[260px] rounded-card" />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : summary ? (
          <>
            <div className="grid grid-cols-3 gap-2">
              {[
                { icon: <Thermometer size={14} />, label: 'Suhu rata-rata', value: summary.temperature !== null ? `${formatNumber(summary.temperature, 1)}°C` : '—', className: 'bg-[#FEF4E2] text-[#B47A16]' },
                { icon: <CloudRain size={14} />, label: 'Curah hujan', value: `${formatNumber(summary.rainfall || 0, 0)} mm`, className: 'bg-[#EAF3FC] text-[#2F73B9]' },
                { icon: <Droplets size={14} />, label: 'Kelembapan', value: summary.humidity !== null ? `${formatNumber(summary.humidity, 0)}%` : '—', className: 'bg-[#E7F6F0] text-secondary' },
              ].map((item) => (
                <div key={item.label} className="rounded-[12px] border border-line bg-white px-2.5 py-2.5 shadow-card">
                  <span className={cn('flex h-7 w-7 items-center justify-center rounded-[8px]', item.className)}>{item.icon}</span>
                  <p className="mt-1.5 text-[8px] uppercase leading-tight tracking-wide text-muted">{item.label}</p>
                  <p className="mt-0.5 text-[12px] font-bold text-ink">{item.value}</p>
                </div>
              ))}
            </div>

            <Card className="mt-3">
              <SectionTitle
                title="Tren Cuaca Mingguan"
                subtitle="12 pekan terakhir"
                icon={<Sun size={16} />}
                action={<Badge tone="info">{summary.daily_count} hari</Badge>}
              />
              <div className="mb-1 flex items-center gap-3 text-[9px] font-medium text-muted">
                <span className="inline-flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-[#F2A93B]" /> Suhu</span>
                <span className="inline-flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-[#7FC8E8]" /> Curah hujan</span>
              </div>
              <div className="h-[200px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chartData} margin={{ top: 8, right: 2, left: -28, bottom: 0 }}>
                    <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 4" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 8.5, fill: 'var(--chart-axis)' }} tickLine={false} axisLine={false} minTickGap={16} dy={4} />
                    <YAxis yAxisId="rain" hide />
                    <YAxis
                      yAxisId="temp"
                      tick={{ fontSize: 8.5, fill: 'var(--chart-axis)' }}
                      tickLine={false}
                      axisLine={false}
                      width={42}
                      domain={['dataMin - 1', 'dataMax + 1']}
                      tickFormatter={(value) => `${Math.round(value)}°`}
                    />
                    <Tooltip content={<WeatherTooltip />} cursor={{ fill: 'rgba(8,127,107,.04)' }} />
                    <Bar yAxisId="rain" dataKey="rainfall" fill="#7FC8E8" radius={[4, 4, 0, 0]} maxBarSize={14} />
                    <Line
                      yAxisId="temp"
                      type="monotone"
                      dataKey="temperature"
                      stroke="#F2A93B"
                      strokeWidth={2.2}
                      dot={{ r: 2.4, fill: '#F2A93B', strokeWidth: 0 }}
                      activeDot={{ r: 4 }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-1 text-[9px] text-[#93A3AC]">
                Sumber: {summary.source} · diperbarui {summary.updated_at ? formatDate(summary.updated_at) : '—'}
              </p>
            </Card>

            <Card className="mt-3">
              <SectionTitle title="Catatan Harian" subtitle="10 hari terakhir" icon={<CloudRain size={16} />} />
              <div className="divide-y divide-line">
                {rows.map((row) => (
                  <div key={row.id} className="flex items-center gap-2 py-2 first:pt-0 last:pb-0">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[8px] bg-[#EAF3FC] text-[#2F73B9]">
                      <CloudRain size={13} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-[10.5px] font-semibold text-ink">{formatDate(row.weather_date)}</p>
                      <p className="text-[8.5px] text-muted">{row.source}</p>
                    </div>
                    <div className="flex items-center gap-2.5 text-[9.5px]">
                      <span className="inline-flex items-center gap-0.5 text-[#B47A16]"><Thermometer size={10} />{formatNumber(row.temperature, 1)}°</span>
                      <span className="inline-flex items-center gap-0.5 text-[#2F73B9]"><Droplets size={10} />{formatNumber(row.humidity, 0)}%</span>
                      <span className="inline-flex items-center gap-0.5 text-muted"><CloudRain size={10} />{formatNumber(row.rainfall, 0)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <div className="mt-3 flex gap-2">
              <button onClick={() => api.download('/weather/export?fmt=xlsx', 'Data_Cuaca.xlsx')} className="flex-1 rounded-[10px] border border-line bg-white py-2 text-[10.5px] font-semibold text-ink">
                Ekspor Excel
              </button>
              <button onClick={() => api.download('/weather/export?fmt=csv', 'Data_Cuaca.csv')} className="flex-1 rounded-[10px] border border-line bg-white py-2 text-[10.5px] font-semibold text-ink">
                Ekspor CSV
              </button>
            </div>

            <p className="mt-2.5 px-1 text-[9px] leading-relaxed text-[#9AA9B2]">
              Cuaca digunakan sebagai fitur tambahan model. Nilai horizon memakai skenario normal iklim, bukan ramalan
              cuaca resmi. Sumber: NASA POWER (lokasi acuan Bandung).
            </p>
          </>
        ) : null}
      </main>
    </AppShell>
  )
}
