import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Cpu,
  Database,
  HardDriveDownload,
  HardDriveUpload,
  LogOut,
  Moon,
  Save,
  ShieldCheck,
  Sun,
  Trash2,
  UserRound,
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
  Field,
  Input,
  SectionTitle,
  Select,
  Skeleton,
} from '../components/ui'
import { cn, formatDate, formatDateTime, formatNumber } from '../utils'

interface SettingsPayload {
  model: {
    primary_model: string
    n_estimators: number
    max_depth: number
    min_samples_leaf: number
    random_state: number
    test_ratio: number
    horizon_weeks: number
    weather_scenario: string
    n_jobs: number
  }
  procurement: {
    lead_time_days: number
    safety_stock_days: number
    review_period_days: number
    rounding_unit: number
    default_horizon_weeks: number
  }
  display: { theme: string; font_scale: string; user_theme: string; user_font_scale: string }
  database: {
    path: string
    relative_path: string
    size_label: string
    connected: boolean
    counts: { users: number; medicines: number; sales: number; weather_days: number; prediction_runs: number }
    last_modified: string | null
  }
  dataset: {
    dataset_label?: string
    dataset_type?: string
    sales_method?: string
    important_note?: string
    weather_source?: string
    period_start?: string
    period_end?: string
    medicine_count?: number
    sales_records?: number
  }
  backups: { name: string; size_label: string; created_at: string }[]
  app: { name: string; version: string; developer: string; technology: string[] }
  profile: { id: number; username: string; full_name: string; email: string | null; role: string }
}

