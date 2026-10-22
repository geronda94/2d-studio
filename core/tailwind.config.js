export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: 'var(--font-sans)',
        heading: 'var(--font-heading)',
        mono: 'var(--font-mono)',
      },
      colors: {
        bg: {
          base: 'rgb(var(--bg-base-rgb) / <alpha-value>)',
          surface: 'rgb(var(--bg-surface-rgb) / <alpha-value>)',
          'surface-2': 'rgb(var(--bg-surface-2-rgb) / <alpha-value>)',
          hover: 'rgb(var(--bg-hover-rgb) / <alpha-value>)',
          overlay: 'var(--bg-overlay)', // RGBA from token
          
          // Aliases
          surfaceHover: 'rgb(var(--bg-hover-rgb) / <alpha-value>)', 
        },
        border: {
          main: 'rgb(var(--border-main-rgb) / <alpha-value>)',
          strong: 'rgb(var(--border-strong-rgb) / <alpha-value>)',
          accent: 'rgb(var(--border-accent-rgb) / <alpha-value>)',
        },
        text: {
          primary: 'rgb(var(--text-primary-rgb) / <alpha-value>)',
          secondary: 'rgb(var(--text-secondary-rgb) / <alpha-value>)',
          muted: 'rgb(var(--text-muted-rgb) / <alpha-value>)',
          'on-color': 'rgb(var(--text-on-color-rgb) / <alpha-value>)',
        },
        color: {
          primary: 'rgb(var(--color-primary-rgb) / <alpha-value>)',
          'primary-soft': 'rgb(var(--color-primary-soft-rgb) / <alpha-value>)',
          secondary: 'rgb(var(--color-secondary-rgb) / <alpha-value>)',
          'secondary-soft': 'rgb(var(--color-secondary-soft-rgb) / <alpha-value>)',
          accent: 'rgb(var(--color-accent-rgb) / <alpha-value>)',
          'accent-soft': 'rgb(var(--color-accent-soft-rgb) / <alpha-value>)',
          'accent-2': 'rgb(var(--color-accent-2-rgb) / <alpha-value>)',
          'accent-2-soft': 'rgb(var(--color-accent-2-soft-rgb) / <alpha-value>)',
          success: 'rgb(var(--color-success-rgb) / <alpha-value>)',
          'success-soft': 'rgb(var(--color-success-soft-rgb) / <alpha-value>)',
          warning: 'rgb(var(--color-warning-rgb) / <alpha-value>)',
          'warning-soft': 'rgb(var(--color-warning-soft-rgb) / <alpha-value>)',
          error: 'rgb(var(--color-error-rgb) / <alpha-value>)',
          'error-soft': 'rgb(var(--color-error-soft-rgb) / <alpha-value>)',
          danger: 'rgb(var(--color-danger-rgb) / <alpha-value>)',
          'danger-soft': 'rgb(var(--color-danger-soft-rgb) / <alpha-value>)',
          info: 'rgb(var(--color-info-rgb) / <alpha-value>)',
          'info-soft': 'rgb(var(--color-info-soft-rgb) / <alpha-value>)',
        },
        itemAccent: {
          1: 'rgb(var(--item-accent-1-rgb) / <alpha-value>)',
          2: 'rgb(var(--item-accent-2-rgb) / <alpha-value>)',
          3: 'rgb(var(--item-accent-3-rgb) / <alpha-value>)',
          4: 'rgb(var(--item-accent-4-rgb) / <alpha-value>)',
        },
        slideBg: {
          1: 'rgb(var(--slide-bg-1-rgb) / <alpha-value>)',
          2: 'rgb(var(--slide-bg-2-rgb) / <alpha-value>)',
          3: 'rgb(var(--slide-bg-3-rgb) / <alpha-value>)',
          4: 'rgb(var(--slide-bg-4-rgb) / <alpha-value>)',
        },
        chart: {
          1: 'rgb(var(--chart-1-rgb) / <alpha-value>)',
          2: 'rgb(var(--chart-2-rgb) / <alpha-value>)',
          3: 'rgb(var(--chart-3-rgb) / <alpha-value>)',
          4: 'rgb(var(--chart-4-rgb) / <alpha-value>)',
          5: 'rgb(var(--chart-5-rgb) / <alpha-value>)',
          6: 'rgb(var(--chart-6-rgb) / <alpha-value>)',
          grid: 'var(--chart-grid)', // RGBA from token
          axis: 'rgb(var(--chart-axis-rgb) / <alpha-value>)',
        },
        // АЛИАСЫ ДЛЯ СТАРЫХ КЛАССОВ (БЕЗОПАСНАЯ МИГРАЦИЯ)
        brand: {
          blue: 'rgb(var(--color-primary-rgb) / <alpha-value>)',
          lightBlue: 'rgb(var(--color-secondary-rgb) / <alpha-value>)',
          green: 'rgb(var(--color-success-rgb) / <alpha-value>)',
          amber: 'rgb(var(--color-warning-rgb) / <alpha-value>)',
          orange: 'rgb(var(--color-accent-rgb) / <alpha-value>)',
          accent: 'rgb(var(--color-accent-rgb) / <alpha-value>)',
        },
      },
      boxShadow: {
        'elegant': '0 20px 50px -10px rgba(0, 0, 0, 0.9), inset 0 1px 1px rgba(255,255,255,0.05)',
        'elegant-inner': 'inset 0 10px 30px rgba(0, 0, 0, 0.8)',
        'colored-blue': '0 20px 40px -10px rgba(37, 99, 235, 0.15)',
        'colored-amber': '0 20px 40px -10px rgba(245, 158, 11, 0.15)',
        'colored-green': '0 20px 40px -10px rgba(16, 185, 129, 0.15)',
      },
      transitionDuration: {
        'fast': '300ms',
        'base': '600ms',
        'slow': '1200ms',
      },
      keyframes: {
        'gradient-x': {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left center'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right center'
          },
        }
      },
      animation: {
        'gradient-x': 'gradient-x 3s ease infinite',
      }
    }
  },
  plugins: [],
}
