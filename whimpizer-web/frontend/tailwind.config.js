/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        wimpy: {
          blue: '#2563eb',
          yellow: '#fbbf24',
          orange: '#f97316',
          green: '#22c55e',
          red: '#ef4444',
          gray: '#6b7280'
        }
      },
      fontFamily: {
        'comic': ['Comic Sans MS', 'cursive'],
        'wimpy': ['Arial', 'sans-serif']
      }
    },
  },
  plugins: [],
}