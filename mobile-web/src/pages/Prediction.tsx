import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ArrowRight,
  Download,
  FlaskConical,
  Gauge,
  Info,
  Play,
  Sparkles,
  Star,
  TrendingUp,
} from 'lucide-react'
import { api } from '../services/api'
import type { PredictionResult } from '../types'
import { PageHeader, AppShell } from '../components/Layout'
import { BacktestChart, ForecastChart } from '../components/charts'
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Field,
  SectionTitle,
  Select,
  Skeleton,
  Spinner,
} from '../components/ui'
import { cn, formatDate, formatNumber, formatPercent } from '../utils'

interface PredictionOption {
  id: number
  name: string
  code: string
  unit: string
  is_priority: boolean
  sales_days: number
  last_prediction: string | null
}

interface ComparisonRow {
  medicine_id: number
  model_name: string
  model_label: string
  mae: number
  rmse: number
  mape: number | null
  wape: number | null
  accuracy_indikatif: number | null
  test_size: number
}

const MODELS = [
  { value: 'auto', label: 'Otomatis (WAPE terkecil)' },
  { value: 'random_forest', label: 'Random Forest' },
  { value: 'decision_tree', label: 'Decision Tree' },
  { value: 'linear_regression', label: 'Linear Regression' },
]

const HORIZONS = [1, 2, 4, 8, 12]

