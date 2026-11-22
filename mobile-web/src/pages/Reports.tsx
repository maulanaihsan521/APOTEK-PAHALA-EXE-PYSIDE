import { useCallback, useEffect, useState } from 'react'
import { CalendarRange, Download, FileBarChart, FileSpreadsheet, FileText, RefreshCw } from 'lucide-react'
import { api } from '../services/api'
import { AppShell, PageHeader } from '../components/Layout'
import { Badge, Button, Card, ErrorState, Field, Input, SectionTitle, Select, Skeleton } from '../components/ui'
import { formatDate, formatNumber, isoDate, monthStartISO, todayISO } from '../utils'

interface ReportType {
  value: string
  label: string
}

interface ReportPayload {
  type: string
  title: string
  meta: Record<string, string>
  summary: [string, string][]
  columns: string[]
  rows: (string | number)[][]
  chart: [string, number][]
  notes: string
  start: string
  end: string
  generated_at: string
}

export default function Reports() {
  const [types, setTypes] = useState<ReportType[]>([])
  const [type, setType] = useState('sales')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [rangeStart, setRangeStart] = useState('')
  const [rangeEnd, setRangeEnd] = useState('')
  const [booting, setBooting] = useState(true)
  const [report, setReport] = useState<ReportPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const shiftDate = (value: string, days: number) => {
    const date = new Date(`${value}T00:00:00`)
    date.setDate(date.getDate() + days)
    return isoDate(date)
  }

  useEffect(() => {
    api
      .get<ReportType[]>('/reports/types')
      .then(setTypes)
      .catch(() => undefined)
  }, [])

  useEffect(() => {
    let active = true
    api
      .get<{ start: string; end: string }>('/reports/range')
      .then((range) => {
        if (!active) return
        setRangeStart(range.start)
        setRangeEnd(range.end)
        setStart(shiftDate(range.end, -29))
        setEnd(range.end)
      })
      .catch(() => {
        if (!active) return
        const fallback = todayISO()
        setRangeStart(monthStartISO())
        setRangeEnd(fallback)
        setStart(shiftDate(fallback, -29))
        setEnd(fallback)
      })
      .finally(() => {
        if (active) setBooting(false)
      })
    return () => {
      active = false
    }
  }, [])

  const load = useCallback(async () => {
    if (!start || !end) return
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams({ type, start, end })
      const result = await api.get<ReportPayload>(`/reports/summary?${params}`)
      setReport(result)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Gagal menyusun laporan.')
    } finally {
      setLoading(false)
    }
  }, [type, start, end])

  useEffect(() => {
    if (!booting) load()
  }, [load, booting])

  const download = (format: 'pdf' | 'xlsx' | 'csv') => {
    api
      .download(
        `/reports/export?type=${type}&fmt=${format}&start=${start}&end=${end}`,
        `${report?.title.replace(/\s+/g, '_') || 'Laporan'}.${format}`,
      )
      .catch((reason) => setError(reason instanceof Error ? reason.message : 'Unduhan gagal.'))
  }

  return (
    <AppShell active="more">
      <PageHeader
        title="Laporan"
        subtitle="Siap cetak dan diunduh"
        action={
          <button onClick={load} className="rounded-full border border-line bg-white p-2 text-muted shadow-card" aria-label="Susun ulang">
            <RefreshCw size={14} />
          </button>
        }
      />
      <main className="px-4 pt-3">
        <Card>
          <SectionTitle title="Parameter Laporan" icon={<FileBarChart size={15} />} />
          <div className="space-y-2.5">
            <Field label="Jenis laporan">
              <Select value={type} onChange={(event) => setType(event.target.value)}>
                {(types.length ? types : [{ value: 'sales', label: 'Laporan Penjualan' }]).map((item) => (
                  <option key={item.value} value={item.value}>{item.label}</option>
                ))}
              </Select>
            </Field>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Dari">
                <Input type="date" value={start} max={end || rangeEnd} onChange={(event) => setStart(event.target.value)} />
              </Field>
              <Field label="Sampai">
                <Input type="date" value={end} min={start} max={rangeEnd} onChange={(event) => setEnd(event.target.value)} />
              </Field>
            </div>
            <div className="grid grid-cols-3 gap-1.5">
              <Button size="sm" variant="outline" onClick={() => { const anchor = rangeEnd || todayISO(); setStart(shiftDate(anchor, -29)); setEnd(anchor) }}>
                30 hari
              </Button>
              <Button size="sm" variant="outline" onClick={() => { const anchor = rangeEnd || todayISO(); const date = new Date(`${anchor}T00:00:00`); date.setMonth(date.getMonth() - 3); setStart(isoDate(date)); setEnd(anchor) }}>
                3 bulan
              </Button>
              <Button size="sm" variant="outline" onClick={() => { setStart(rangeStart || '2022-01-01'); setEnd(rangeEnd || todayISO()) }}>
                Semua
              </Button>
            </div>
            {rangeStart && rangeEnd && (
              <p className="text-[8.5px] text-[#93A3AC]">
                Data tersedia {formatDate(rangeStart)} – {formatDate(rangeEnd)}. Periode awal mengikuti data terakhir.
              </p>
            )}
          </div>
        </Card>

        {loading || booting ? (
          <div className="mt-3 space-y-3">
            <Skeleton className="h-[150px] rounded-card" />
            <Skeleton className="h-[240px] rounded-card" />
          </div>
        ) : error ? (
          <div className="mt-3"><ErrorState message={error} onRetry={load} /></div>
        ) : report ? (
          <>
            <Card className="mt-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-primary">Laporan</p>
                  <h2 className="mt-0.5 text-[14px] font-bold text-ink">{report.title}</h2>
                  <p className="mt-0.5 flex items-center gap-1 text-[9.5px] text-muted">
                    <CalendarRange size={11} />
                    {formatDate(report.start)} – {formatDate(report.end)}
                  </p>
                </div>
                <Badge tone="success" dot>{report.meta['Label data'] || 'AKTUAL'}</Badge>
              </div>
              <div className="mt-3 space-y-1.5">
                {report.summary.map(([key, value]) => (
                  <div key={key} className="flex items-start justify-between gap-3 rounded-[8px] bg-[#F8FBFC] px-2.5 py-1.5">
                    <span className="text-[10px] text-muted">{key}</span>
                    <span className="text-right text-[10.5px] font-bold text-ink">{value}</span>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="mt-3 !px-0">
              <div className="px-3.5">
                <SectionTitle
                  title="Tabel Data"
                  subtitle={`${formatNumber(report.rows.length)} baris`}
                  icon={<FileText size={15} />}
                />
              </div>
              <div className="divide-y divide-line">
                {report.rows.slice(0, 40).map((row, index) => (
                  <div key={index} className="px-3.5 py-2.5">
                    <p className="text-[10.5px] font-bold text-ink">{typeof row[0] === 'number' ? formatNumber(row[0]) : String(row[0])}</p>
                    {report.columns.length > 1 && (
                      <div className="mt-1.5 grid grid-cols-2 gap-x-3 gap-y-1.5">
                        {report.columns.slice(1).map((column, cellIndex) => {
                          const cell = row[cellIndex + 1]
                          return (
                            <div key={column} className="min-w-0">
                              <p className="text-[7.5px] font-semibold uppercase tracking-wide text-muted">{column}</p>
                              <p className="mt-0.5 break-words text-[9.5px] font-semibold text-ink">
                                {typeof cell === 'number' ? formatNumber(cell) : String(cell ?? '—')}
                              </p>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              {report.rows.length > 40 && (
                <p className="px-3.5 pt-1.5 text-[9px] text-muted">
                  Menampilkan 40 dari {formatNumber(report.rows.length)} baris. Ekspor Excel memuat seluruh data.
                </p>
              )}
            </Card>

            <Card className="mt-3">
              <SectionTitle title="Unduh Laporan" subtitle="PDF dengan kop, Excel dengan lembar informasi, CSV untuk analisis" icon={<Download size={15} />} />
              <div className="space-y-2">
                <Button className="w-full" onClick={() => download('pdf')}>
                  <FileText size={15} /> Unduh PDF
                </Button>
                <div className="grid grid-cols-2 gap-2">
                  <Button variant="outline" onClick={() => download('xlsx')}>
                    <FileSpreadsheet size={14} /> Excel
                  </Button>
                  <Button variant="outline" onClick={() => download('csv')}>
                    <FileText size={14} /> CSV
                  </Button>
                </div>
              </div>
            </Card>

            <div className="mt-3 rounded-[11px] border border-[#F3E3C3] bg-[#FEF9EF] px-3 py-2.5">
              <p className="text-[9.5px] leading-relaxed text-[#8A6A28]">{report.notes}</p>
            </div>
          </>
        ) : null}
      </main>
    </AppShell>
  )
}
