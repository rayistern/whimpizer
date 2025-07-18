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
        'wimpy': ['WimpyKid', 'Comic Sans MS', 'cursive'],
        'wimpy-dialogue': ['WimpyKidDialogue', 'Comic Sans MS', 'cursive'],
        'wimpy-cover': ['WimpyCover', 'Impact', 'sans-serif'],
        'rowley': ['Rowley', 'Comic Sans MS', 'cursive'],
        'kong': ['Kongtext', 'monospace', 'cursive']
      }
    },
  },
  plugins: [],
}