import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
import { CheckCircle2, Info, TriangleAlert, X } from 'lucide-react'
import { cn } from '../utils'

type ToastTone = 'success' | 'error' | 'info' | 'warning'

interface ToastItem {
  id: number
  message: string
  tone: ToastTone
}

interface ToastValue {
  toast: (message: string, tone?: ToastTone) => void
}

const ToastContext = createContext<ToastValue | null>(null)

const icons = {
  success: CheckCircle2,
  error: TriangleAlert,
  warning: TriangleAlert,
  info: Info,
}

const tones: Record<ToastTone, string> = {
  success: 'bg-[#0F2F2A] text-white',
  error: 'bg-[#3A1D1D] text-white',
  warning: 'bg-[#3A2E17] text-white',
  info: 'bg-[#17303E] text-white',
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])

  const remove = useCallback((id: number) => {
    setItems((current) => current.filter((item) => item.id !== id))
  }, [])

  const toast = useCallback((message: string, tone: ToastTone = 'success') => {
    const id = Date.now() + Math.random()
    setItems((current) => [...current, { id, message, tone }])
    window.setTimeout(() => remove(id), 3800)
  }, [remove])

  const value = useMemo(() => ({ toast }), [toast])

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 top-3 z-[80] flex justify-center px-4">
        <div className="w-full max-w-[440px] space-y-2">
          {items.map((item) => {
            const Icon = icons[item.tone]
            return (
              <div
                key={item.id}
                className={cn(
                  'pointer-events-auto flex items-start gap-2.5 rounded-xl px-3.5 py-3 text-[12.5px] shadow-float animate-fade-up',
                  tones[item.tone],
                )}
              >
                <Icon size={17} className="mt-0.5 shrink-0" />
                <p className="flex-1 leading-snug">{item.message}</p>
                <button onClick={() => remove(item.id)} aria-label="Tutup" className="opacity-60 hover:opacity-100">
                  <X size={15} />
                </button>
              </div>
            )
          })}
        </div>
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast harus dipakai di dalam ToastProvider')
  return context
}
