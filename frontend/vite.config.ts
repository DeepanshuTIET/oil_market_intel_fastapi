import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/static/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: '../app/static',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        // Keep clean asset names
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/health': 'http://localhost:8000',
      '/debug': 'http://localhost:8000',
      '/ingest': 'http://localhost:8000',
      '/eia': 'http://localhost:8000',
      '/cot': 'http://localhost:8000',
      '/quanthub': 'http://localhost:8000',
      '/features': 'http://localhost:8000',
      '/signals': 'http://localhost:8000',
      '/regime': 'http://localhost:8000',
      '/alerts': 'http://localhost:8000',
      '/docs': 'http://localhost:8000',
      '/redoc': 'http://localhost:8000',
      '/openapi.json': 'http://localhost:8000',
    },
  },
})
