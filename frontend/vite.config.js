/* global process */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Isolated dev/preview proxy (infra/docker-compose.backend.yml, 127.0.0.1:18000).
// Same origin in the browser, so the SameSite session cookie just works. The /api prefix is
// stripped because backend routes live at the root and would clash with SPA paths like /auth/callback.
const api = {
  '/api': {
    target: process.env.WORKBENCH_API_PROXY || 'http://localhost:18000',
    changeOrigin: true,
    rewrite: path => path.replace(/^\/api/, ''),
  },
}

export default defineConfig({
  plugins: [react()],
  server: { port: 15173, strictPort: true, proxy: api },
  preview: { port: 15173, strictPort: true, proxy: api },
})
