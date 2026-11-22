import { useCallback, useEffect, useMemo, useState } from 'react'
import { CalendarRange, Download, Plus, ReceiptText, Search } from 'lucide-react'
import { api } from '../services/api'
import { useToast } from '../context/ToastContext'
import { AppShell, PageHeader } from '../components/Layout'
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Modal,
  SearchInput,
  Select,
  Skeleton,
} from '../components/ui'
import { formatCompactRupiah, formatDate, formatNumber, formatRupiah, todayISO } from '../utils'

interface SaleRow {
  id: number
  transaction_code: string
  sale_date: string
  medicine_id: number
  medicine_name: string
  medicine_code: string
  unit: string
  quantity: number
  unit_price: number
  total_price: number
  source: string
}

interface SalesSummary {
  quantity: number
  revenue: number
  transactions: number
}

interface MedicineOption {
  id: number
  name: string
  code: string
  unit: string
  price: number
}

export default function Sales() {
  const { toast } = useToast()
  const [items, setItems] = useState<SaleRow[]>([])
  const [summary, setSummary] = useState<SalesSummary | null>(null)
  const [medicines, setMedicines] = useState<MedicineOption[]>([])
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [addOpen, setAddOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')
  const [form, setForm] = useState({
    medicine_id: '',
    sale_date: todayISO(),
    quantity: '1',
    unit_price: '',
  })

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(query)
      setPage(1)
    }, 400)
    return () => window.clearTimeout(timer)
  }, [query])

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '20',
        q: search,
      })
      if (start) params.set('start', start)
      if (end) params.set('end', end)
      const result = await api.get<{ items: SaleRow[]; total: number; pages: number }>(`/sales?${params}`)
      setItems((current) => (page === 1 ? result.items : [...current, ...result.items]))
      setPages(result.pages)
      setTotal(result.total)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Gagal memuat data permintaan.')
    } finally {
      setLoading(false)
    }
  }, [page, search, start, end])

  const loadSummary = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      if (start) params.set('start', start)
      if (end) params.set('end', end)
      const result = await api.get<SalesSummary>(`/sales/summary?${params}`)
      setSummary(result)
    } catch {
      setSummary(null)
    }
  }, [start, end])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    loadSummary()
  }, [loadSummary])

  useEffect(() => {
    api
      .get<MedicineOption[]>('/medicines')
      .then((rows) => {
        setMedicines(rows)
        setForm((current) => ({
          ...current,
          medicine_id: current.medicine_id || String(rows[0]?.id ?? ''),
          unit_price: current.unit_price || String(rows[0]?.price ?? ''),
        }))
      })
      .catch(() => undefined)
  }, [])

  const activeMedicine = medicines.find((item) => String(item.id) === form.medicine_id)
  const estimated = Math.max(0, Number(form.quantity) || 0) * Math.max(0, Number(form.unit_price) || 0)

  const submitSale = async () => {
    setFormError('')
    if (!form.medicine_id) {
      setFormError('Pilih obat terlebih dahulu.')
      return
    }
    const quantity = Number(form.quantity)
    if (!Number.isFinite(quantity) || quantity <= 0) {
      setFormError('Jumlah harus lebih dari nol.')
      return
    }
    setSaving(true)
    try {
      await api.post('/sales', {
        transaction_code: '',
        sale_date: form.sale_date,
        medicine_id: Number(form.medicine_id),
        quantity,
        unit_price: Number(form.unit_price) || 0,
      })
      toast('Transaksi penjualan berhasil dicatat.', 'success')
      setAddOpen(false)
      setForm((current) => ({ ...current, quantity: '1' }))
      setPage(1)
      await Promise.all([load(), loadSummary()])
    } catch (reason) {
      setFormError(reason instanceof Error ? reason.message : 'Gagal menyimpan transaksi.')
    } finally {
      setSaving(false)
    }
  }

  const grouped = useMemo(() => {
    const map = new Map<string, SaleRow[]>()
    items.forEach((item) => {
      const list = map.get(item.sale_date) || []
      list.push(item)
      map.set(item.sale_date, list)
    })
    return Array.from(map.entries())
  }, [items])

  return (
    <AppShell active="more">
      <PageHeader
        title="Data Penjualan"
        subtitle={`${formatNumber(total)} baris data tercatat`}
        action={
          <Button size="sm" onClick={() => setAddOpen(true)}>
            <Plus size={14} /> Catat
          </Button>
        }
      />
      <main className="px-4 pt-3">
        <div className="grid grid-cols-3 gap-2">
          {[
            { label: 'Estimasi Nilai', value: formatCompactRupiah(summary?.revenue || 0), title: formatRupiah(summary?.revenue || 0) },
            { label: 'Baris Data', value: formatNumber(summary?.transactions || 0) },
            { label: 'Estimasi Unit', value: formatNumber(summary?.quantity || 0) },
          ].map((item) => (
            <div key={item.label} className="rounded-[12px] border border-line bg-white px-2.5 py-2 shadow-card">
              <p className="text-[8.5px] uppercase tracking-wide text-muted">{item.label}</p>
              <p className="mt-0.5 truncate text-[11.5px] font-bold text-ink" title={'title' in item ? String(item.title) : undefined}>{item.value}</p>
            </div>
          ))}
        </div>

        <p className="mt-2 px-0.5 text-[9px] leading-relaxed text-[#9AA9B2]">
          Riwayat 2022–2026 adalah estimasi permintaan mingguan dari stok opname dan pembelian, bukan
          transaksi kasir. Baris yang dicatat manual adalah transaksi baru.
        </p>

        <div className="mt-3">
          <SearchInput value={query} onChange={setQuery} placeholder="Cari kode catatan atau obat..." />
        </div>

        <div className="mt-2 flex items-center gap-2">
          <button
            onClick={() => setFiltersOpen((value) => !value)}
            className="inline-flex items-center gap-1.5 rounded-full border border-line bg-white px-2.5 py-1.5 text-[10px] font-semibold text-muted"
          >
            <CalendarRange size={12} /> Rentang tanggal
          </button>
          {(start || end) && (
            <button
              onClick={() => {
                setStart('')
                setEnd('')
                setPage(1)
              }}
              className="text-[9.5px] font-semibold text-danger"
            >
              Hapus filter
            </button>
          )}
          <div className="ml-auto flex gap-1">
            <button
              onClick={() => api.download(`/sales/export?fmt=xlsx&start=${start}&end=${end}`, 'Data_Penjualan.xlsx')}
              className="rounded-full border border-line bg-white p-2 text-muted"
              aria-label="Ekspor Excel"
            >
              <Download size={13} />
            </button>
          </div>
        </div>

        {filtersOpen && (
          <Card className="mt-2 !p-3">
            <div className="grid grid-cols-2 gap-2">
              <Field label="Dari tanggal">
                <Input type="date" value={start} onChange={(event) => { setStart(event.target.value); setPage(1) }} />
              </Field>
              <Field label="Sampai tanggal">
                <Input type="date" value={end} onChange={(event) => { setEnd(event.target.value); setPage(1) }} />
              </Field>
            </div>
          </Card>
        )}

        {loading && page === 1 ? (
          <div className="mt-3 space-y-2">
            {[0, 1, 2, 3].map((index) => (
              <Skeleton key={index} className="h-[58px] rounded-[13px]" />
            ))}
          </div>
        ) : error ? (
          <div className="mt-3"><ErrorState message={error} onRetry={load} /></div>
        ) : items.length === 0 ? (
          <Card className="mt-3">
            <EmptyState icon={<Search size={20} />} title="Tidak ada data" description="Ubah kata kunci atau rentang tanggal, atau catat penjualan baru." />
          </Card>
        ) : (
          <div className="mt-3 space-y-3">
            {grouped.map(([date, rows]) => (
              <div key={date}>
                <div className="mb-1.5 flex items-center justify-between px-1">
                  <p className="text-[9.5px] font-semibold uppercase tracking-[0.08em] text-muted">{formatDate(date)}</p>
                  <p className="text-[9px] text-[#93A3AC]">{rows.length} baris data</p>
                </div>
                <div className="space-y-2">
                  {rows.map((row) => (
                    <div key={row.id} className="flex items-center gap-2.5 rounded-[13px] border border-line bg-white px-3 py-2.5 shadow-card">
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[9px] bg-primary/10 text-primary">
                        <ReceiptText size={14} />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-[11px] font-semibold text-ink">{row.medicine_name}</p>
                        <p className="mt-0.5 truncate text-[8.5px] text-muted">
                          {row.quantity} {row.unit.toLowerCase()} × {formatRupiah(row.unit_price)} · {row.transaction_code}
                        </p>
                      </div>
                      <div className="shrink-0 text-right">
                        <p className="text-[11px] font-bold text-ink">{formatRupiah(row.total_price)}</p>
                        <Badge tone={row.source === 'import' || row.source === 'stok_opname' ? 'info' : 'neutral'} className="mt-0.5">
                          {row.source === 'stok_opname' ? 'Stok opname' : row.source === 'import' ? 'Import' : 'Manual'}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {page < pages && (
              <Button variant="outline" className="w-full" onClick={() => setPage((value) => value + 1)} loading={loading}>
                Muat lebih banyak
              </Button>
            )}
          </div>
        )}
      </main>

      <Modal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        title="Catat Penjualan"
        subtitle="Transaksi akan langsung menambah riwayat permintaan"
        footer={
          <Button className="w-full" onClick={submitSale} loading={saving}>
            Simpan Transaksi
          </Button>
        }
      >
        <div className="space-y-3">
          <Field label="Obat" required>
            <Select
              value={form.medicine_id}
              onChange={(event) => {
                const selected = medicines.find((item) => String(item.id) === event.target.value)
                setForm((current) => ({
                  ...current,
                  medicine_id: event.target.value,
                  unit_price: selected ? String(selected.price) : current.unit_price,
                }))
              }}
            >
              {medicines.map((medicine) => (
                <option key={medicine.id} value={medicine.id}>
                  {medicine.name} ({medicine.code})
                </option>
              ))}
            </Select>
          </Field>
          <div className="grid grid-cols-2 gap-2.5">
            <Field label="Tanggal" required>
              <Input
                type="date"
                value={form.sale_date}
                max={todayISO()}
                onChange={(event) => setForm((current) => ({ ...current, sale_date: event.target.value }))}
              />
            </Field>
            <Field label="Jumlah" required hint={activeMedicine ? activeMedicine.unit : undefined}>
              <Input
                type="number"
                min={1}
                value={form.quantity}
                onChange={(event) => setForm((current) => ({ ...current, quantity: event.target.value }))}
              />
            </Field>
          </div>
          <Field label="Harga satuan">
            <Input
              type="number"
              min={0}
              value={form.unit_price}
              onChange={(event) => setForm((current) => ({ ...current, unit_price: event.target.value }))}
            />
          </Field>
          <div className="flex items-center justify-between rounded-[10px] bg-[#F4FBF8] px-3 py-2">
            <span className="text-[10.5px] text-muted">Perkiraan total</span>
            <span className="text-[13px] font-bold text-secondary">{formatRupiah(estimated)}</span>
          </div>
          {formError && <p className="text-[10.5px] text-danger">{formError}</p>}
        </div>
      </Modal>
    </AppShell>
  )
}
