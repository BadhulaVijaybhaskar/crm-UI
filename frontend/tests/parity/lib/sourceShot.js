/**
 * Screenshot the Figma capture HTML in the same browser engine as the Vue
 * build, so we can separate Vue shell deltas from the Figma MCP rasterisation
 * floor (PNG ≠ Chrome pixels even for identical HTML).
 */
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { PATHS } from '../config.js'

export async function screenshotSourceHtml({
  browser,
  htmlFile,
  theme,
  viewport,
  outPath,
}) {
  const root = PATHS.figmaSrc
  if (!fs.existsSync(path.join(root, htmlFile))) {
    throw new Error(`Figma source HTML missing: ${path.join(root, htmlFile)}`)
  }

  const server = http.createServer((req, res) => {
    let pathname = decodeURIComponent(new URL(req.url, 'http://x').pathname)
    if (pathname === '/') pathname = `/${htmlFile}`
    const fp = path.join(root, pathname)
    if (!fp.startsWith(root) || !fs.existsSync(fp)) {
      res.writeHead(404)
      return res.end('not found')
    }
    const ext = path.extname(fp).toLowerCase()
    const mime =
      {
        '.html': 'text/html; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
        '.png': 'image/png',
        '.js': 'text/javascript; charset=utf-8',
        '.woff2': 'font/woff2',
      }[ext] || 'application/octet-stream'
    res.writeHead(200, { 'Content-Type': mime })
    res.end(fs.readFileSync(fp))
  })

  await new Promise((r) => server.listen(0, '127.0.0.1', r))
  const { port } = server.address()

  const inter = (w) =>
    fs
      .readFileSync(path.join(PATHS.frontend, `src/assets/fonts/Inter-${w}.woff2`))
      .toString('base64')

  const context = await browser.newContext({
    viewport,
    deviceScaleFactor: 1,
    colorScheme: theme === 'dark' ? 'dark' : 'light',
  })
  const page = await context.newPage()
  await page.goto(`http://127.0.0.1:${port}/${htmlFile}`, {
    waitUntil: 'networkidle',
    timeout: 30000,
  })
  await page.addStyleTag({
      content: `
  @font-face{font-family:Inter;font-weight:400;src:url(data:font/woff2;base64,${inter(400)}) format('woff2')}
  @font-face{font-family:Inter;font-weight:500;src:url(data:font/woff2;base64,${inter(500)}) format('woff2')}
  @font-face{font-family:Inter;font-weight:600;src:url(data:font/woff2;base64,${inter(600)}) format('woff2')}
  `,
    })
  await page.evaluate(() => document.fonts.ready)
  await page.waitForTimeout(400)
  fs.mkdirSync(path.dirname(outPath), { recursive: true })
  await page.screenshot({
    path: outPath,
    clip: { x: 0, y: 0, width: viewport.width, height: viewport.height },
    animations: 'disabled',
  })
  await context.close()
  await new Promise((r, j) => server.close((e) => (e ? j(e) : r())))
  return outPath
}
