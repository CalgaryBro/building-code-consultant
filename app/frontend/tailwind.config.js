/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary palette - Architectural Slate
        slate: {
          950: '#020617',
          900: '#0f172a',
          800: '#1e293b',
          700: '#334155',
          600: '#475569',
          500: '#64748b',
          400: '#94a3b8',
          300: '#cbd5e1',
          200: '#e2e8f0',
          100: '#f1f5f9',
          50: '#f8fafc',
        },
        // Accent - Calgary Amber/Gold
        amber: {
          950: '#451a03',
          900: '#78350f',
          800: '#92400e',
          700: '#b45309',
          600: '#d97706',
          500: '#f59e0b',
          400: '#fbbf24',
          300: '#fcd34d',
          200: '#fde68a',
          100: '#fef3c7',
          50: '#fffbeb',
        },
        // Success - Teal
        teal: {
          600: '#0d9488',
          500: '#14b8a6',
          400: '#2dd4bf',
        },
        // Warning/Fail - Rose
        rose: {
          600: '#e11d48',
          500: '#f43f5e',
          400: '#fb7185',
        },
        // Warm background
        cream: {
          50: '#fefce8',
          100: '#fef9c3',
        }
      },
      fontFamily: {
        'display': ['"Instrument Serif"', 'Georgia', 'serif'],
        'sans': ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        'mono': ['"JetBrains Mono"', 'Consolas', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.5s ease-out forwards',
        'slide-in-right': 'slideInRight 0.4s ease-out forwards',
        'scale-in': 'scaleIn 0.3s ease-out forwards',
        'pulse-subtle': 'pulseSubtle 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
      },
      backgroundImage: {
        'grid-slate': `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23334155' fill-opacity='0.08'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      boxShadow: {
        'glow-amber': '0 0 40px -10px rgba(245, 158, 11, 0.3)',
        'glow-teal': '0 0 40px -10px rgba(20, 184, 166, 0.3)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'card-hover': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
      },
    },
  },
  plugins: [],
}