export default function Prediction() {
  const initialMedicine = Number(new URLSearchParams(window.location.hash.split('?')[1] || '').get('medicine')) || null
  const [options, setOptions] = useState<PredictionOption[]>([])
  const [medicineId, setMedicineId] = useState<number | null>(initialMedicine)
  const [modelName, setModelName] = useState('auto')
  const [horizon, setHorizon] = useState(4)
  const [result, setResult] = useState<PredictionResult | null>(null)
  const [comparison, setComparison] = useState<ComparisonRow[]>([])
  const [loadingOptions, setLoadingOptions] = useState(true)
  const [loadingResult, setLoadingResult] = useState(false)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoadingOptions(true)
    api
      .get<PredictionOption[]>('/predictions/options')
      .then((rows) => {
        if (cancelled) return
        setOptions(rows)
        setMedicineId((current) => current ?? rows[0]?.id ?? null)
      })
      .catch((reason) => !cancelled && setError(reason instanceof Error ? reason.message : 'Gagal memuat daftar obat.'))
      .finally(() => !cancelled && setLoadingOptions(false))
    return () => {
      cancelled = true
    }
  }, [])

  const loadLatest = useCallback(async (id: number) => {
    setLoadingResult(true)
    setError('')
    try {
      const payload = await api.get<{ available: boolean } & PredictionResult>(`/predictions/latest?medicine_id=${id}`)
      if (payload.available) {
        setResult(payload)
        const requested = payload.params?.requested_model
        setModelName(typeof requested === 'string' ? requested : 'auto')
        setHorizon(payload.horizon_weeks)
      } else {
        setResult(null)
      }
      const rows = await api.get<ComparisonRow[]>(`/predictions/comparison?medicine_id=${id}`)
      setComparison(rows)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Gagal memuat prediksi terbaru.')
    } finally {
      setLoadingResult(false)
    }
  }, [])

  useEffect(() => {
    if (medicineId) loadLatest(medicineId)
  }, [medicineId, loadLatest])

  const run = async () => {
    if (!medicineId) return
    setRunning(true)
    setError('')
    setNotice('')
    try {
      const payload = await api.post<PredictionResult>('/predictions/run', {
        medicine_id: medicineId,
        model_name: modelName,
        horizon_weeks: horizon,
        start_date: null,
        save: true,
      })
      setResult(payload)
      setNotice(`Prediksi ${payload.medicine.name} berhasil dihitung dengan ${payload.model_label}.`)
      const rows = await api.get<ComparisonRow[]>(`/predictions/comparison?medicine_id=${medicineId}`)
      setComparison(rows)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Prediksi gagal dijalankan.')
    } finally {
      setRunning(false)
    }
  }

  const medicine = options.find((item) => item.id === medicineId)
  const metrics = result?.metrics?.[result.model_name]
  const total = useMemo(
    () => (result ? result.forecast.reduce((sum, item) => sum + item.predicted, 0) : 0),
    [result],
  )
  const maxImportance = Math.max(...(result?.feature_importance.slice(0, 7).map((item) => item.importance) || [0.001]))
  const bestModel = comparison.reduce<string | null>((best, row) => {
    if (row.wape === null) return best
    if (!best) return row.model_name
    const current = comparison.find((item) => item.model_name === best)
    return current && current.wape !== null && row.wape < current.wape ? row.model_name : best
  }, null)

  const exportResult = (format: 'pdf' | 'xlsx' | 'csv') => {
    if (!result) return
    const extension = format
    api
      .download(`/predictions/${result.run_id}/export?fmt=${format}`, `Prediksi_${result.medicine.code}.${extension}`)
      .catch((reason) => setError(reason instanceof Error ? reason.message : 'Unduhan gagal.'))
  }

  return (
    <AppShell active="prediction">
      <PageHeader title="Prediksi Permintaan" subtitle={result?.model_label || 'Analitik prediksi permintaan'} />
      <main className="px-4 pt-3">
        <Card>
          <SectionTitle
            title="Jalankan Prediksi"
            subtitle="Pilih obat, algoritma, dan horizon prakiraan"
            icon={<FlaskConical size={16} />}
          />
          {loadingOptions ? (
            <div className="space-y-2">
              <Skeleton className="h-11" />
              <Skeleton className="h-11" />
            </div>
          ) : (
            <div className="space-y-2.5">
              <Field label="Obat">
                <Select value={medicineId ?? ''} onChange={(event) => setMedicineId(Number(event.target.value))}>
                  {options.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.is_priority ? '★ ' : ''}
                      {option.name} ({option.code})
                    </option>
                  ))}
                </Select>
              </Field>
              <div className="grid grid-cols-2 gap-2.5">
                <Field label="Algoritma">
                  <Select value={modelName} onChange={(event) => setModelName(event.target.value)}>
                    {MODELS.map((model) => (
                      <option key={model.value} value={model.value}>
                        {model.label}
                      </option>
                    ))}
                  </Select>
                </Field>
                <Field label="Horizon">
                  <Select value={horizon} onChange={(event) => setHorizon(Number(event.target.value))}>
                    {HORIZONS.map((value) => (
                      <option key={value} value={value}>
                        {value} pekan
                      </option>
                    ))}
                  </Select>
                </Field>
              </div>
              {medicine && (
                <p className="rounded-[9px] bg-[#F5F8FA] px-2.5 py-1.5 text-[9.5px] leading-relaxed text-muted">
                  {formatNumber(medicine.sales_days)} hari data permintaan tercatat. Data uji dipisahkan secara kronologis
                  (tanpa pengacakan) agar evaluasi mencerminkan kondisi nyata.
                </p>
              )}
              <Button className="w-full" onClick={run} loading={running} disabled={!medicineId}>
                <Play size={15} /> {running ? 'Menghitung model...' : 'Jalankan Prediksi'}
              </Button>
            </div>
          )}
        </Card>

        {error && (
          <div className="mt-3">
            <ErrorState message={error} onRetry={() => medicineId && loadLatest(medicineId)} />
          </div>
        )}
        {notice && (
          <div className="mt-3 flex items-start gap-2 rounded-[11px] border border-[#CFEDE2] bg-[#F4FBF8] px-3 py-2.5">
            <Sparkles size={13} className="mt-0.5 shrink-0 text-success" />
            <p className="text-[10.5px] leading-relaxed text-[#3E6B62]">{notice}</p>
          </div>
        )}

        {loadingResult ? (
          <div className="mt-3 space-y-3">
            <Skeleton className="h-[190px] rounded-card" />
            <Skeleton className="h-[190px] rounded-card" />
          </div>
        ) : result ? (
          <>
            <Card className="mt-3 overflow-hidden !p-0">
              <div className="bg-gradient-to-br from-[#0B5F52] via-[#087F6B] to-[#20B58A] px-4 py-4 text-white">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="truncate text-[13px] font-bold">{result.medicine.name}</p>
                    <p className="mt-0.5 text-[9.5px] text-white/70">
                      {result.medicine.code} · {result.medicine.category}
                    </p>
                  </div>
                  <Badge className="border border-white/25 bg-white/15 !text-white" tone="neutral">
                    {result.model_label}
                  </Badge>
                </div>
                <p className="mt-3 text-[9.5px] font-medium uppercase tracking-[0.12em] text-white/65">
                  Total prakiraan {result.horizon_weeks} pekan
                </p>
                <div className="flex items-end gap-1.5">
                  <p className="text-[30px] font-extrabold leading-none tracking-[-0.03em]">{formatNumber(total)}</p>
                  <p className="mb-0.5 text-[11px] text-white/75">{result.medicine.unit.toLowerCase()}</p>
                </div>
                <p className="mt-1.5 text-[9px] text-white/55">
                  {formatDate(result.start_date)} · dilatih {formatDate(result.train_start)}–{formatDate(result.train_end)}
                </p>
              </div>
              <div className="grid grid-cols-3 divide-x divide-line bg-white">
                {[
                  { label: 'MAE', value: metrics ? formatNumber(metrics.mae, 2) : '—' },
                  { label: 'RMSE', value: metrics ? formatNumber(metrics.rmse, 2) : '—' },
                  { label: 'WAPE', value: metrics ? formatPercent(metrics.wape, 2) : '—' },
                ].map((item) => (
                  <div key={item.label} className="px-2 py-2.5 text-center">
                    <p className="text-[9px] font-semibold uppercase tracking-wide text-muted">{item.label}</p>
                    <p className="mt-0.5 text-[12.5px] font-bold text-ink">{item.value}</p>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="mt-3">
              <SectionTitle
                title="Prakiraan per Pekan"
                subtitle="Garis putus-putus menunjukkan batas ketidakpastian"
                icon={<TrendingUp size={16} />}
              />
              <ForecastChart
                points={result.forecast.map((item) => ({
                  label: formatDate(item.date, { day: '2-digit', month: 'short' }),
                  predicted: item.predicted,
                  lower: item.lower_bound,
                  upper: item.upper_bound,
                }))}
              />
              <div className="mt-2 grid grid-cols-2 gap-1.5">
                {result.forecast.map((item) => (
                  <div key={item.week_number} className="flex items-center justify-between rounded-[8px] bg-[#F8FBFC] px-2.5 py-1.5">
                    <span className="text-[9.5px] text-muted">{formatDate(item.date, { day: '2-digit', month: 'short' })}</span>
                    <span className="text-[10.5px] font-bold text-ink">{formatNumber(item.predicted)}</span>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="mt-3">
              <SectionTitle
                title="Evaluasi pada Data Uji"
                subtitle={`${formatNumber(result.test_size || 0)} pekan pengujian kronologis`}
                icon={<Gauge size={16} />}
              />
              <BacktestChart data={result.backtest} />
              <div className="mt-2 flex items-center gap-3 text-[9px] font-medium text-muted">
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" /> Aktual
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-warning" /> Prediksi
                </span>
                {metrics && metrics.mape_zero_actual > 0 && (
                  <span className="ml-auto text-[8.5px]">WAPE membandingkan total selisih dengan total permintaan</span>
                )}
              </div>
            </Card>

            <Card className="mt-3">
              <SectionTitle
                title="Perbandingan Algoritma"
                subtitle="Semakin kecil MAE dan WAPE, semakin baik"
                icon={<Star size={16} />}
              />
              <div className="overflow-hidden rounded-[10px] border border-line">
                <table className="w-full text-[10px]">
                  <thead className="bg-[#F5F8FA] text-[8.5px] uppercase tracking-wide text-muted">
                    <tr>
                      <th className="px-2 py-2 text-left font-semibold">Model</th>
                      <th className="px-2 py-2 text-right font-semibold">MAE</th>
                      <th className="px-2 py-2 text-right font-semibold">WAPE</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {comparison.map((row) => (
                      <tr key={row.model_name} className={cn(row.model_name === result.model_name && 'bg-[#F4FBF8]')}>
                        <td className="px-2 py-2">
                          <span className="flex items-center gap-1.5 font-medium text-ink">
                            {row.model_label}
                            {bestModel === row.model_name && (
                              <span className="rounded-full bg-[#E8F7F0] px-1.5 py-0.5 text-[7.5px] font-bold text-[#0E8A5F]">
                                TERBAIK
                              </span>
                            )}
                          </span>
                        </td>
                        <td className="px-2 py-2 text-right text-muted">{formatNumber(row.mae, 2)}</td>
                        <td className="px-2 py-2 text-right font-semibold text-ink">{formatPercent(row.wape, 1)}</td>
                      </tr>
                    ))}
                    {comparison.length === 0 && (
                      <tr>
                        <td colSpan={3} className="px-2 py-4 text-center text-muted">Belum ada data evaluasi.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </Card>

            {result.feature_importance.length > 0 && (
              <Card className="mt-3">
                <SectionTitle
                  title="Faktor Paling Berpengaruh"
                  subtitle={`Feature importance ${result.model_label}`}
                  icon={<Info size={16} />}
                />
                <div className="space-y-2">
                  {result.feature_importance.slice(0, 7).map((item) => (
                    <div key={item.feature}>
                      <div className="mb-0.5 flex items-center justify-between gap-2">
                        <span className="truncate text-[10px] text-ink">{item.label || item.feature}</span>
                        <span className="text-[9px] font-semibold text-muted">{formatPercent(item.importance * 100, 1)}</span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-[#EDF2F5]">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-primary to-accent"
                          style={{ width: `${Math.max(4, (item.importance / maxImportance) * 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            <Card className="mt-3">
              <SectionTitle title="Unduh Hasil" subtitle="PDF untuk laporan, Excel untuk analisis lanjutan" icon={<Download size={16} />} />
              <div className="grid grid-cols-3 gap-2">
                <Button variant="outline" size="sm" onClick={() => exportResult('pdf')}>PDF</Button>
                <Button variant="outline" size="sm" onClick={() => exportResult('xlsx')}>Excel</Button>
                <Button variant="outline" size="sm" onClick={() => exportResult('csv')}>CSV</Button>
              </div>
            </Card>

            <div className="mt-3 rounded-[11px] border border-[#F3E3C3] bg-[#FEF9EF] px-3 py-2.5">
              <p className="text-[9.5px] leading-relaxed text-[#8A6A28]">
                <b>Catatan:</b> prakiraan adalah estimasi model, bukan kepastian. WAPE dipakai sebagai ukuran
                kesalahan utama karena lebih stabil ketika permintaan mingguan rendah. Data aktual berasal dari stok
                opname dan pembelian Apotek Pahala; permintaan adalah estimasi, bukan transaksi kasir.
              </p>
            </div>
          </>
        ) : (
          <Card className="mt-3">
            <EmptyState
              icon={<Sparkles size={22} />}
              title="Belum ada prediksi"
              description="Pilih obat dan algoritma, lalu jalankan prediksi untuk melihat prakiraan permintaan."
              action={
                <Button size="sm" onClick={run} loading={running} disabled={!medicineId}>
                  <ArrowRight size={14} /> Prediksi sekarang
                </Button>
              }
            />
          </Card>
        )}

        {running && <Spinner label="Melatih model dan menyusun prakiraan..." />}
      </main>
    </AppShell>
  )
}
