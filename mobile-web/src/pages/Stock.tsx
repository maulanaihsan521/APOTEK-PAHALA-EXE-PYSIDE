import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Boxes,
  ChevronRight,
  Download,
  History,
  Loader2,
  Package,
  Search,
  SlidersHorizontal,
  TriangleAlert,
} from 'lucide-react'
import { api } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { AppShell, PageHeader } from '../components/Layout'
import { DonutChart } from '../components/charts'
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Modal,
  SectionTitle,
  Select,
  Skeleton,
  StockBadge,
  Textarea,
  SearchInput,
} from '../components/ui'
import { cn, formatDate, formatNumber, formatRupiah } from '../utils'

interface StockRow {
  medicine_id: number
  code: string
  name: string
  category: string
  unit: string
  price: number
  system_stock: number
  physical_stock: number
  difference: number
  min_stock: number
  safety_stock: number
  status: 'aman' | 'perlu_perhatian' | 'kritis'
  last_opname_date: string | null
  inventory_id: number | null
  updated_at: string | null
  is_priority: boolean
}

interface StockSummary {
  aman: number
  perlu_perhatian: number
  kritis: number
  total: number
  total_units: number
  total_system: number
  difference: number
  last_opname_date: string | null
}

interface Movement {
  id: number
  date: string
  stock_before: number
  stock_after: number
  change_type: string
  quantity_change: number
  note: string | null
}

const FILTERS = [
  { value: '', label: 'Semua' },
  { value: 'aman', label: 'Aman' },
  { value: 'perlu_perhatian', label: 'Periksa' },
  { value: 'kritis', label: 'Kritis' },
]

