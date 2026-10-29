// Static server for `core/dist` with SPA fallback and an /api proxy, so the
// production bundle can be measured and tested without docker or vite.
//
//   node tests/audit/serve.cjs [port] [backend]
const http = require('http')
const fs = require('fs')
const path = require('path')

const PORT = Number(process.argv[2] || 5590)
const BACKEND = process.argv[3] || 'http://127.0.0.1:8002'
const ROOT = path.resolve(__dirname, '../../core/dist')

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.webp': 'image/webp',
  '.mp3': 'audio/mpeg',
  '.woff2': 'font/woff2',
  '.glb': 'model/gltf-binary',
  '.riv': 'application/octet-stream',
  '.webm': 'video/webm',
  '.mp4': 'video/mp4',
}

function proxy(req, res) {
  const target = new URL(req.url, BACKEND)
  const opts = {
    method: req.method,
    headers: { ...req.headers, host: target.host },
  }
  const upstream = http.request(target, opts, (up) => {
    res.writeHead(up.statusCode || 502, up.headers)
    up.pipe(res)
  })
  upstream.on('error', (e) => {
    res.writeHead(502, { 'content-type': 'application/json' })
    res.end(JSON.stringify({ detail: 'backend unavailable: ' + e.message }))
  })
  req.pipe(upstream)
}

function serveFile(file, req, res) {
  fs.stat(file, (err, st) => {
    if (err || !st.isFile()) return false
    const ext = path.extname(file).toLowerCase()
    const etag = `W/"${st.size.toString(16)}-${st.mtimeMs.toString(16)}"`
    if (req.headers['if-none-match'] === etag) {
      res.writeHead(304).end()
      return true
    }
    res.writeHead(200, {
      'content-type': TYPES[ext] || 'application/octet-stream',
      'content-length': st.size,
      etag,
      'cache-control': /assets\//.test(file) ? 'public, max-age=31536000, immutable' : 'no-cache',
    })
    fs.createReadStream(file).pipe(res)
    return true
  })
  return true
}

http.createServer((req, res) => {
  const url = decodeURIComponent((req.url || '/').split('?')[0])
  if (url.startsWith('/api/') || url.startsWith('/uploads/') || url.startsWith('/media/')) {
    if (url.startsWith('/api/')) req.url = url.replace(/^\/api/, '') || '/'
    return proxy(req, res)
  }
  const file = path.join(ROOT, path.normalize(url))
  if (!file.startsWith(ROOT)) {
    res.writeHead(403).end('forbidden')
    return
  }
  fs.stat(file, (err, st) => {
    if (!err && st.isFile()) {
      serveFile(file, req, res)
      return
    }
    // SPA fallback
    serveFile(path.join(ROOT, 'index.html'), req, res)
  })
}).listen(PORT, () => console.log(`serving ${ROOT} on http://localhost:${PORT} (api → ${BACKEND})`))
