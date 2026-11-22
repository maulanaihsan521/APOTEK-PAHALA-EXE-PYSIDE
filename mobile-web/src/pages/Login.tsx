import { useState } from 'react'
import { Eye, EyeOff, Loader2, LockKeyhole, ShieldCheck, UserRound } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { navigate } from '../router'
import { PharmacyIllustration, HeaderOrnaments } from '../components/Illustration'
import { Badge, Button } from '../components/ui'

const defaultAccounts = [
  { label: 'Admin', username: 'admin', password: 'admin123' },
  { label: 'Petugas', username: 'petugas', password: 'petugas123' },
]

export default function Login() {
  const { login } = useAuth()
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [visible, setVisible] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate('/')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Gagal masuk. Periksa koneksi Anda.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="phone-shell relative flex min-h-dvh flex-col overflow-hidden bg-gradient-to-br from-[#0B5F52] via-[#087F6B] to-[#149C80]">
      <HeaderOrnaments />
      <div className="relative flex flex-1 flex-col px-5 pb-6 pt-8">
        <div className="mx-auto w-full max-w-[280px]">
          <PharmacyIllustration className="drop-shadow-[0_18px_30px_rgba(3,40,34,.28)]" />
        </div>

        <div className="mt-1 text-center text-white">
          <h1 className="text-[24px] font-extrabold tracking-[-0.02em]">Apotek Pahala</h1>
          <p className="mt-1 text-[11px] font-medium uppercase tracking-[0.22em] text-white/70">
            Pharmacy Intelligence
          </p>
        </div>

        <div className="mt-6 rounded-[24px] bg-white p-5 shadow-[0_24px_50px_rgba(3,40,34,.24)]">
          <div className="mb-4">
            <h2 className="text-[16px] font-bold text-ink">Masuk ke akun Anda</h2>
            <p className="mt-0.5 text-[11px] text-muted">
              Kelola prediksi permintaan dan persediaan obat dalam satu tempat.
            </p>
          </div>

          <form onSubmit={submit} className="space-y-3">
            <label className="block">
              <span className="mb-1.5 block text-[11.5px] font-semibold text-ink">Nama pengguna</span>
              <div className="relative">
                <UserRound size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  autoComplete="username"
                  autoCapitalize="none"
                  spellCheck={false}
                  required
                  placeholder="admin"
                  className="h-11 w-full rounded-[11px] border border-line bg-[#F8FBFC] pl-9 pr-3 text-[13px] text-ink placeholder:text-[#A6B4BC] focus:border-primary focus:bg-white focus:ring-2 focus:ring-primary/10"
                />
              </div>
            </label>

            <label className="block">
              <span className="mb-1.5 block text-[11.5px] font-semibold text-ink">Password</span>
              <div className="relative">
                <LockKeyhole size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  type={visible ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  placeholder="••••••••"
                  className="h-11 w-full rounded-[11px] border border-line bg-[#F8FBFC] pl-9 pr-10 text-[13px] text-ink placeholder:text-[#A6B4BC] focus:border-primary focus:bg-white focus:ring-2 focus:ring-primary/10"
                />
                <button
                  type="button"
                  onClick={() => setVisible((value) => !value)}
                  aria-label={visible ? 'Sembunyikan password' : 'Tampilkan password'}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full p-1.5 text-muted hover:bg-slate-100"
                >
                  {visible ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </label>

            {error && (
              <div className="rounded-[10px] border border-[#F6DADA] bg-[#FDF3F3] px-3 py-2 text-[11px] text-[#B63B3B]">
                {error}
              </div>
            )}

            <Button type="submit" size="lg" className="w-full" loading={loading}>
              {loading ? 'Memeriksa...' : 'Masuk'}
            </Button>
          </form>

          <div className="mt-4 rounded-[12px] bg-[#F5F8FA] p-2.5">
            <div className="mb-1.5 flex items-center gap-1.5 text-[10px] font-semibold text-muted">
              <ShieldCheck size={12} className="text-primary" />
              Akun bawaan · ganti kata sandi setelah login
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {defaultAccounts.map((account) => (
                <button
                  key={account.username}
                  type="button"
                  onClick={() => {
                    setUsername(account.username)
                    setPassword(account.password)
                    setError('')
                  }}
                  className="flex flex-col items-start rounded-[9px] border border-line bg-white px-2.5 py-1.5 text-left transition hover:border-primary/40 hover:bg-[#F0FAF6]"
                >
                  <span className="text-[10.5px] font-semibold text-ink">{account.label}</span>
                  <span className="text-[9.5px] text-muted">{account.username} / {account.password}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-auto flex flex-col items-center gap-1.5 pt-5 text-center">
          <Badge className="border border-white/20 bg-white/10 !text-white" tone="neutral">
            Data aktual Apotek Pahala
          </Badge>
          <p className="text-[9.5px] text-white/55">Apotek Pahala v1.0.0 · Universitas · 2026</p>
        </div>
      </div>

      {loading && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-[#04211C]/10">
          <Loader2 size={22} className="animate-spin text-white" />
        </div>
      )}
    </div>
  )
}