export default function Stock() {
  const { user } = useAuth()
  const isAdmin = user?.role?.toLowerCase() === 'admin'
  const [rows, setRows] = useState<StockRow[]>([])
  const [summary, setSummary] = useState<StockSummary | null>(null)
  const [categories, setCategories] = useState<string[]>([])
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('')
  const [category, setCategory] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [history, setHistory] = useState<Movement[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [form, setForm] = useState({ physical: '', system: '', type: 'opname', note: '' })
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [items, stats, cats] = await Promise.all([
        api.get<StockRow[]>('/inventory'),
        api.get<StockSummary>('/inventory/summary'),
        api.get<string[]>('/medicines/categories'),
      ])
      setRows(items)
      setSummary(stats)
      setCategories(cats)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Gagal memuat data stok.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    return rows.filter((row) => {
      if (filter && row.status !== filter) return false
      if (category && row.category !== category) return false
      if (term && !row.name.toLowerCase().includes(term) && !row.code.toLowerCase().includes(term)) return false
      return true
    })
  }, [rows, search, filter, category])

  const selected = rows.find((row) => row.medicine_id === selectedId) || null

  const openDetail = async (row: StockRow) => {
    setSelectedId(row.medicine_id)
    setForm({
      physical: String(row.physical_stock),
      system: String(row.system_stock),
      type: 'opname',
      note: '',
    })
    setFormError('')
    setHistory([])
    setHistoryLoading(true)
    try {
      const data = await api.get<Movement[]>(`/inventory/${row.medicine_id}/history`)
      setHistory(data)
    } catch {
      setHistory([])
    } finally {
      setHistoryLoading(false)
    }
  }

  const saveAdjustment = async () => {
    if (!selected) return
    setFormError('')
    const physical = Number(form.physical)
    const system = Number(form.system)
    if (!Number.isFinite(physical) || physical < 0 || !Number.isFinite(system) || system < 0) {
      setFormError('Stok harus berupa angka nol atau lebih.')
      return
    }
    if (form.note.trim().length < 3) {
      setFormError('Catatan minimal 3 karakter agar perubahan dapat diaudit.')
      return
    }
    setSaving(true)
    try {
      await api.post(`/inventory/${selected.medicine_id}/adjust`, {
        physical_stock: physical,
        system_stock: system,
        change_type: form.type,
        note: form.note.trim(),
      })
      setSelectedId(null)
      await load()
    } catch (reason) {
      setFormError(reason instanceof Error ? reason.message : 'Gagal menyimpan penyesuaian.')
    } finally {
      setSaving(false)
    }
  }

  const donut = summary
    ? [
        { name: 'Aman', value: summary.aman, color: '#16A36A' },
        { name: 'Perlu perhatian', value: summary.perlu_perhatian, color: '#F2A93B' },
        { name: 'Kritis', value: summary.kritis, color: '#E55353' },
      ]
    : []

  return (
    <AppShell active="stock">
      <PageHeader
        title="Manajemen Stok"
        subtitle="Posisi persediaan & stock opname"
        action={
          <button onClick={load} className="rounded-full border border-line bg-white p-2 text-muted shadow-card" aria-label="Muat ulang">
            <SlidersHorizontal size={15} />
          </button>
        }
      />
      <main className="px-4 pt-3">
        {loading && !summary ? (
          <div className="space-y-3">
            <Skeleton className="h-[150px] rounded-card" />
            <Skeleton className="h-11" />
            <Skeleton className="h-[300px] rounded-card" />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : (
          <>
            <Card>
              <div className="flex items-center gap-4">
                {summary && <DonutChart data={donut} size={118} thickness={13} centerValue={String(summary.total)} centerLabel="obat" />}
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex items-center justify-between">
                    <p className="text-[12.5px] font-bold text-ink">Ringkasan Stok</p>
                    <Badge tone="neutral">{summary?.total_units ? `${formatNumber(summary.total_units)} unit` : '—'}</Badge>
                  </div>
                  {donut.map((item) => (
                    <div key={item.name} className="flex items-center gap-2 py-0.5">
                      <span className="h-2 w-2 rounded-full" style={{ background: item.color }} />
                      <span className="flex-1 text-[10px] text-muted">{item.name}</span>
                      <span className="text-[10px] font-bold text-ink">{item.value}</span>
                    </div>
                  ))}
                  <p className="mt-1 text-[8.5px] text-[#93A3AC]">
                    Opname terakhir {summary?.last_opname_date ? formatDate(summary.last_opname_date) : 'belum tercatat'}
                  </p>
                </div>
              </div>
              <div className="mt-2.5 grid grid-cols-3 gap-1.5">
                <div className="rounded-[9px] bg-[#F8FBFC] px-2 py-1.5">
                  <p className="text-[8px] uppercase tracking-wide text-muted">Stok fisik</p>
                  <p className="text-[11px] font-bold text-ink">{formatNumber(summary?.total_units || 0)}</p>
                </div>
                <div className="rounded-[9px] bg-[#F8FBFC] px-2 py-1.5">
                  <p className="text-[8px] uppercase tracking-wide text-muted">Stok sistem</p>
                  <p className="text-[11px] font-bold text-ink">{formatNumber(summary?.total_system || 0)}</p>
                </div>
                <div className="rounded-[9px] bg-[#F8FBFC] px-2 py-1.5">
                  <p className="text-[8px] uppercase tracking-wide text-muted">Selisih</p>
                  <p className={cn('text-[11px] font-bold', (summary?.difference || 0) === 0 ? 'text-ink' : 'text-warning')}>
                    {summary && summary.difference > 0 ? '+' : ''}
                    {formatNumber(summary?.difference || 0)}
                  </p>
                </div>
              </div>
            </Card>

            {summary && summary.kritis > 0 && (
              <div className="mt-2.5 flex items-start gap-2 rounded-[11px] border border-[#F6DADA] bg-[#FDF3F3] px-3 py-2.5">
                <TriangleAlert size={14} className="mt-0.5 shrink-0 text-danger" />
                <div>
                  <p className="text-[10.5px] font-semibold text-[#B63B3B]">{summary.kritis} obat kritis</p>
                  <p className="text-[9.5px] leading-relaxed text-[#9C5B5B]">
                    Stok berada di bawah atau sama dengan minimum. Segera buat rekomendasi pengadaan.
                  </p>
                </div>
              </div>
            )}

            <div className="mt-3">
              <SearchInput value={search} onChange={setSearch} placeholder="Cari nama atau kode obat..." />
            </div>

            <div className="mt-2 flex flex-wrap gap-1.5 pb-1">
              {FILTERS.map((item) => {
                const count =
                  item.value === ''
                    ? rows.length
                    : rows.filter((row) => row.status === item.value).length
                return (
                  <button
                    key={item.value}
                    onClick={() => setFilter(item.value)}
                    className={cn(
                      'shrink-0 rounded-full border px-2.5 py-1.5 text-[10px] font-semibold transition',
                      filter === item.value
                        ? 'border-primary bg-primary text-white'
                        : 'border-line bg-white text-muted',
                    )}
                  >
                    {item.label} <span className="opacity-70">({count})</span>
                  </button>
                )
              })}
            </div>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className="mt-1 h-[33px] w-full rounded-[10px] border border-line bg-white px-2.5 text-[10px] font-semibold text-muted"
            >
              <option value="">Semua kategori</option>
              {categories.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>

            <div className="mt-2 space-y-2">
              {filtered.map((row) => (
                <button
                  key={row.medicine_id}
                  onClick={() => openDetail(row)}
                  className="flex w-full items-center gap-3 rounded-[13px] border border-line bg-white px-3 py-2.5 text-left shadow-card transition active:scale-[.995]"
                >
                  <span
                    className={cn(
                      'flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px]',
                      row.status === 'kritis'
                        ? 'bg-[#FDECEC] text-danger'
                        : row.status === 'perlu_perhatian'
                          ? 'bg-[#FEF4E2] text-[#B47A16]'
                          : 'bg-[#E8F7F0] text-[#0E8A5F]',
                    )}
                  >
                    <Package size={16} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <p className="truncate text-[11.5px] font-semibold text-ink">{row.name}</p>
                      {row.is_priority && <span className="text-[8px] font-bold text-warning">★</span>}
                    </div>
                    <p className="mt-0.5 truncate text-[9px] text-muted">
                      {row.code} · min {formatNumber(row.min_stock)} {row.unit.toLowerCase()}
                    </p>
                    <div className="mt-1 flex items-center gap-1.5">
                      <span className="text-[10px] font-bold text-ink">{formatNumber(row.physical_stock)}</span>
                      <span className="text-[8.5px] text-muted">fisik</span>
                      <span className="text-[8.5px] text-[#C3CDD3]">·</span>
                      <span className="text-[9px] text-muted">sistem {formatNumber(row.system_stock)}</span>
                      {row.difference !== 0 && (
                        <span className={cn('text-[8.5px] font-semibold', row.difference > 0 ? 'text-info' : 'text-warning')}>
                          ({row.difference > 0 ? '+' : ''}{formatNumber(row.difference)})
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-1">
                    <StockBadge status={row.status} />
                    <ChevronRight size={13} className="text-[#C3CDD3]" />
                  </div>
                </button>
              ))}
              {filtered.length === 0 && (
                <Card>
                  <EmptyState icon={<Search size={20} />} title="Tidak ada obat" description="Ubah kata kunci atau filter status." compact />
                </Card>
              )}
            </div>

            <div className="mt-3 grid grid-cols-2 gap-2">
              <Button variant="outline" size="sm" onClick={() => api.download('/inventory/export?fmt=xlsx', 'Data_Stok.xlsx')}>
                <Download size={14} /> Excel
              </Button>
              <Button variant="outline" size="sm" onClick={() => api.download('/inventory/export?fmt=csv', 'Data_Stok.csv')}>
                <Download size={14} /> CSV
              </Button>
            </div>

            <div className="mt-3 rounded-[11px] bg-[#EFF9F5] px-3 py-2.5">
              <p className="flex items-start gap-1.5 text-[9.5px] leading-relaxed text-[#3E6B62]">
                <Boxes size={12} className="mt-0.5 shrink-0" />
                Status dihitung dari stok fisik: <b>kritis</b> bila ≤ minimum, <b>perlu perhatian</b> bila &lt; 1,5 ×
                minimum, selebihnya <b>aman</b>. Stok berasal dari opname terakhir.
              </p>
            </div>
          </>
        )}
      </main>

      <Modal
        open={Boolean(selected)}
        onClose={() => setSelectedId(null)}
        title={selected?.name || 'Detail obat'}
        subtitle={selected ? `${selected.code} · ${selected.category}` : undefined}
        size="lg"
        footer={
          isAdmin ? (
            <Button className="w-full" onClick={saveAdjustment} loading={saving}>
              Simpan Penyesuaian
            </Button>
          ) : (
            <p className="text-center text-[10px] text-muted">Hanya Admin yang dapat menyesuaikan stok.</p>
          )
        }
      >
        {selected && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: 'Stok fisik', value: formatNumber(selected.physical_stock), tone: 'text-primary' },
                { label: 'Stok sistem', value: formatNumber(selected.system_stock), tone: 'text-ink' },
                { label: 'Minimum stok', value: formatNumber(selected.min_stock), tone: 'text-ink' },
                { label: 'Selisih', value: `${selected.difference > 0 ? '+' : ''}${formatNumber(selected.difference)}`, tone: selected.difference === 0 ? 'text-ink' : 'text-warning' },
              ].map((item) => (
                <div key={item.label} className="rounded-[10px] border border-line bg-[#F8FBFC] px-3 py-2">
                  <p className="text-[9px] text-muted">{item.label}</p>
                  <p className={cn('mt-0.5 text-[15px] font-extrabold', item.tone)}>{item.value}</p>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between rounded-[10px] border border-line px-3 py-2">
              <div>
                <p className="text-[10px] text-muted">Status persediaan</p>
                <p className="mt-0.5 text-[9px] text-[#93A3AC]">
                  Harga {formatRupiah(selected.price)} / {selected.unit.toLowerCase()}
                </p>
              </div>
              <StockBadge status={selected.status} />
            </div>

            {isAdmin && (
              <div className="space-y-2.5 rounded-[12px] border border-[#CFEDE2] bg-[#F4FBF8] p-3">
                <p className="flex items-center gap-1.5 text-[11px] font-bold text-ink">
                  <SlidersHorizontal size={13} className="text-primary" /> Penyesuaian stok
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <Field label="Stok fisik">
                    <Input
                      type="number"
                      min={0}
                      value={form.physical}
                      onChange={(event) => setForm((current) => ({ ...current, physical: event.target.value }))}
                    />
                  </Field>
                  <Field label="Stok sistem">
                    <Input
                      type="number"
                      min={0}
                      value={form.system}
                      onChange={(event) => setForm((current) => ({ ...current, system: event.target.value }))}
                    />
                  </Field>
                </div>
                <Field label="Jenis perubahan">
                  <Select value={form.type} onChange={(event) => setForm((current) => ({ ...current, type: event.target.value }))}>
                    <option value="opname">Stock opname</option>
                    <option value="penambahan">Penambahan</option>
                    <option value="pengurangan">Pengurangan</option>
                    <option value="koreksi">Koreksi</option>
                  </Select>
                </Field>
                <Field label="Catatan" hint="Wajib diisi, minimal 3 karakter.">
                  <Textarea
                    rows={2}
                    value={form.note}
                    onChange={(event) => setForm((current) => ({ ...current, note: event.target.value }))}
                    placeholder="Contoh: hasil hitung fisik rak A3"
                  />
                </Field>
                {formError && <p className="text-[10px] text-danger">{formError}</p>}
              </div>
            )}

            <div>
              <SectionTitle title="Riwayat Perubahan" icon={<History size={14} />} />
              {historyLoading ? (
                <div className="flex justify-center py-4"><Loader2 size={18} className="animate-spin text-primary" /></div>
              ) : history.length === 0 ? (
                <p className="rounded-[9px] bg-[#F8FBFC] py-4 text-center text-[10px] text-muted">Belum ada riwayat perubahan.</p>
              ) : (
                <div className="space-y-2">
                  {history.slice(0, 6).map((movement) => (
                    <div key={movement.id} className="flex items-start gap-2 border-b border-line pb-2 last:border-0">
                      <span
                        className={cn(
                          'mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[9px] font-bold',
                          movement.quantity_change > 0 ? 'bg-[#E8F7F0] text-[#0E8A5F]' : movement.quantity_change < 0 ? 'bg-[#FDECEC] text-[#D14343]' : 'bg-slate-100 text-muted',
                        )}
                      >
                        {movement.quantity_change > 0 ? '+' : ''}
                        {formatNumber(movement.quantity_change)}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="text-[10px] font-medium capitalize text-ink">
                          {movement.change_type.replace('_', ' ')} · {formatNumber(movement.stock_before)} → {formatNumber(movement.stock_after)}
                        </p>
                        <p className="text-[9px] text-muted">{movement.note || 'Tanpa catatan'} · {formatDate(movement.date)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>
    </AppShell>
  )
}
