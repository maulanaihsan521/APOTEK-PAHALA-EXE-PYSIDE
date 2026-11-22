import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { cn, formatNumber } from '../utils'

const AXIS = { fontSize: 9, fill: 'var(--chart-axis)' } as const

function ChartTooltip({ active, payload, label, suffix }: any) {
  if (!active || !payload?.length) return null
  const rows = payload.filter((entry: any) => entry.value !== null && entry.value !== undefined && entry.dataKey !== 'base' && entry.dataKey !== 'band')
  if (!rows.length) return null
  return (
    <div className="min-w-[118px] rounded-xl border border-line bg-white px-2.5 py-2 text-[10px] shadow-float backdrop-blur">
      <p className="mb-1 font-semibold text-ink">{label}</p>
      {rows.map((entry: any) => (
        <div key={entry.dataKey} className="flex items-center gap-1.5 py-0.5 text-muted">
          <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: entry.color || entry.stroke }} />
          <span className="truncate">{entry.name}</span>
          <span className="ml-auto pl-2 font-semibold text-ink">
            {formatNumber(entry.value)}
            {suffix || ''}
          </span>
        </div>
      ))}
    </div>
  )
}

/* ------------------------------ Grafik tren ------------------------------- */
export function TrendChart({
  labels,
  actual,
  predicted,
  height = 190,
}: {
  labels: string[]
  actual: number[]
  predicted: (number | null)[]
  height?: number
}) {
  const data = labels.map((label, index) => ({
    label,
    aktual: actual[index] ?? null,
    prediksi: predicted[index] ?? null,
  }))
  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 4, left: -26, bottom: 0 }}>
          <defs>
            <linearGradient id="trendActual" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#087F6B" stopOpacity={0.22} />
              <stop offset="100%" stopColor="#087F6B" stopOpacity={0.01} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 4" vertical={false} />
          <XAxis
            dataKey="label"
            tick={AXIS}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
            minTickGap={18}
            dy={4}
          />
          <YAxis tick={AXIS} tickLine={false} axisLine={false} width={44} tickFormatter={(value) => formatNumber(value)} />
          <Tooltip content={<ChartTooltip />} cursor={{ stroke: 'var(--chart-cursor)', strokeWidth: 1, strokeDasharray: '3 3' }} />
          <Area
            type="monotone"
            dataKey="aktual"
            name="Aktual"
            stroke="#087F6B"
            strokeWidth={2.2}
            fill="url(#trendActual)"
            dot={false}
            activeDot={{ r: 3.5, strokeWidth: 2, stroke: '#fff' }}
            connectNulls
          />
          <Area
            type="monotone"
            dataKey="prediksi"
            name="Prediksi"
            stroke="#20B58A"
            strokeWidth={2}
            strokeDasharray="5 4"
            fill="transparent"
            dot={false}
            activeDot={{ r: 3, strokeWidth: 2, stroke: '#fff' }}
            connectNulls
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

/* --------------------------- Grafik prakiraan ----------------------------- */
export function ForecastChart({
  points,
  height = 210,
}: {
  points: { label: string; predicted: number; lower: number | null; upper: number | null }[]
  height?: number
}) {
  const data = points.map((point) => ({
    label: point.label,
    prediksi: point.predicted,
    batas_atas: point.upper,
    batas_bawah: point.lower,
  }))
  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 10, right: 6, left: -24, bottom: 0 }}>
          <defs>
            <linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#087F6B" stopOpacity={0.2} />
              <stop offset="100%" stopColor="#087F6B" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 4" vertical={false} />
          <XAxis dataKey="label" tick={AXIS} tickLine={false} axisLine={false} minTickGap={14} dy={4} />
          <YAxis tick={AXIS} tickLine={false} axisLine={false} width={44} tickFormatter={(value) => formatNumber(value)} />
          <Tooltip content={<ChartTooltip suffix=" unit" />} cursor={{ stroke: 'var(--chart-cursor)', strokeDasharray: '3 3' }} />
          <Area
            type="monotone"
            dataKey="prediksi"
            name="Prakiraan"
            stroke="#087F6B"
            strokeWidth={2.4}
            fill="url(#forecastFill)"
            dot={{ r: 3, fill: '#087F6B', strokeWidth: 2, stroke: '#fff' }}
            activeDot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="batas_atas"
            name="Batas atas"
            stroke="#20B58A"
            strokeWidth={1.2}
            strokeDasharray="4 4"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="batas_bawah"
            name="Batas bawah"
            stroke="#20B58A"
            strokeWidth={1.2}
            strokeDasharray="4 4"
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

