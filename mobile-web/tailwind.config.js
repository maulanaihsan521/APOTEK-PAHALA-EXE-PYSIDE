/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#087F6B',
        secondary: '#0B5F52',
        accent: '#20B58A',
        canvas: '#F5F8FA',
        surface: '#FFFFFF',
        ink: '#18343D',
        muted: '#718096',
        line: '#E3EBEF',
        success: '#16A36A',
        warning: '#F2A93B',
        danger: '#E55353',
        info: '#3985D6',
        sidebar: '#0B4F45',
      },
      fontFamily: {
        sans: ['Inter Variable', 'Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '16px',
        xl2: '18px',
      },
      boxShadow: {
        card: '0 2px 10px rgba(16, 52, 61, 0.05)',
        float: '0 12px 34px rgba(11, 95, 82, 0.16)',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
      },
      animation: {
        'fade-up': 'fade-up .35s ease-out both',
        shimmer: 'shimmer 1.4s linear infinite',
      },
    },
  },
  plugins: [],
}
