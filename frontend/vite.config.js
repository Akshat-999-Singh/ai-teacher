import fs from 'node:fs'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import sirv from 'sirv'

const fromRoot = (path) => fileURLToPath(new URL(`../${path}`, import.meta.url))

// The sidebar's topic list. tools/render_topic.py adds a topic to rendered/manifest.json
// when it publishes the video. This reads that file on every request and drops entries
// whose video or script is gone (tools/topic_manifest.py applies the same rule for the
// classifier), so a new topic appears on refresh and a deleted one disappears, with no
// code change and no restart.
function topicList(req, res) {
  let manifest = {}
  try {
    manifest = JSON.parse(fs.readFileSync(fromRoot('rendered/manifest.json'), 'utf8'))
  } catch (err) {
    if (err.code !== 'ENOENT') {
      res.statusCode = 500
      res.end(`rendered/manifest.json: ${err.message}`)
      return
    }
  }
  const topics = Object.entries(manifest)
    .filter(([, entry]) => fs.existsSync(fromRoot(entry.video)) && fs.existsSync(fromRoot(entry.script)))
    .map(([id, { title, category }]) => ({ id, title, category }))
  res.setHeader('Content-Type', 'application/json; charset=utf-8')
  res.setHeader('Cache-Control', 'no-store')
  res.end(JSON.stringify(topics))
}

// Videos and narration are pipeline outputs outside frontend/, so serve them in
// place rather than copying. sirv answers Range requests, which <video> seeking needs.
function projectMedia() {
  const mount = (server) => {
    server.middlewares.use('/media/topics.json', topicList)
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
