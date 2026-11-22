export function cn(...values: (string | false | null | undefined)[]) {
  return values.filter(Boolean).join(' ')
}

const numberFormat = new Intl.NumberFormat('id-ID')

export function formatNumber(value: number | null | undefined, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  return new Intl.NumberFormat('id-ID', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)
}

export function formatRupiah(value: number | null | undefined) {
  if (value === null || value === undefined) return '-'
  return `Rp ${numberFormat.format(Math.round(value))}`
}

export function formatCompactRupiah(value: number | null | undefined) {
  if (value === null || value === undefined) return '-'
  if (Math.abs(value) >= 1_000_000_000) return `Rp ${formatNumber(value / 1_000_000_000, 1)} M`
  if (Math.abs(value) >= 1_000_000) return `Rp ${formatNumber(value / 1_000_000, 1)} jt`
  if (Math.abs(value) >= 1_000) return `Rp ${formatNumber(value / 1_000, 0)} rb`
  return formatRupiah(value)
}

export function formatPercent(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined) return '-'
  return `${formatNumber(value, digits)}%`
}

/** Tanggal tanpa jam diperlakukan sebagai tanggal lokal; timestamp tanpa zona
 *  dianggap UTC agar waktu dari API ditampilkan dalam zona perangkat. */
function parseApiDate(value: string) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return new Date(`${value}T00:00:00`)
  const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value)
  return new Date(hasZone ? value : `${value}Z`)
}

export function formatDate(value: string | null | undefined, options?: Intl.DateTimeFormatOptions) {
  if (!value) return '-'
  const date = parseApiDate(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('id-ID', options || { day: '2-digit', month: 'short', year: 'numeric' }).format(date)
}

export function formatDateTime(value: string | null | undefined) {
  if (!value) return '-'
  const date = parseApiDate(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('id-ID', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(date)
}

export function relativeTime(value: string) {
  const date = parseApiDate(value)
  const diff = Date.now() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'Baru saja'
  if (minutes < 60) return `${minutes} menit lalu`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} jam lalu`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days} hari lalu`
  return formatDate(value)
}

export type StockStatus = 'aman' | 'perlu_perhatian' | 'kritis'

export function statusLabel(status: StockStatus | string) {
  if (status === 'perlu_perhatian') return 'Periksa'
  if (status === 'kritis') return 'Kritis'
  return 'Aman'
}

export function statusTone(status: StockStatus | string) {
  if (status === 'kritis') return 'danger'
  if (status === 'perlu_perhatian') return 'warning'
  return 'success'
}

export function urgencyTone(urgency: string) {
  if (urgency === 'kritis') return 'danger'
  if (urgency === 'tinggi') return 'warning'
  if (urgency === 'sedang') return 'info'
  return 'success'
}

/** Format tanggal lokal sebagai YYYY-MM-DD tanpa konversi UTC. */
export function isoDate(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function todayISO(offsetDays = 0) {
  const date = new Date()
  date.setDate(date.getDate() + offsetDays)
  return isoDate(date)
}

export function monthStartISO() {
  const date = new Date()
  return isoDate(new Date(date.getFullYear(), date.getMonth(), 1))
}

export function greeting() {
  const hour = new Date().getHours()
  if (hour < 11) return 'Selamat pagi'
  if (hour < 15) return 'Selamat siang'
  if (hour < 18) return 'Selamat sore'
  return 'Selamat malam'
}

export function initials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
}
