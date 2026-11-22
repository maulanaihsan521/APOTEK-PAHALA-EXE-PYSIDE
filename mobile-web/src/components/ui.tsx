import {
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
  useEffect,
} from 'react'
import { Loader2, Search, X } from 'lucide-react'
import { cn, statusLabel, statusTone } from '../utils'

/* ---------------------------------- Button --------------------------------- */
type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'soft'
type ButtonSize = 'sm' | 'md' | 'lg'

const buttonVariants: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-white hover:bg-secondary active:scale-[.99] shadow-[0_6px_16px_rgba(8,127,107,.20)]',
  secondary: 'bg-secondary text-white hover:bg-[#0a5147]',
  outline: 'border border-line bg-white text-ink hover:bg-slate-50',
  ghost: 'text-muted hover:bg-slate-50 hover:text-ink',
  danger: 'bg-danger text-white hover:bg-[#cf4646]',
  soft: 'bg-[#E7F6F0] text-secondary hover:bg-[#DCF1E8]',
}

const buttonSizes: Record<ButtonSize, string> = {
  sm: 'h-9 px-3 text-[12px] rounded-[10px] gap-1.5',
  md: 'h-11 px-4 text-[13px] rounded-[11px] gap-2',
  lg: 'h-12 px-5 text-[13.5px] rounded-[12px] gap-2',
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  className,
  children,
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
}) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center font-semibold transition disabled:cursor-not-allowed disabled:opacity-55',
        buttonVariants[variant],
        buttonSizes[size],
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 size={16} className="animate-spin" />}
      {children}
    </button>
  )
}

export function IconButton({
  label,
  className,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return (
    <button
      aria-label={label}
      className={cn(
        'flex h-9 w-9 items-center justify-center rounded-full text-muted transition hover:bg-slate-100 active:scale-95',
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}

/* ----------------------------------- Card ---------------------------------- */
export function Card({
  className,
  children,
  onClick,
}: {
  className?: string
  children: ReactNode
  onClick?: () => void
}) {
  return (
    <div
      onClick={onClick}
      className={cn('rounded-card border border-line bg-white p-3.5 shadow-card', onClick && 'cursor-pointer', className)}
    >
      {children}
    </div>
  )
}

export function SectionTitle({
  icon,
  title,
  action,
  subtitle,
}: {
  icon?: ReactNode
  title: string
  action?: ReactNode
  subtitle?: string
}) {
  return (
    <div className="mb-3 flex items-start justify-between gap-3">
      <div className="flex min-w-0 items-center gap-2">
        {icon && <span className="text-primary">{icon}</span>}
        <div>
          <h2 className="text-[14px] font-bold leading-tight text-ink">{title}</h2>
          {subtitle && <p className="mt-0.5 text-[11px] text-muted">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
  )
}

/* ---------------------------------- Badge ---------------------------------- */
type Tone = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'primary'

const badgeTones: Record<Tone, string> = {
  success: 'bg-[#E8F7F0] text-[#0E8A5F]',
  warning: 'bg-[#FEF4E2] text-[#B47A16]',
  danger: 'bg-[#FDECEC] text-[#D14343]',
  info: 'bg-[#EAF3FC] text-[#2F73B9]',
  neutral: 'bg-slate-100 text-muted',
  primary: 'bg-[#E7F6F0] text-secondary',
}

export function Badge({
  tone = 'neutral',
  children,
  className,
  dot = false,
}: {
  tone?: Tone
  children: ReactNode
  className?: string
  dot?: boolean
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold leading-5',
        badgeTones[tone],
        className,
      )}
    >
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  )
}

export function StockBadge({ status }: { status: string }) {
  return <Badge tone={statusTone(status) as Tone}>{statusLabel(status)}</Badge>
}

/* -------------------------------- Form field ------------------------------- */
export function Field({
  label,
  hint,
  error,
  children,
  className,
  required,
}: {
  label?: string
  hint?: string
  error?: string
  children: ReactNode
  className?: string
  required?: boolean
}) {
  return (
    <label className={cn('block', className)}>
      {label && (
        <span className="mb-1.5 block text-[11.5px] font-semibold text-ink">
          {label} {required && <span className="text-danger">*</span>}
        </span>
      )}
      {children}
      {error ? (
        <span className="mt-1 block text-[10.5px] text-danger">{error}</span>
      ) : hint ? (
        <span className="mt-1 block text-[10.5px] text-muted">{hint}</span>
      ) : null}
    </label>
  )
}

export function Input({
  className,
  icon,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { icon?: ReactNode }) {
  return (
    <span className="relative block">
      {icon && (
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted">
          {icon}
        </span>
      )}
      <input
        className={cn(
          'h-11 w-full rounded-[11px] border border-line bg-[#F8FBFC] px-3 text-[13px] text-ink placeholder:text-[#9AA9B2] focus:border-primary focus:bg-white focus:ring-2 focus:ring-primary/10',
          icon ? 'pl-9' : undefined,
          className,
        )}
        {...props}
      />
    </span>
  )
}

export function SearchInput({
  value,
  onChange,
  placeholder,
}: {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}) {
  return (
    <div className="relative">
      <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder || 'Cari...'}
        className="h-11 w-full rounded-[11px] border border-line bg-white pl-9 pr-9 text-[12.5px] text-ink shadow-card placeholder:text-[#9AA9B2] focus:border-primary focus:ring-2 focus:ring-primary/10"
      />
      {value && (
        <button
          onClick={() => onChange('')}
          aria-label="Hapus pencarian"
          className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-full p-1 text-muted hover:bg-slate-100"
        >
          <X size={14} />
        </button>
      )}
    </div>
  )
}

export function Select({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        'h-11 w-full appearance-none rounded-[11px] border border-line bg-[#F8FBFC] px-3 pr-8 text-[13px] text-ink focus:border-primary focus:bg-white focus:ring-2 focus:ring-primary/10',
        className,
      )}
      style={{
        backgroundImage:
          "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='none' stroke='%23718096' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m4 6 4 4 4-4'/%3E%3C/svg%3E\")",
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'right 10px center',
      }}
      {...props}
    >
      {children}
    </select>
  )
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        'w-full rounded-[11px] border border-line bg-[#F8FBFC] p-3 text-[13px] text-ink placeholder:text-[#9AA9B2] focus:border-primary focus:bg-white focus:ring-2 focus:ring-primary/10',
        className,
      )}
      {...props}
    />
  )
}

