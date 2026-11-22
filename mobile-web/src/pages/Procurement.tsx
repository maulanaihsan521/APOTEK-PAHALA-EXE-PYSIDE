import { useCallback, useEffect, useState } from 'react'
import {
  BadgeCheck,
  CalendarClock,
  ChevronDown,
  ClipboardList,
  Download,
  PencilLine,
  RefreshCw,
  Sparkles,
  Wallet,
} from 'lucide-react'
import { api } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { AppShell, PageHeader } from '../components/Layout'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Modal,
  SectionTitle,
  Select,
  Skeleton,
  Textarea,
} from '../components/ui'
import { cn, formatDate, formatNumber, formatRupiah, urgencyTone } from '../utils'

interface ProcurementItem {
  id: number
  medicine_id: number
  name: string
  code: string
  unit: string
  category: string
  current_stock: number
  predicted_demand: number
  safety_stock: number
  min_stock: number
  recommended_qty: number
  final_qty: number
  unit_price: number
  subtotal: number
  urgency: string
  reason: string
  adjustment_reason: string | null
}

interface Recommendation {
  available: boolean
  id: number
  code: string
  period_weeks: number
  status: string
  total_estimated_cost: number
  created_at: string
  updated_at: string
  notes: string | null
  assumptions: Record<string, number | string>
  items: ProcurementItem[]
  total_items: number
  total_units: number
}

const STATUS_LABEL: Record<string, string> = {
  draft: 'Draf',
  approved: 'Disetujui',
  cancelled: 'Dibatalkan',
}

