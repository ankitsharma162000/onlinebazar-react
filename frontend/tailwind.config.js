/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#2874F0', dark: '#1a5dc8' },
        accent:  { DEFAULT: '#FB641B', dark: '#e0521a' },
      }
    }
  },
  plugins: []
}
