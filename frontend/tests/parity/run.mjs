#!/usr/bin/env node
/**
 * yarn parity <screen-id|all> [<screen-id> …] [--theme=light|dark]
 *
 * TEST-ONLY pixel-parity harness. Serves the production Vite build, mocks
 * Frappe APIs from fixtures/, freezes Date, screenshots at Figma size, and
 * writes built|figma|diff triplets under /opt/cursor/artifacts/parity/.
 *
 * Nothing here is imported by production src/.
 *
 * Pass bar (same viewport, Example-data mask only, 1px / 0.1 "real" diff):
 *   (a) Vue vs unedited sourceHtml = 0 % on pixels where HTML agrees with PNG
 *       (PNG wins on layout; p-*.html and PNGs are READ-ONLY — never edit them)
 *   (b) Vue vs Figma PNG ≤ 0.75 % (absolute, light and dark)
 *
 * floor % = sourceHtml-in-Chrome vs PNG (informational). If sourceHtml is
 * missing, (a) is n/a and the row is PARTIAL when PNG ≤ 0.75 %, else FAIL.
 */
import fs from 'node:fs'
import path from 'node:path'
import { chromium } from 'playwright'
import {
  PATHS,
  PARITY_CLOCK,
  PASS,
  DEFAULT_SESSION_USER,
  SCREENS,
  resolveFigmaPng,
} from './config.js'
import { startParityServer } from './lib/server.js'
import { clockInitScript } from './lib/clock.js'
import {
  installParityMocks,
  sessionInitScript,
  themeInitScript,
} from './lib/mocks.js'
import { compareImages } from './lib/diff.js'
import { screenshotSourceHtml } from './lib/sourceShot.js'

const THEMES = ['light', 'dark']

function usage() {
  console.error(`Usage: yarn parity <screen-id|all> [<screen-id> …] [--theme=light|dark]
Known screens: ${Object.keys(SCREENS).join(', ')}`)
  process.exit(2)
}

function findFigma(fileName) {
  const local = path.join(PATHS.figmaDir, fileName)
  if (fs.existsSync(local)) return local
  const fallback = path.join(PATHS.figmaFallback, fileName)
  if (fs.existsSync(fallback)) return fallback
  throw new Error(`Figma PNG not found: ${fileName}`)
}

function sourceHtmlAvailable(screen, theme) {
  const file = screen.sourceHtml?.[theme]
  return Boolean(file && fs.existsSync(path.join(PATHS.figmaSrc, file)))
}

async function resolveMasks(page, screen) {
  const resolved = []
  for (const m of screen.masks || []) {
    if (m.selector) {
      const loc = page.locator(m.selector).first()
      if ((await loc.count()) > 0) {
        const box = await loc.boundingBox()
        if (box) {
          resolved.push({ name: m.name, ...box })
          continue
        }
      }
    }
    if (m.fallback) resolved.push({ name: m.name, ...m.fallback })
  }
  return resolved
}