/* -------------------------- Grafik backtest ------------------------------- */
export function BacktestChart({
  data,
  height = 180,
}: {
  data: { week: string; actual: number; predicted: number }[]
  height?: number
}) {
  const rows = data.map((row) => ({ label: row.week.slice(5), Aktual: row.actual, Prediksi: row.predicted }))
  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={rows} margin={{ top: 8, right: 4, left: -26, bottom: 0 }}>
          <defs>
            <linearGradient id="btActual" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#087F6B" stopOpacity={0.18} />
              <stop offset="100%" stopColor="#087F6B" stopOpacity={0.01} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 4" vertical={false} />
          <XAxis dataKey="label" tick={AXIS} tickLine={false} axisLine={false} minTickGap={20} dy={4} />
          <YAxis tick={AXIS} tickLine={false} axisLine={false} width={44} tickFormatter={(value) => formatNumber(value)} />
          <Tooltip content={<ChartTooltip />} cursor={{ stroke: 'var(--chart-cursor)', strokeDasharray: '3 3' }} />
          <Area type="monotone" dataKey="Aktual" stroke="#087F6B" strokeWidth={2} fill="url(#btActual)" dot={false} />
          <Area
            type="monotone"
            dataKey="Prediksi"
            stroke="#F2A93B"
            strokeWidth={1.8}
            strokeDasharray="4 3"
            fill="transparent"
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

/* ------------------------------ Donut chart ------------------------------- */
export function DonutChart({
  data,
  size = 132,
  thickness = 15,
  centerValue,
  centerLabel,
}: {
  data: { name: string; value: number; color: string }[]
  size?: number
  thickness?: number
  centerValue?: string
  centerLabel?: string
}) {
  const total = data.reduce((sum, item) => sum + item.value, 0) || 1
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={size / 2 - thickness}
            outerRadius={size / 2 - 2}
            startAngle={90}
            endAngle={-270}
            paddingAngle={2}
            cornerRadius={5}
            stroke="none"
          >
            {data.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<ChartTooltip suffix=" obat" />} />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-[18px] font-extrabold leading-none text-ink">{centerValue ?? total}</span>
        {centerLabel && <span className="mt-1 text-[9px] font-medium text-muted">{centerLabel}</span>}
      </div>
    </div>
  )
}

/* ----------------------------- Bar horizontal ----------------------------- */
export function MiniBars({
  data,
  color = '#087F6B',
  height = 132,
}: {
  data: { label: string; value: number }[]
  color?: string
  height?: number
}) {
  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 6, right: 4, left: -30, bottom: 0 }}>
          <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 4" vertical={false} />
          <XAxis dataKey="label" tick={AXIS} tickLine={false} axisLine={false} dy={4} />
          <YAxis tick={AXIS} tickLine={false} axisLine={false} width={44} tickFormatter={(value) => formatNumber(value)} />
          <Tooltip content={<ChartTooltip suffix=" unit" />} cursor={{ fill: 'rgba(8,127,107,.05)' }} />
          <Bar dataKey="value" name="Prakiraan" fill={color} radius={[6, 6, 2, 2]} maxBarSize={34} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/* ------------------------------- Sparkline -------------------------------- */
export function Sparkline({
  values,
  width = 64,
  height = 26,
  color = '#087F6B',
  className,
}: {
  values: number[]
  width?: number
  height?: number
  color?: string
  className?: string
}) {
  if (!values.length) return <div className={cn('h-[26px] w-[64px]', className)} />
  const max = Math.max(...values)
  const min = Math.min(...values)
  const span = max - min || 1
  const step = width / Math.max(values.length - 1, 1)
  const points = values.map((value, index) => {
    const x = index * step
    const y = height - 3 - ((value - min) / span) * (height - 6)
    return [x, y] as const
  })
  const line = points.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
  const area = `0,${height} ${line} ${width},${height}`
  const gradientId = `spark-${Math.abs(values.reduce((a, b) => a + b, 0))}-${color.replace('#', '')}`
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className={className} aria-hidden>
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.22} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      <polygon points={area} fill={`url(#${gradientId})`} />
      <polyline points={line} fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={points[points.length - 1][0]} cy={points[points.length - 1][1]} r={2.4} fill={color} />
    </svg>
  )
}
