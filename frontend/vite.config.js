import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import sirv from 'sirv'

const fromRoot = (dir) => fileURLToPath(new URL(`../${dir}`, import.meta.url))

// Videos and narration are pipeline outputs outside frontend/, so serve them in
// place rather than copying. sirv answers Range requests, which <video> seeking needs.
function projectMedia() {
  const mount = (server) => {
    server.middlewares.use('/media/rendered', sirv(fromRoot('rendered'), { dev: true }))
    server.middlewares.use('/media/scripts', sirv(fromRoot('scripts'), { dev: true }))
  }
  return { name: 'project-media', configureServer: mount, configurePreviewServer: mount }
}

// The classifier service (tools/classify_api.py); same origin for the browser, so no CORS.
const proxy = {
  '/api': { target: 'http://127.0.0.1:8000', rewrite: (path) => path.replace(/^\/api/, '') },
}

export default defineConfig({
  plugins: [react(), projectMedia()],
  server: { port: 5173, proxy },
  preview: { proxy },
})
