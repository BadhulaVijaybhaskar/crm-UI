/**
 * Serve the production Vite build with Jinja boot replaced by a static blob.
 * Assets stay at /assets/crm/frontend/*; the SPA lives under /crm.
 */
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { buildBoot, bootScript } from './boot.js'

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.woff2': 'font/woff2',
  '.woff': 'font/woff',
  '.ico': 'image/x-icon',
  '.webmanifest': 'application/manifest+json',
  '.map': 'application/json',
}

function send(res, status, body, headers = {}) {
  res.writeHead(status, headers)
  res.end(body)
}

function readIndex(distDir, theme) {
  const raw = fs.readFileSync(path.join(distDir, 'index.html'), 'utf8')
  const boot = bootScript(buildBoot({ theme }))
  // Strip leftover Jinja from frappe-ui buildConfig
  return raw.replace(
    /<script>\s*\{%\s*for key in boot\s*%\}[\s\S]*?\{%\s*endfor\s*%\}\s*<\/script>/,
    boot,
  )
}

export function startParityServer({ distDir, theme = 'light', port = 0 } = {}) {
  if (!fs.existsSync(path.join(distDir, 'index.html'))) {
    throw new Error(
      `Parity dist missing at ${distDir}. Run yarn build in frontend/ first.`,
    )
  }

  let cachedHtml = readIndex(distDir, theme)

  const server = http.createServer((req, res) => {
    const url = new URL(req.url || '/', `http://${req.headers.host}`)
    let pathname = decodeURIComponent(url.pathname)

    // SPA routes
    if (
      pathname === '/' ||
      pathname === '/crm' ||
      pathname === '/crm/' ||
      pathname.startsWith('/crm/')
    ) {
      return send(res, 200, cachedHtml, {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-store',
      })
    }

    // Built assets
    let filePath = null
    if (pathname.startsWith('/assets/crm/frontend/')) {
      const rel = pathname.slice('/assets/crm/frontend/'.length)
      filePath = path.join(distDir, rel)
    } else if (pathname.startsWith('/assets/')) {
      // favicon / public images sometimes absolute
      filePath = path.join(distDir, path.basename(pathname))
    }

    if (!filePath || !filePath.startsWith(distDir)) {
      return send(res, 404, 'not found')
    }

    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      return send(res, 404, 'not found')
    }

    const ext = path.extname(filePath).toLowerCase()
    const body = fs.readFileSync(filePath)
    return send(res, 200, body, {
      'Content-Type': MIME[ext] || 'application/octet-stream',
      'Cache-Control': 'public, max-age=60',
    })
  })

  return new Promise((resolve) => {
    server.listen(port, '127.0.0.1', () => {
      const addr = server.address()
      resolve({
        port: addr.port,
        origin: `http://127.0.0.1:${addr.port}`,
        close: () =>
          new Promise((r, j) => server.close((e) => (e ? j(e) : r()))),
        setTheme(next) {
          cachedHtml = readIndex(distDir, next)
        },
      })
    })
  })
}
