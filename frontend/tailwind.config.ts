import type { Config } from 'tailwindcss';

export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2E7D32',
          soft: '#E8F5E9',
        },
        accent: {
          DEFAULT: '#F59E0B',
        },
        ink: {
          DEFAULT: '#1F2937',
        },
        muted: {
          DEFAULT: '#6B7280',
        },
        surface: {
          DEFAULT: '#FFFFFF',
        },
        bg: {
          DEFAULT: '#F7F8F5',
        },
        success: '#2E7D32',
        warning: '#B45309',
        danger: '#B91C1C',
        info: '#1D4ED8',
      },
    },
  },
  plugins: [],
} satisfies Config;
