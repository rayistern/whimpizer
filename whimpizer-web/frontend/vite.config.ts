import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          api: ['axios', '@tanstack/react-query'],
          ui: ['lucide-react']
        }
      }
    }
  },
  server: {
    port: 3000,
    host: true, // Allow external connections
  },
  preview: {
    port: 3000,
    host: true,
  }
})