async function runTheme({ screen, theme, origin, browser }) {
  const user = screen.sessionUser || DEFAULT_SESSION_USER
  const context = await browser.newContext({
    viewport: screen.viewport,
    deviceScaleFactor: screen.deviceScaleFactor || 1,
    colorScheme: theme === 'dark' ? 'dark' : 'light',
    timezoneId: 'Asia/Kolkata',
  })
  const page = await context.newPage()

  await page.addInitScript(clockInitScript(screen.clock || PARITY_CLOCK))
  await page.addInitScript(sessionInitScript(user.email, user.fullName))
  await page.addInitScript(themeInitScript(theme))

  await installParityMocks(page, { fixture: screen.fixture || screen.id })

  const url = `${origin}${screen.route}`
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {})
  await page.waitForTimeout(1500)
  await page.evaluate(async () => {
    if (document.fonts?.ready) await document.fonts.ready
  })
  await page.waitForTimeout(400)

  fs.mkdirSync(PATHS.artifacts, { recursive: true })
  const builtPath = path.join(PATHS.artifacts, `_tmp-${screen.id}-${theme}-built.png`)
  await page.screenshot({
    path: builtPath,
    clip: {
      x: 0,
      y: 0,
      width: screen.viewport.width,
      height: screen.viewport.height,
    },
    animations: 'disabled',
  })
  const masks = await resolveMasks(page, screen)
  await context.close()

  const figmaPath = findFigma(resolveFigmaPng(screen.id, theme))
  const pngTriplet = path.join(PATHS.artifacts, `${screen.id}-${theme}.png`)

  // (b) built vs Figma PNG
  const png = compareImages({
    builtPath,
    figmaPath,
    outTripletPath: pngTriplet,
    masks,
    shellRegions: screen.shellRegions || [],
  })

  // (a) built vs sourceHtml in Chrome (only where HTML agrees with PNG)
  // floor = sourceHtml vs PNG (informational; refs are read-only)
  const hasSource = sourceHtmlAvailable(screen, theme)
  let html = null
  let floor = null
  let htmlTriplet = null
  let sourcePath = null
  if (hasSource) {
    sourcePath = path.join(PATHS.artifacts, `_tmp-${screen.id}-${theme}-source.png`)
    await screenshotSourceHtml({
      browser,
      htmlFile: screen.sourceHtml[theme],
      theme,
      viewport: screen.viewport,
      outPath: sourcePath,
    })
    floor = compareImages({
      builtPath: sourcePath,
      figmaPath,
      masks,
    })
    // Score Vue vs HTML only where HTML agrees with PNG (PNG wins on layout).
    htmlTriplet = path.join(PATHS.artifacts, `${screen.id}-${theme}-vs-html.png`)
    html = compareImages({
      builtPath,
      figmaPath: sourcePath,
      outTripletPath: htmlTriplet,
      masks,
      excludeDisagreement: { aPath: sourcePath, bPath: figmaPath },
    })
  }

  for (const p of [builtPath, sourcePath]) {
    if (!p) continue
    try {
      fs.unlinkSync(p)
    } catch {
      /* keep */
    }
  }

  const htmlRealPct = html ? html.realPct : null
  const pngRealPct = png.realPct
  const floorPct = floor ? floor.realPct : PASS.nominalFloorPct
  const floorEstimated = !floor
  const htmlOk = htmlRealPct != null && htmlRealPct <= PASS.htmlEpsilonPct
  const pngOk = pngRealPct <= PASS.pngMaxPct

  let status
  if (hasSource) status = htmlOk && pngOk ? 'PASS' : 'FAIL'
  else status = pngOk ? 'PARTIAL' : 'FAIL'

  const remainingPngPct = Math.max(0, pngRealPct - PASS.pngMaxPct)
  const remainingHtmlPct =
    htmlRealPct == null ? null : Math.max(0, htmlRealPct - PASS.htmlEpsilonPct)
  const total = png.width * png.height
  const maskedNames = [
    ...masks.map((m) => m.name),
    ...(html?.disagreePx
      ? [`html↔png disagree (${html.disagreePx}px)`]
      : []),
  ]

  return {
    screen: screen.id,
    theme,
    viewport: screen.viewport,
    clock: screen.clock || PARITY_CLOCK,
    htmlRealPct,
    pngRealPct,
    floorPct,
    floorEstimated,
    status,
    pass: status === 'PASS',
    masked: maskedNames,
    remainingHtmlPct,
    remainingPngPct,
    remainingHtmlPx: html ? Math.max(0, html.real) : null,
    remainingPngPx: Math.round((remainingPngPct / 100) * total),
    rawPngPct: png.rawPct,
    rawHtmlPct: html ? html.rawPct : null,
    shellRealPct: png.shellRealPct,
    pngTriplet,
    htmlTriplet,
  }
}

function fmt(pct) {
  if (pct == null || Number.isNaN(pct)) return 'n/a'
  return `${pct.toFixed(4)}%`
}

function remainingText(r) {
  if (r.status === 'PASS') return '—'
  const parts = []
  if (r.remainingHtmlPct == null) parts.push('html: no source (read-only pack missing)')
  else if (r.remainingHtmlPct > 0) parts.push(`html ${fmt(r.remainingHtmlPct)} on HTML∩PNG`)
  if (r.remainingPngPct > 0) parts.push(`png ${fmt(r.pngRealPct)} > ${PASS.pngMaxPct}%`)
  return parts.join('; ') || '—'
}

