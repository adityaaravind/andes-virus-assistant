/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: '#0a0a0a',
        teal: '#00b4d8',
        'red-alert': '#ef4444',
        amber: '#f59e0b',
      }
    },
  },
  plugins: [],
}
