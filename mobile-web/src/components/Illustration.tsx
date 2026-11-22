import { cn } from '../utils'

/** Ilustrasi etalase apotek bergaya flat, dibuat khusus untuk Apotek Pahala. */
export function PharmacyIllustration({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 240 180" className={cn('h-auto w-full', className)} role="img" aria-label="Ilustrasi apotek">
      <ellipse cx="120" cy="164" rx="92" ry="9" fill="#0B4F45" opacity=".16" />
      {/* bangunan */}
      <rect x="34" y="44" width="172" height="112" rx="8" fill="#FFFFFF" />
      <rect x="34" y="44" width="172" height="112" rx="8" fill="none" stroke="#D8E7E2" strokeWidth="2" />
      {/* atap */}
      <path d="M24 44h192l-14-22a8 8 0 0 0-6.6-3.4H44.6A8 8 0 0 0 38 22L24 44Z" fill="#0B5F52" />
      <path d="M24 44h192l-3 9H27l-3-9Z" fill="#083F37" opacity=".55" />
      {/* kanopi bergaris */}
      <path d="M40 53h160v20H40z" fill="#EAF6F1" />
      {[0, 1, 2, 3, 4, 5, 6, 7].map((index) => (
        <path key={index} d={`M${44 + index * 20} 53h10v20H${44 + index * 20}z`} fill="#20B58A" opacity={0.9} />
      ))}
      <path d="M40 73h160l-7 16H47l-7-16Z" fill="#087F6B" />
      {/* jendela */}
      <rect x="52" y="96" width="58" height="44" rx="5" fill="#DDF1EA" stroke="#B9DED2" strokeWidth="1.5" />
      <rect x="58" y="102" width="46" height="27" rx="3" fill="#F7FCFA" />
      {/* rak obat dalam jendela */}
      {[0, 1, 2, 3].map((index) => (
        <rect key={index} x={62 + index * 11} y={106} width={7} height={19} rx={2} fill={index % 2 === 0 ? '#0B5F52' : '#F2A93B'} opacity={0.85} />
      ))}
      <rect x="56" y="132" width="50" height="3" rx="1.5" fill="#B9DED2" />
      {/* pintu */}
      <rect x="126" y="96" width="50" height="60" rx="5" fill="#0B5F52" />
      <rect x="131" y="101" width="40" height="50" rx="3" fill="#7FD3BC" opacity=".45" />
      <rect x="131" y="101" width="40" height="22" rx="3" fill="#DDF1EA" opacity=".7" />
      <circle cx="165" cy="127" r="2.6" fill="#F2A93B" />
      <path d="M140 132h22M140 138h22" stroke="#EAF6F1" strokeWidth="2" strokeLinecap="round" opacity=".65" />
      {/* papan salib */}
      <rect x="182" y="92" width="14" height="4" rx="2" fill="#0B5F52" opacity=".16" />
      <circle cx="188" cy="84" r="0" fill="#20B58A" />
      <g>
        <rect x="184" y="58" width="9" height="26" rx="3" fill="#0B5F52" />
        <rect x="175.5" y="66.5" width="26" height="9" rx="3" fill="#087F6B" />
      </g>
      {/* tanaman */}
      <path d="M30 150c-6-8-6-16 0-22 5 7 6 15 0 22Z" fill="#20B58A" />
      <path d="M38 150c7-6 8-14 3-19-5 5-7 12-3 19Z" fill="#16A36A" />
      <path d="M24 150h20l-3 12H27l-3-12Z" fill="#0B5F52" />
      {/* pot kanan */}
      <path d="M206 154h16l-2.5 10h-11L206 154Z" fill="#0B5F52" />
      <path d="M214 154c-5-5-5-12-1-17 4 5 5 12 1 17Z" fill="#20B58A" />
      {/* bintang */}
      <path d="M76 32l2.2 4.6 5 .7-3.6 3.5.9 5-4.5-2.4-4.5 2.4.9-5-3.6-3.5 5-.7L76 32Z" fill="#F2A93B" opacity=".9" />
      <circle cx="166" cy="30" r="3" fill="#7FD3BC" opacity=".8" />
      <circle cx="186" cy="22" r="2" fill="#F2A93B" opacity=".7" />
    </svg>
  )
}

/** Lambang apotek: palang hijau dengan daun mint. */
export function LogoMark({ size = 40, className }: { size?: number; className?: string }) {
  return (
    <img
      src="/logo.svg"
      width={size}
      height={size}
      alt="Apotek Pahala"
      className={cn('object-contain', className)}
      draggable={false}
    />
  )
}

/** Ornamen lingkaran dekoratif untuk header/login. */
export function HeaderOrnaments({ tone = 'light' }: { tone?: 'light' | 'dark' }) {
  const color = tone === 'light' ? '#FFFFFF' : '#20B58A'
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute -right-10 -top-14 h-40 w-40 rounded-full border" style={{ borderColor: `${color}1f` }} />
      <div className="absolute -right-2 -top-6 h-24 w-24 rounded-full" style={{ background: `${color}0d` }} />
      <div className="absolute -bottom-16 -left-10 h-40 w-40 rounded-full" style={{ background: `${color}0a` }} />
      <div className="absolute bottom-6 left-1/2 h-1 w-1 rounded-full" style={{ background: `${color}30` }} />
      <div className="absolute left-8 top-1/3 h-1.5 w-1.5 rounded-full" style={{ background: `${color}26` }} />
    </div>
  )
}