/* ---------------------------------- Modal ---------------------------------- */
export function Modal({
  open,
  onClose,
  title,
  subtitle,
  children,
  footer,
  size = 'md',
}: {
  open: boolean
  onClose: () => void
  title: string
  subtitle?: string
  children: ReactNode
  footer?: ReactNode
  size?: 'md' | 'lg'
}) {
  useEffect(() => {
    if (!open) return
    const handler = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handler)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="fixed inset-0 z-[70] flex items-end justify-center sm:items-center" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-[#08231E]/45 backdrop-blur-[2px]" onClick={onClose} />
      <div
        className={cn(
          'relative flex max-h-[90vh] w-full flex-col overflow-hidden rounded-t-[24px] bg-white shadow-float animate-fade-up sm:rounded-[22px]',
          size === 'md' ? 'max-w-[480px]' : 'max-w-[620px]',
        )}
      >
        <div className="flex items-start justify-between gap-3 border-b border-line px-4 pb-3 pt-3">
          <div className="min-w-0">
            <h3 className="text-[15px] font-bold text-ink">{title}</h3>
            {subtitle && <p className="mt-0.5 text-[11.5px] text-muted">{subtitle}</p>}
          </div>
          <IconButton label="Tutup" onClick={onClose}>
            <X size={18} />
          </IconButton>
        </div>
        <div className="flex-1 overflow-y-auto px-4 py-4">{children}</div>
        {footer && <div className="border-t border-line bg-[#F8FBFC] px-4 py-3">{footer}</div>}
      </div>
    </div>
  )
}

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Ya, lanjutkan',
  danger = false,
  loading = false,
}: {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmLabel?: string
  danger?: boolean
  loading?: boolean
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      footer={
        <div className="flex gap-2">
          <Button variant="outline" className="flex-1" onClick={onClose} disabled={loading}>
            Batal
          </Button>
          <Button variant={danger ? 'danger' : 'primary'} className="flex-1" onClick={onConfirm} loading={loading}>
            {confirmLabel}
          </Button>
        </div>
      }
    >
      <p className="text-[12.5px] leading-relaxed text-muted">{message}</p>
    </Modal>
  )
}

/* -------------------------------- Feedback -------------------------------- */
export function EmptyState({
  icon,
  title,
  description,
  action,
  compact = false,
}: {
  icon: ReactNode
  title: string
  description?: string
  action?: ReactNode
  compact?: boolean
}) {
  return (
    <div className={cn('flex flex-col items-center justify-center px-4 text-center', compact ? 'py-6' : 'py-10')}>
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#EAF6F1] text-primary">
        {icon}
      </div>
      <p className="text-[13px] font-semibold text-ink">{title}</p>
      {description && <p className="mt-1 max-w-[280px] text-[11.5px] leading-relaxed text-muted">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('skeleton animate-pulse-soft rounded-lg bg-[#E8EFF2]', className)} />
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-10 text-muted">
      <Loader2 size={22} className="animate-spin text-primary" />
      {label && <span className="text-[11.5px]">{label}</span>}
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-[14px] border border-[#F6DADA] bg-[#FDF3F3] px-4 py-5 text-center">
      <p className="text-[12.5px] font-semibold text-[#B63B3B]">Terjadi kendala</p>
      <p className="mt-1 text-[11.5px] leading-relaxed text-[#9C5B5B]">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-3 rounded-lg bg-white px-3 py-1.5 text-[11.5px] font-semibold text-danger shadow-sm">
          Coba lagi
        </button>
      )}
    </div>
  )
}

/* -------------------------------- Controls -------------------------------- */
export function Segmented<T extends string | number>({
  value,
  options,
  onChange,
  className,
}: {
  value: T
  options: { value: T; label: string }[]
  onChange: (value: T) => void
  className?: string
}) {
  return (
    <div className={cn('inline-flex items-center rounded-full bg-[#EEF3F5] p-0.5', className)}>
      {options.map((option) => (
        <button
          key={String(option.value)}
          onClick={() => onChange(option.value)}
          className={cn(
            'rounded-full px-3 py-1.5 text-[10.5px] font-semibold transition',
            value === option.value ? 'bg-primary text-white shadow-sm' : 'text-muted hover:text-ink',
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}

export function StatusDot({ tone = 'success' }: { tone?: Tone }) {
  const colors: Record<Tone, string> = {
    success: 'bg-success',
    warning: 'bg-warning',
    danger: 'bg-danger',
    info: 'bg-info',
    neutral: 'bg-muted',
    primary: 'bg-primary',
  }
  return <span className={cn('inline-block h-2 w-2 rounded-full', colors[tone])} />
}

export function Divider({ className }: { className?: string }) {
  return <div className={cn('h-px w-full bg-line', className)} />
}