export default function Procurement() {
  const { user } = useAuth()
  const { toast } = useToast()
  const isAdmin = user?.role?.toLowerCase() === 'admin'
  const [data, setData] = useState<Recommendation | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [period, setPeriod] = useState(4)
  const [expanded, setExpanded] = useState<number | null>(null)
  const [editItem, setEditItem] = useState<ProcurementItem | null>(null)
  const [editForm, setEditForm] = useState({ qty: '', reason: '' })
  const [saving, setSaving] = useState(false)
  const [approveOpen, setApproveOpen] = useState(false)
  const [actionError, setActionError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const result = await api.get<Recommendation>('/procurement/latest')
      setData(result.available ? result : null)
      if (result.available) setPeriod(result.period_weeks)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Gagal memuat rekomendasi.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const generate = async () => {
    setGenerating(true)
    setError('')
    try {
      const result = await api.post<Recommendation>('/procurement/generate', { period_weeks: period, notes: null })
      setData({ ...result, available: true })
      toast(`Rekomendasi ${result.code} berhasil dibuat.`, 'success')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Gagal membuat rekomendasi.')
    } finally {
      setGenerating(false)
    }
  }

  const approve = async () => {
    if (!data) return
    setSaving(true)
    try {
      const result = await api.post<Recommendation>(`/procurement/${data.id}/approve`)
      setData({ ...result, available: true })
      setApproveOpen(false)
      toast('Rekomendasi pengadaan disetujui.', 'success')
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : 'Gagal menyetujui rekomendasi.')
    } finally {
      setSaving(false)
    }
  }

  const openEdit = (item: ProcurementItem) => {
    setEditItem(item)
    setEditForm({ qty: String(item.final_qty), reason: item.adjustment_reason || '' })
    setActionError('')
  }

  const saveEdit = async () => {
    if (!data || !editItem) return
    setActionError('')
    const qty = Number(editForm.qty)
    if (!Number.isFinite(qty) || qty < 0) {
      setActionError('Jumlah harus nol atau lebih.')
      return
    }
    if (editForm.reason.trim().length < 3) {
      setActionError('Alasan perubahan minimal 3 karakter.')
      return
    }
    setSaving(true)
    try {
      const result = await api.patch<Recommendation>(`/procurement/${data.id}/items/${editItem.id}`, {
        final_qty: qty,
        reason: editForm.reason.trim(),
      })
      setData({ ...result, available: true })
      setEditItem(null)
      toast('Jumlah pembelian diperbarui.', 'success')
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : 'Gagal mengubah jumlah.')
    } finally {
      setSaving(false)
    }
  }

  const statusTone = data?.status === 'approved' ? 'success' : data?.status === 'cancelled' ? 'neutral' : 'warning'
  const exportFile = (format: 'pdf' | 'xlsx' | 'csv') => {
    if (!data) return
    api
      .download(`/procurement/${data.id}/export?fmt=${format}`, `Pengadaan_${data.code}.${format}`)
      .catch((reason) => setError(reason instanceof Error ? reason.message : 'Unduhan gagal.'))
  }

  return (
    <AppShell active="more">
      <PageHeader
        title="Rekomendasi Pengadaan"
        subtitle="Berdasarkan prakiraan & stok fisik"
        action={
          <button onClick={load} className="rounded-full border border-line bg-white p-2 text-muted shadow-card" aria-label="Muat ulang">
            <RefreshCw size={14} />
          </button>
        }
      />
      <main className="px-4 pt-3">
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-[150px] rounded-card" />
            <Skeleton className="h-[300px] rounded-card" />
          </div>
        ) : error && !data ? (
          <ErrorState message={error} onRetry={load} />
        ) : !data ? (
          <Card>
            <EmptyState
              icon={<ClipboardList size={22} />}
              title="Belum ada rekomendasi"
              description="Buat rekomendasi pembelian dari prakiraan permintaan dan posisi stok terkini."
            />
            <div className="mx-auto mt-1 max-w-[280px] space-y-2.5">
              <Field label="Periode pengadaan">
                <Select value={period} onChange={(event) => setPeriod(Number(event.target.value))}>
                  {[1, 2, 4, 8, 12].map((value) => (
                    <option key={value} value={value}>{value} pekan</option>
                  ))}
                </Select>
              </Field>
              <Button className="w-full" onClick={generate} loading={generating}>
                <Sparkles size={15} /> Buat Rekomendasi
              </Button>
            </div>
            {error && <p className="mt-2 text-center text-[10px] text-danger">{error}</p>}
          </Card>
        ) : (
          <>
            <Card className="overflow-hidden !p-0">
              <div className="bg-gradient-to-br from-[#0B5F52] via-[#087F6B] to-[#20B58A] px-4 py-3.5 text-white">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-white/65">Kode rekomendasi</p>
                    <p className="mt-0.5 text-[15px] font-extrabold">{data.code}</p>
                  </div>
                  <Badge className="border border-white/25 bg-white/15 !text-white" tone="neutral">
                    {STATUS_LABEL[data.status] || data.status}
                  </Badge>
                </div>
                <div className="mt-3 flex items-end justify-between gap-2">
                  <div>
                    <p className="text-[9px] text-white/65">Total perkiraan biaya</p>
                    <p className="text-[24px] font-extrabold leading-tight tracking-[-0.02em]">
                      {formatRupiah(data.total_estimated_cost)}
                    </p>
                  </div>
                  <div className="text-right text-[9px] text-white/70">
                    <p>{data.total_items} obat · {formatNumber(data.total_units)} unit</p>
                    <p className="mt-0.5">{data.period_weeks} pekan</p>
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between px-4 py-2.5">
                <p className="text-[9px] text-muted">Dibuat {formatDate(data.created_at)}</p>
                <div className="flex gap-1.5">
                  <button onClick={() => exportFile('pdf')} className="rounded-full border border-line p-1.5 text-muted" aria-label="Ekspor PDF"><Download size={12} /></button>
                  <button onClick={() => exportFile('xlsx')} className="rounded-full border border-line p-1.5 text-muted" aria-label="Ekspor Excel"><Download size={12} /></button>
                  <button onClick={() => exportFile('csv')} className="rounded-full border border-line p-1.5 text-muted" aria-label="Ekspor CSV"><Download size={12} /></button>
                </div>
              </div>
            </Card>

            <div className="mt-2.5 grid grid-cols-2 gap-2">
              <div className="rounded-[11px] border border-line bg-white px-3 py-2">
                <p className="flex items-center gap-1 text-[8.5px] uppercase tracking-wide text-muted"><CalendarClock size={10} /> Lead time</p>
                <p className="mt-0.5 text-[11.5px] font-bold text-ink">{formatNumber(Number(data.assumptions.lead_time_days ?? 7))} hari</p>
              </div>
              <div className="rounded-[11px] border border-line bg-white px-3 py-2">
                <p className="flex items-center gap-1 text-[8.5px] uppercase tracking-wide text-muted"><Wallet size={10} /> Safety stock</p>
                <p className="mt-0.5 text-[11.5px] font-bold text-ink">{formatNumber(Number(data.assumptions.safety_stock_days ?? 14))} hari</p>
              </div>
            </div>

            {data.status === 'draft' && isAdmin && (
              <div className="mt-2.5 flex gap-2">
                <Button variant="secondary" className="flex-1" onClick={() => setApproveOpen(true)}>
                  <BadgeCheck size={15} /> Setujui
                </Button>
                <Button variant="outline" onClick={load} aria-label="Muat ulang"><RefreshCw size={15} /></Button>
              </div>
            )}

            {(error || actionError) && (
              <p className="mt-2 rounded-[9px] bg-[#FDF3F3] px-3 py-2 text-[10px] text-danger">{error || actionError}</p>
            )}

            <Card className="mt-3 !px-0 !py-0">
              <div className="px-3.5 pt-3">
                <SectionTitle
                  title="Daftar Pembelian"
                  subtitle={`${data.items.filter((item) => item.final_qty > 0).length} obat perlu dibeli · ${data.items.filter((item) => item.final_qty <= 0).length} stok cukup`}
                  action={<Badge tone="primary">{data.items.length} item</Badge>}
                />
              </div>
              <div className="divide-y divide-line">
                {data.items.map((item) => {
                  const open = expanded === item.id
                  return (
                    <div key={item.id} className="px-3.5 py-2.5">
                      <button
                        onClick={() => setExpanded(open ? null : item.id)}
                        className="flex w-full items-start gap-2 text-left"
                      >
                        <span
                          className={cn(
                            'mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-[7px] text-[8.5px] font-bold',
                            item.urgency === 'kritis'
                              ? 'bg-[#FDECEC] text-danger'
                              : item.urgency === 'tinggi'
                                ? 'bg-[#FEF4E2] text-[#B47A16]'
                                : item.urgency === 'sedang'
                                  ? 'bg-[#EAF3FC] text-[#2F73B9]'
                                  : 'bg-[#E8F7F0] text-[#0E8A5F]',
                          )}
                        >
                          {item.final_qty > 0 ? item.final_qty : '—'}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-[11px] font-semibold text-ink">{item.name}</p>
                          <p className="mt-0.5 text-[8.5px] text-muted">
                            stok {formatNumber(item.current_stock)} → butuh {formatNumber(item.predicted_demand)} · {item.unit.toLowerCase()}
                          </p>
                        </div>
                        <div className="shrink-0 text-right">
                          <p className="text-[10.5px] font-bold text-ink">{item.final_qty > 0 ? formatRupiah(item.subtotal) : 'Tidak perlu beli'}</p>
                          <div className="mt-0.5 flex items-center justify-end gap-1">
                            <Badge tone={item.final_qty > 0 ? (urgencyTone(item.urgency) as 'success' | 'warning' | 'danger' | 'info') : 'success'}>
                              {item.final_qty > 0 ? item.urgency : 'cukup'}
                            </Badge>
                            <ChevronDown size={11} className={cn('text-[#C3CDD3] transition', open && 'rotate-180')} />
                          </div>
                        </div>
                      </button>

                      {open && (
                        <div className="mt-2 rounded-[9px] bg-[#F8FBFC] px-2.5 py-2">
                          <div className="grid grid-cols-4 gap-1 text-center">
                            {[
                              { label: 'Stok', value: item.current_stock },
                              { label: 'Prakiraan', value: Math.round(item.predicted_demand) },
                              { label: 'Safety', value: item.safety_stock },
                              { label: 'Saran', value: item.recommended_qty },
                            ].map((cell) => (
                              <div key={cell.label}>
                                <p className="text-[8px] uppercase text-muted">{cell.label}</p>
                                <p className="text-[10.5px] font-bold text-ink">{formatNumber(cell.value)}</p>
                              </div>
                            ))}
                          </div>
                          <p className="mt-1.5 text-[9px] leading-relaxed text-[#5C727B]">{item.reason}</p>
                          {item.adjustment_reason && (
                            <p className="mt-1 text-[9px] text-[#8A6A28]">Penyesuaian: {item.adjustment_reason}</p>
                          )}
                          {isAdmin && data.status === 'draft' && (
                            <button
                              onClick={() => openEdit(item)}
                              className="mt-1.5 inline-flex items-center gap-1 text-[9.5px] font-semibold text-primary"
                            >
                              <PencilLine size={11} /> Ubah jumlah final
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </Card>

            <Card className="mt-3">
              <SectionTitle title="Buat Ulang Rekomendasi" subtitle="Rekomendasi baru berstatus draf" icon={<Sparkles size={15} />} />
              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <Field label="Periode">
                    <Select value={period} onChange={(event) => setPeriod(Number(event.target.value))}>
                      {[1, 2, 4, 8, 12].map((value) => (
                        <option key={value} value={value}>{value} pekan</option>
                      ))}
                    </Select>
                  </Field>
                </div>
                <Button onClick={generate} loading={generating} className="mb-0.5">
                  <Sparkles size={14} /> Buat
                </Button>
              </div>
            </Card>

            <p className="mt-2.5 px-1 text-[9px] leading-relaxed text-[#9AA9B2]">
              Formula: prakiraan kebutuhan + stok pengaman + kebutuhan lead time − stok fisik, dibulatkan ke atas sesuai
              satuan pembelian. Angka adalah usulan dan tetap perlu ditinjau manajemen.
            </p>
          </>
        )}
      </main>

      <Modal
        open={Boolean(editItem)}
        onClose={() => setEditItem(null)}
        title="Ubah Jumlah Pembelian"
        subtitle={editItem?.name}
        footer={<Button className="w-full" onClick={saveEdit} loading={saving}>Simpan Perubahan</Button>}
      >
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-[10px] bg-[#F8FBFC] px-3 py-2">
              <p className="text-[9px] text-muted">Saran sistem</p>
              <p className="text-[15px] font-bold text-ink">{formatNumber(editItem?.recommended_qty || 0)}</p>
            </div>
            <Field label="Jumlah final" required>
              <Input
                type="number"
                min={0}
                value={editForm.qty}
                onChange={(event) => setEditForm((current) => ({ ...current, qty: event.target.value }))}
              />
            </Field>
          </div>
          <Field label="Alasan penyesuaian" required hint="Tersimpan pada riwayat aktivitas.">
            <Textarea
              rows={3}
              value={editForm.reason}
              onChange={(event) => setEditForm((current) => ({ ...current, reason: event.target.value }))}
              placeholder="Contoh: menyesuaikan dengan anggaran bulan ini"
            />
          </Field>
          {actionError && <p className="text-[10px] text-danger">{actionError}</p>}
        </div>
      </Modal>

      <ConfirmDialog
        open={approveOpen}
        onClose={() => setApproveOpen(false)}
        onConfirm={approve}
        title="Setujui rekomendasi?"
        message="Rekomendasi yang disetujui tidak dapat dibatalkan dan siap dijadikan daftar pembelian."
        confirmLabel="Ya, setujui"
        loading={saving}
      />
    </AppShell>
  )
}