export default function Settings() {
  const { user, logout, updateUser } = useAuth()
  const { toast } = useToast()
  const isAdmin = user?.role?.toLowerCase() === 'admin'
  const [data, setData] = useState<SettingsPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [profileForm, setProfileForm] = useState({ full_name: '', email: '' })
  const [savingProfile, setSavingProfile] = useState(false)
  const [modelForm, setModelForm] = useState<SettingsPayload['model'] | null>(null)
  const [procForm, setProcForm] = useState<SettingsPayload['procurement'] | null>(null)
  const [savingModel, setSavingModel] = useState(false)
  const [savingProc, setSavingProc] = useState(false)
  const [backingUp, setBackingUp] = useState(false)
  const [restoring, setRestoring] = useState(false)
  const [confirmRestore, setConfirmRestore] = useState(false)
  const [logoutOpen, setLogoutOpen] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const result = await api.get<SettingsPayload>('/settings')
      setData(result)
      setProfileForm({ full_name: result.profile.full_name, email: result.profile.email || '' })
      setModelForm(result.model)
      setProcForm(result.procurement)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Gagal memuat pengaturan.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const saveProfile = async () => {
    setSavingProfile(true)
    try {
      await api.put('/settings/profile', profileForm)
      updateUser({ full_name: profileForm.full_name, email: profileForm.email })
      toast('Profil berhasil diperbarui.', 'success')
    } catch (reason) {
      toast(reason instanceof Error ? reason.message : 'Gagal menyimpan profil.', 'error')
    } finally {
      setSavingProfile(false)
    }
  }

  const saveTheme = async (theme: string) => {
    try {
      await api.put('/settings/display', { theme })
      updateUser({ theme })
      toast(`Tema ${theme === 'dark' ? 'gelap' : theme === 'auto' ? 'otomatis' : 'terang'} diterapkan.`, 'success')
    } catch (reason) {
      toast(reason instanceof Error ? reason.message : 'Gagal menyimpan tema.', 'error')
    }
  }

  const saveModel = async () => {
    if (!modelForm) return
    setSavingModel(true)
    try {
      await api.put('/settings/model', modelForm)
      toast('Parameter model disimpan. Jalankan ulang pelatihan agar berlaku.', 'success')
    } catch (reason) {
      toast(reason instanceof Error ? reason.message : 'Gagal menyimpan parameter.', 'error')
    } finally {
      setSavingModel(false)
    }
  }

  const saveProcurement = async () => {
    if (!procForm) return
    setSavingProc(true)
    try {
      await api.put('/settings/procurement', procForm)
      toast('Asumsi pengadaan disimpan.', 'success')
    } catch (reason) {
      toast(reason instanceof Error ? reason.message : 'Gagal menyimpan asumsi.', 'error')
    } finally {
      setSavingProc(false)
    }
  }

  const backup = async () => {
    setBackingUp(true)
    try {
      const result = await api.post<{ message: string; file: string }>('/settings/database/backup')
      toast(result.message, 'success')
      await load()
    } catch (reason) {
      toast(reason instanceof Error ? reason.message : 'Backup gagal.', 'error')
    } finally {
      setBackingUp(false)
    }
  }

  const restore = async () => {
    const file = fileRef.current?.files?.[0]
    if (!file) {
      toast('Pilih berkas .db terlebih dahulu.', 'warning')
      return
    }
    if (!confirmRestore) {
      toast('Centang konfirmasi restore terlebih dahulu.', 'warning')
      return
    }
    setRestoring(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const result = await api.postForm<{ message: string }>('/settings/database/restore?confirm=true', formData)
      toast(result.message, 'success')
      window.setTimeout(() => logout(), 1200)
    } catch (reason) {
      toast(reason instanceof Error ? reason.message : 'Restore gagal.', 'error')
    } finally {
      setRestoring(false)
    }
  }

  return (
    <AppShell active="more">
      <PageHeader title="Pengaturan" subtitle="Profil, model, dan database" />
      <main className="px-4 pt-3">
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-[180px] rounded-card" />
            <Skeleton className="h-[160px] rounded-card" />
            <Skeleton className="h-[200px] rounded-card" />
          </div>
        ) : error || !data ? (
          <Card>
            <p className="py-4 text-center text-[11px] text-danger">{error || 'Pengaturan tidak tersedia.'}</p>
            <Button variant="outline" className="w-full" onClick={load}>Coba lagi</Button>
          </Card>
        ) : (
          <>
            <Card>
              <SectionTitle title="Profil" subtitle={`@${data.profile.username} · ${data.profile.role.charAt(0).toUpperCase() + data.profile.role.slice(1).toLowerCase()}`} icon={<UserRound size={15} />} />
              <div className="space-y-2.5">
                <Field label="Nama lengkap">
                  <Input
                    value={profileForm.full_name}
                    onChange={(event) => setProfileForm((current) => ({ ...current, full_name: event.target.value }))}
                  />
                </Field>
                <Field label="Email">
                  <Input
                    type="email"
                    value={profileForm.email}
                    onChange={(event) => setProfileForm((current) => ({ ...current, email: event.target.value }))}
                    placeholder="nama@apotekpahala.id"
                  />
                </Field>
                <Button className="w-full" size="sm" onClick={saveProfile} loading={savingProfile}>
                  <Save size={14} /> Simpan Profil
                </Button>
              </div>
            </Card>

            <Card className="mt-3">
              <SectionTitle title="Tampilan" subtitle="Preferensi tersimpan pada akun" icon={<Sun size={15} />} />
              <div className="grid grid-cols-3 gap-1.5">
                {[
                  { value: 'light', label: 'Terang', icon: Sun },
                  { value: 'dark', label: 'Gelap', icon: Moon },
                  { value: 'auto', label: 'Otomatis', icon: Cpu },
                ].map((item) => {
                  const Icon = item.icon
                  return (
                    <button
                      key={item.value}
                      onClick={() => saveTheme(item.value)}
                      className={cn(
                        'flex flex-col items-center gap-1 rounded-[10px] border px-2 py-2.5 text-[9.5px] font-semibold',
                        (user?.theme || 'light') === item.value
                          ? 'border-primary bg-[#F0FAF6] text-primary'
                          : 'border-line bg-white text-muted',
                      )}
                    >
                      <Icon size={15} />
                      {item.label}
                    </button>
                  )
                })}
              </div>
              <p className="mt-2 text-[9px] leading-relaxed text-muted">
                Mode otomatis mengikuti preferensi sistem perangkat. Tema juga berlaku pada aplikasi mobile ini.
              </p>
            </Card>

            {isAdmin && modelForm && (
              <Card className="mt-3">
                <SectionTitle title="Parameter Model" subtitle="Berlaku saat pelatihan berikutnya" icon={<Cpu size={15} />} />
                <div className="space-y-2.5">
                  <Field label="Model utama">
                    <Select
                      value={modelForm.primary_model}
                      onChange={(event) => setModelForm({ ...modelForm, primary_model: event.target.value })}
                    >
                      <option value="auto">Otomatis (WAPE terkecil)</option>
                      <option value="random_forest">Random Forest</option>
                      <option value="decision_tree">Decision Tree</option>
                      <option value="linear_regression">Linear Regression</option>
                    </Select>
                  </Field>
                  <div className="grid grid-cols-2 gap-2">
                    <Field label="Jumlah pohon">
                      <Input
                        type="number"
                        min={10}
                        max={1500}
                        value={modelForm.n_estimators}
                        onChange={(event) => setModelForm({ ...modelForm, n_estimators: Number(event.target.value) })}
                      />
                    </Field>
                    <Field label="Min sampel daun">
                      <Input
                        type="number"
                        min={1}
                        max={50}
                        value={modelForm.min_samples_leaf}
                        onChange={(event) => setModelForm({ ...modelForm, min_samples_leaf: Number(event.target.value) })}
                      />
                    </Field>
                    <Field label="Porsi data uji">
                      <Input
                        type="number"
                        min={0.1}
                        max={0.4}
                        step={0.05}
                        value={modelForm.test_ratio}
                        onChange={(event) => setModelForm({ ...modelForm, test_ratio: Number(event.target.value) })}
                      />
                    </Field>
                    <Field label="Horizon default">
                      <Select
                        value={modelForm.horizon_weeks}
                        onChange={(event) => setModelForm({ ...modelForm, horizon_weeks: Number(event.target.value) })}
                      >
                        {[1, 2, 4, 8, 12].map((value) => <option key={value} value={value}>{value} pekan</option>)}
                      </Select>
                    </Field>
                  </div>
                  <Button className="w-full" size="sm" onClick={saveModel} loading={savingModel}>
                    <Save size={14} /> Simpan Parameter Model
                  </Button>
                </div>
              </Card>
            )}

            {isAdmin && procForm && (
              <Card className="mt-3">
                <SectionTitle title="Asumsi Pengadaan" subtitle="Dipakai pada perhitungan rekomendasi" icon={<ShieldCheck size={15} />} />
                <div className="grid grid-cols-2 gap-2">
                  <Field label="Lead time (hari)">
                    <Input
                      type="number"
                      min={0}
                      value={procForm.lead_time_days}
                      onChange={(event) => setProcForm({ ...procForm, lead_time_days: Number(event.target.value) })}
                    />
                  </Field>
                  <Field label="Safety stock (hari)">
                    <Input
                      type="number"
                      min={0}
                      value={procForm.safety_stock_days}
                      onChange={(event) => setProcForm({ ...procForm, safety_stock_days: Number(event.target.value) })}
                    />
                  </Field>
                  <Field label="Pembulatan unit">
                    <Input
                      type="number"
                      min={1}
                      value={procForm.rounding_unit}
                      onChange={(event) => setProcForm({ ...procForm, rounding_unit: Number(event.target.value) })}
                    />
                  </Field>
                  <Field label="Horizon default">
                    <Select
                      value={procForm.default_horizon_weeks}
                      onChange={(event) => setProcForm({ ...procForm, default_horizon_weeks: Number(event.target.value) })}
                    >
                      {[1, 2, 4, 8, 12].map((value) => <option key={value} value={value}>{value} pekan</option>)}
                    </Select>
                  </Field>
                </div>
                <Button className="mt-2.5 w-full" size="sm" onClick={saveProcurement} loading={savingProc}>
                  <Save size={14} /> Simpan Asumsi
                </Button>
              </Card>
            )}

            <Card className="mt-3">
              <SectionTitle title="Database" subtitle="SQLite bersama desktop & mobile" icon={<Database size={15} />} />
              <div className="space-y-1.5">
                {[
                  { label: 'Ukuran', value: data.database.size_label },
                  { label: 'Pengguna', value: formatNumber(data.database.counts.users) },
                  { label: 'Obat', value: formatNumber(data.database.counts.medicines) },
                  { label: 'Data permintaan', value: formatNumber(data.database.counts.sales) },
                  { label: 'Hari cuaca', value: formatNumber(data.database.counts.weather_days) },
                  { label: 'Riwayat prediksi', value: formatNumber(data.database.counts.prediction_runs) },
                ].map((row) => (
                  <div key={row.label} className="flex items-center justify-between rounded-[8px] bg-[#F8FBFC] px-2.5 py-1.5">
                    <span className="text-[9.5px] text-muted">{row.label}</span>
                    <span className="text-[10px] font-semibold text-ink">{row.value}</span>
                  </div>
                ))}
              </div>
              <p className="mt-1.5 break-all text-[8.5px] text-[#9AA9B2]">{data.database.relative_path}</p>

              {isAdmin && (
                <>
                  <Button className="mt-2.5 w-full" size="sm" variant="outline" onClick={backup} loading={backingUp}>
                    <HardDriveDownload size={14} /> Buat Backup Database
                  </Button>
                  <div className="mt-2 rounded-[10px] border border-[#F6DADA] bg-[#FDF7F7] p-2.5">
                    <p className="flex items-center gap-1 text-[10px] font-semibold text-[#B63B3B]">
                      <HardDriveUpload size={12} /> Restore Database
                    </p>
                    <p className="mt-0.5 text-[8.5px] leading-relaxed text-[#9C5B5B]">
                      Menimpa seluruh data aktif. Backup otomatis dibuat sebelum restore.
                    </p>
                    <input ref={fileRef} type="file" accept=".db" className="mt-2 block w-full text-[9px] text-muted file:mr-2 file:rounded-lg file:border-0 file:bg-white file:px-2 file:py-1.5 file:text-[9px] file:font-semibold file:text-ink" />
                    <label className="mt-1.5 flex items-start gap-1.5 text-[8.5px] text-[#8A5B5B]">
                      <input
                        type="checkbox"
                        checked={confirmRestore}
                        onChange={(event) => setConfirmRestore(event.target.checked)}
                        className="mt-0.5 accent-[#E55353]"
                      />
                      Saya memahami data aktif akan diganti.
                    </label>
                    <Button variant="danger" size="sm" className="mt-2 w-full" onClick={restore} loading={restoring} disabled={!confirmRestore}>
                      <Trash2 size={13} /> Restore sekarang
                    </Button>
                  </div>
                </>
              )}

              {data.backups.length > 0 && (
                <div className="mt-2">
                  <p className="text-[9px] font-semibold text-muted">Backup tersedia</p>
                  <div className="mt-1 space-y-1">
                    {data.backups.slice(0, 4).map((item) => (
                      <div key={item.name} className="flex items-center justify-between gap-2 rounded-[8px] border border-line px-2 py-1.5">
                        <span className="truncate text-[8.5px] text-ink">{item.name}</span>
                        <span className="shrink-0 text-[8px] text-muted">{item.size_label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>

            <Card className="mt-3">
              <SectionTitle title="Sumber Data" icon={<Database size={15} />} />
              <div className="space-y-1.5">
                {[
                  { label: 'Jenis', value: data.dataset.dataset_type || 'Data aktual Apotek Pahala' },
                  { label: 'Periode', value: data.dataset.period_start && data.dataset.period_end
                    ? `${formatDate(data.dataset.period_start)} – ${formatDate(data.dataset.period_end)}`
                    : '2022–2026' },
                  { label: 'Jumlah obat', value: `${formatNumber(data.dataset.medicine_count || 0)} jenis` },
                  { label: 'Cuaca', value: data.dataset.weather_source || 'NASA POWER' },
                ].map((item) => (
                  <div key={item.label} className="flex items-start justify-between gap-3 rounded-[8px] bg-[#F8FBFC] px-2.5 py-1.5">
                    <span className="text-[10px] text-muted">{item.label}</span>
                    <span className="max-w-[65%] text-right text-[10px] font-semibold text-ink">{item.value}</span>
                  </div>
                ))}
              </div>
              <p className="mt-2 text-[8.5px] leading-relaxed text-[#9AA9B2]">
                {data.dataset.important_note || 'Permintaan dihitung dari stok opname dan pembelian, bukan transaksi kasir.'}
              </p>
            </Card>

            <Card className="mt-3">
              <SectionTitle title="Tentang" icon={<ShieldCheck size={15} />} />
              <p className="text-[10.5px] font-semibold text-ink">{data.app.name}</p>
              <p className="text-[9.5px] text-muted">Versi {data.app.version} · {data.app.developer}</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {data.app.technology.slice(0, 8).map((item) => (
                  <Badge key={item} tone="neutral">{item}</Badge>
                ))}
              </div>
              <p className="mt-2 text-[8.5px] leading-relaxed text-[#9AA9B2]">
                Data aktual Apotek Pahala berasal dari stok opname dan pembelian 2022–2026. Permintaan
                merupakan estimasi, bukan transaksi kasir; prakiraan tetap perlu ditinjau apoteker.
              </p>
            </Card>

            <Button variant="outline" className="mt-3 w-full !border-[#F6DADA] !text-danger" onClick={() => setLogoutOpen(true)}>
              <LogOut size={15} /> Keluar dari akun
            </Button>
            <p className="mt-2 pb-2 text-center text-[8.5px] text-[#9AA9B2]">
              Terakhir diubah {data.database.last_modified ? formatDateTime(data.database.last_modified) : '—'}
            </p>
          </>
        )}
      </main>

      <ConfirmDialog
        open={logoutOpen}
        onClose={() => setLogoutOpen(false)}
        onConfirm={logout}
        title="Keluar dari aplikasi?"
        message="Anda perlu masuk kembali untuk mengakses data apotek."
        confirmLabel="Ya, keluar"
        danger
      />
    </AppShell>
  )
}
