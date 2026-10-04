/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Atkinson Hyperlegible Next"', 'system-ui', 'sans-serif'],
      },
      colors: {
        paper: '#F5F6F4',
        ink: { DEFAULT: '#1E2A2D', soft: '#4A5759', faint: '#6B7678' },
        rule: { DEFAULT: '#D9DDD8', strong: '#B9C0BA' },
        scrub: { DEFAULT: '#0E5A54', dark: '#0A4541', tint: '#E3EFEC' },
        late: { DEFAULT: '#A8321F', tint: '#F7E6E2' },
        soon: { DEFAULT: '#8A5C00', tint: '#F6EDD9' },
        ok: { DEFAULT: '#2F6B3A', tint: '#E4EFE4' },
      },
    },
  },
  plugins: [],
};
