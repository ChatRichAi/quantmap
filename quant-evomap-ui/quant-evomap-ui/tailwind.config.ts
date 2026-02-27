import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#667eea',
          deep: '#764ba2',
        },
        accent: {
          DEFAULT: '#f093fb',
          light: '#a78bfa',
          pink: '#f472b6',
        },
        success: '#10b981',
        danger: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6',
        bg: {
          root: '#0a0a0f',
          deep: '#0f0f15',
          card: '#1a1a24',
          float: 'rgba(15, 15, 25, 0.8)',
        },
        surface: {
          1: 'rgba(255, 255, 255, 0.03)',
          2: 'rgba(255, 255, 255, 0.05)',
          3: 'rgba(255, 255, 255, 0.08)',
          4: 'rgba(255, 255, 255, 0.10)',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        display: ['Inter Display', 'Inter', 'sans-serif'],
        mono: ['ui-monospace', 'Monaco', 'Menlo', 'monospace'],
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'title-gradient': 'linear-gradient(to right, #a78bfa, #f472b6)',
        'glow-gradient': 'linear-gradient(135deg, rgba(102,126,234,0.5), rgba(118,75,162,0.5), rgba(240,147,251,0.5))',
        'divider-gradient': 'linear-gradient(to right, transparent, rgba(255,255,255,0.1), transparent)',
      },
      boxShadow: {
        'glow-xs': '0 0 8px rgba(102, 126, 234, 0.2)',
        'glow-sm': '0 0 12px rgba(102, 126, 234, 0.2)',
        'glow': '0 0 16px rgba(102, 126, 234, 0.35)',
        'glow-lg': '0 0 20px rgba(102, 126, 234, 0.25)',
        'glow-xl': '0 0 24px rgba(102, 126, 234, 0.4)',
        'glow-green': '0 0 10px rgba(67, 233, 123, 0.15)',
        'card': '0 4px 20px rgba(0, 0, 0, 0.3)',
        'card-hover': '0 8px 32px rgba(0, 0, 0, 0.4)',
        'float': '0 8px 32px rgba(0, 0, 0, 0.4)',
      },
      animation: {
        'pulse-slow': 'pulse 2s infinite',
        'shimmer': 'shimmer 1.5s infinite',
        'slide-in': 'agentCardSlideIn 0.35s ease-out forwards',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
      },
      keyframes: {
        pulse: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.5', transform: 'scale(1.2)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        agentCardSlideIn: {
          from: { opacity: '0', transform: 'translateX(12px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 12px rgba(102, 126, 234, 0.2)' },
          '50%': { boxShadow: '0 0 20px rgba(102, 126, 234, 0.4)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