function printTable(rows) {
  const lines = [
    '| screen | theme | real vs HTML % | real vs PNG % | floor % | pass | masked | remaining |',
    '|---|---|---:|---:|---:|---|---|---|',
  ]
  for (const r of rows) {
    lines.push(
      `| ${r.screen} | ${r.theme} | ${fmt(r.htmlRealPct)} | ${fmt(r.pngRealPct)} | ${fmt(r.floorPct)}${r.floorEstimated ? ' (nominal)' : ''} | ${r.status} | ${(r.masked || []).join('; ') || '—'} | ${remainingText(r)} |`,
    )
  }
  return lines.join('\n')
}

function parseArgs(argv) {
  const ids = []
  let themes = THEMES
  for (const a of argv) {
    if (a.startsWith('--theme=')) {
      const t = a.slice('--theme='.length)
      if (!THEMES.includes(t)) usage()
      themes = [t]
    } else if (a.startsWith('-')) usage()
    else ids.push(a)
  }
  if (!ids.length) usage()
  const screenIds = ids.includes('all') ? Object.keys(SCREENS) : ids
  for (const id of screenIds) {
    if (!SCREENS[id]) {
      console.error(`Unknown screen "${id}"`)
      usage()
    }
  }
  return { screenIds, themes }
}

async function main() {
  const { screenIds, themes } = parseArgs(process.argv.slice(2))

  if (!fs.existsSync(path.join(PATHS.dist, 'index.html'))) {
    console.error('Production build missing. Run: cd frontend && yarn build')
    process.exit(1)
  }
  fs.mkdirSync(PATHS.artifacts, { recursive: true })

  const chromePath = ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable'].find(
    (p) => fs.existsSync(p),
  )

  const results = []
  for (const screenId of screenIds) {
    const screen = SCREENS[screenId]
    const screenResults = []
    for (const theme of themes) {
      const server = await startParityServer({ distDir: PATHS.dist, theme })
      const browser = await chromium.launch({
        headless: true,
        executablePath: chromePath,
        args: ['--font-render-hinting=none', '--disable-lcd-text', '--no-sandbox'],
      })
      try {
        const row = await runTheme({ screen, theme, origin: server.origin, browser })
        screenResults.push(row)
        console.log(
          `[parity] ${screen.id}/${theme}: html=${fmt(row.htmlRealPct)} png=${fmt(row.pngRealPct)} floor=${fmt(row.floorPct)} ${row.status}`,
        )
      } finally {
        await browser.close()
        await server.close()
      }
    }
    results.push(...screenResults)

    const report = {
      clock: screen.clock || PARITY_CLOCK,
      generatedAt: new Date().toISOString(),
      passBar: PASS,
      results: screenResults,
    }
    fs.writeFileSync(
      path.join(PATHS.artifacts, `${screen.id}-report.json`),
      JSON.stringify(report, null, 2),
    )
  }

  const reportName = screenIds.length === 1 ? screenIds[0] : 'all'
  const md = [
    `# Parity — ${screenIds.join(', ')}`,
    '',
    printTable(results),
    '',
    '## Pass bar',
    '',
    `- (a) **real vs HTML** — Vue vs unedited \`p-*.html\` in Chrome = 0% on pixels where that HTML agrees with the PNG (PNG wins on layout).`,
    `- (b) **real vs PNG** — Vue vs Figma PNG ≤ **${PASS.pngMaxPct}%** (absolute, light and dark).`,
    '- **floor %** = HTML-in-Chrome vs PNG (informational only).',
    '- **READ-ONLY:** never edit `p-*.html` or Figma PNGs to make a diff pass.',
    '- Design mask: only the **Example data** tag. HTML↔PNG disagreement spans are masked solely for scoring (a).',
    '- **PARTIAL** = sourceHtml missing: (a) n/a; PNG ≤ 0.75% is not a full pass.',
    '',
  ].join('\n')
  const jsonPath = path.join(PATHS.artifacts, `${reportName}-report.json`)
  const mdPath = path.join(PATHS.artifacts, `${reportName}-report.md`)
  fs.writeFileSync(
    jsonPath,
    JSON.stringify({ generatedAt: new Date().toISOString(), passBar: PASS, results }, null, 2),
  )
  fs.writeFileSync(mdPath, md)
  console.log('\n' + md)
  console.log(`Wrote ${jsonPath}`)
  console.log(`Wrote ${mdPath}`)

  process.exit(results.some((r) => r.status === 'FAIL') ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
