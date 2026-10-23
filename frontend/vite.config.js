import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'serve-live-csv-data',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (req.url && (req.url.startsWith('/api/csv/') || req.url.startsWith('/data/'))) {
            const cleanUrl = req.url.split('?')[0]
            const filename = path.basename(cleanUrl)
            // Look in parent data directory first for fresh outputs
            const parentDataFile = path.resolve(__dirname, '../data', filename)
            const publicDataFile = path.resolve(__dirname, 'public/data', filename)

            const targetFile = fs.existsSync(parentDataFile) ? parentDataFile : (fs.existsSync(publicDataFile) ? publicDataFile : null)

            if (targetFile) {
              res.setHeader('Content-Type', 'text/csv; charset=utf-8')
              res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate')
              return fs.createReadStream(targetFile).pipe(res)
            }
          }
          next()
        })
      }
    }
  ],
  server: {
    port: 5173,
    host: true
  }
})
