#!/usr/bin/env node
/**
 * yarn parity <screen>
 *
 * TEST-ONLY pixel-parity harness. Serves the production Vite build, mocks
 * Frappe APIs from fixtures/, freezes Date, screenshots at Figma size, and
 * writes built|figma|diff triplets under /opt/cursor/artifacts/parity/.
 *
 * Nothing here is imported by production src/.
 *
 * Pass bar (per screen × theme):
 *   (a) real % vs source HTML (p-*.html in Chrome) ≈ 0  (ε = 0.05%)
 *   (b) real % vs Figma PNG ≤ floor (sourceHtml↔PNG), ~0.75% typical
 *
 * Floor = sourceHtml re-rendered in Chrome ↔ Figma PNG (MCP rasterisation noise).
 */
import fs from 'node:fs'
import path from 'node:path'
import { chromium } from 'playwright'
import {
  PATHS,
  PARITY_CLOCK,
  SCREENS,
  resolveFigmaPng,
} from './config.js'
import { startParityServer } from './lib/server.js'
import { clockInitScript } from './lib/clock.js'
import {
  installParityMocks,
  sessionInitScript,
  guestSessionInitScript,
  themeInitScript,
} from './lib/mocks.js'
import { compareImages, realPercent } from './lib/diff.js'
import { screenshotSourceHtml } from './lib/sourceShot.js'

/** Mode (a): real vs HTML must be exactly 0% (no ε). Float noise only. */
const HTML_PASS_EPS = 0.00005
/** Soft ceiling when floor is missing — ~0.75% typical MCP noise. */
const PNG_FLOOR_FALLBACK = 0.75
/** Mode (b): PNG may sit at the floor; tiny float slack only. */
const PNG_PASS_EPS = 0.00005

function usage() {
  console.error(`Usage: yarn parity <screen-id>
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
  const context = await browser.newContext({
    viewport: screen.viewport,
    deviceScaleFactor: screen.deviceScaleFactor || 1,
    colorScheme: theme === 'dark' ? 'dark' : 'light',
  })
  const page = await context.newPage()

  await page.addInitScript(clockInitScript(PARITY_CLOCK))
  await page.addInitScript(
    screen.guest
      ? guestSessionInitScript()
      : sessionInitScript('priya.nair@example.com'),
  )
  await page.addInitScript(themeInitScript(theme))

  await installParityMocks(page, { fixture: screen.fixture || screen.id })

  const url = `${origin}${screen.route}`
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {})
  await page.waitForTimeout(1500)

  // Optional field fills (e.g. Figma sample email/password on login)
  if (screen.fills) {
    for (const [selector, value] of Object.entries(screen.fills)) {
      const loc = page.locator(selector).first()
      if ((await loc.count()) > 0) {
        await loc.fill(String(value))
      }
    }
    // Match Figma capture: email field focused with primary ring
    const email = page.locator('#login_email').first()
    if ((await email.count()) > 0) {
      await email.focus()
    }
  }

  await page.evaluate(async () => {
    if (document.fonts?.ready) await document.fonts.ready
  })
  await page.waitForTimeout(400)

  const shotPath = path.join(
    PATHS.artifacts,
    `_tmp-${screen.id}-${theme}-built.png`,
  )
  fs.mkdirSync(PATHS.artifacts, { recursive: true })
  await page.screenshot({
    path: shotPath,
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
  const tripletPath = path.join(PATHS.artifacts, `${screen.id}-${theme}.png`)

  const result = compareImages({
    builtPath: shotPath,
    figmaPath,
    outTripletPath: tripletPath,
    masks,
    shellRegions: screen.shellRegions || [],
  })

  // Mode (a)+(b): render source HTML as second reference
  let realVsHtmlPct = null
  let floorPct = null
  let srcPath = null
  if (screen.sourceHtml?.[theme]) {
    srcPath = path.join(
      PATHS.artifacts,
      `_tmp-${screen.id}-${theme}-source.png`,
    )
    await screenshotSourceHtml({
      browser,
      htmlFile: screen.sourceHtml[theme],
      theme,
      viewport: screen.viewport,
      outPath: srcPath,
    })
    // (a) Vue built ↔ source HTML (same engine) — must be ~0
    realVsHtmlPct = realPercent(shotPath, srcPath, masks)
    // Floor: source HTML ↔ Figma PNG
    floorPct = realPercent(srcPath, figmaPath, masks)
    // Keep HTML↔Vue diff artifact for debugging
    const htmlTriplet = path.join(
      PATHS.artifacts,
      `${screen.id}-${theme}-vs-html.png`,
    )
    compareImages({
      builtPath: shotPath,
      figmaPath: srcPath,
      outTripletPath: htmlTriplet,
      masks,
      shellRegions: [],
    })
  }

  const realVsPngPct = result.realPct
  const floorLimit = floorPct != null ? floorPct : PNG_FLOOR_FALLBACK
  const passA = realVsHtmlPct != null ? realVsHtmlPct <= HTML_PASS_EPS : false
  const passB = realVsPngPct <= floorLimit + PNG_PASS_EPS
  const pass = passA && passB

  // Legacy shell metrics (still useful for shell-owned crops)
  let shellSourceFloorPct = floorPct
  let shellAttributablePct =
    floorPct != null
      ? Math.max(0, result.shellRealPct - floorPct)
      : result.shellRealPct

  try {
    if (srcPath) fs.unlinkSync(srcPath)
  } catch {
    /* keep */
  }
  try {
    fs.unlinkSync(shotPath)
  } catch {
    /* keep */
  }

  return {
    screen: screen.id,
    theme,
    ...result,
    realVsHtmlPct,
    realVsPngPct,
    floorPct,
    pass,
    passA,
    passB,
    shellSourceFloorPct,
    shellAttributablePct,
    masked: masks.map((m) => m.name),
    remaining: pass
      ? '—'
      : [
          !passA
            ? `real vs HTML ${fmt(realVsHtmlPct)} > ${HTML_PASS_EPS}%`
            : null,
          !passB
            ? `real vs PNG ${fmt(realVsPngPct)} > floor ${fmt(floorLimit)}`
            : null,
        ]
          .filter(Boolean)
          .join('; '),
  }
}

function fmt(pct) {
  if (pct == null || Number.isNaN(pct)) return '—'
  return `${pct.toFixed(4)}%`
}

function printTable(rows) {
  const lines = [
    '| screen | theme | real vs HTML % | real vs PNG % | floor % | pass | masked | remaining |',
    '|---|---|---:|---:|---:|---|---|---|',
  ]
  for (const r of rows) {
    lines.push(
      `| ${r.screen} | ${r.theme} | ${fmt(r.realVsHtmlPct)} | ${fmt(r.realVsPngPct)} | ${fmt(r.floorPct)} | ${r.pass ? 'yes' : 'no'} | ${(r.masked || []).join('; ') || '—'} | ${r.remaining || '—'} |`,
    )
  }
  return lines.join('\n')
}

async function main() {
  const screenId = process.argv[2]
  if (!screenId || screenId.startsWith('-')) usage()
  const screen = SCREENS[screenId]
  if (!screen) {
    console.error(`Unknown screen "${screenId}"`)
    usage()
  }

  if (!fs.existsSync(path.join(PATHS.dist, 'index.html'))) {
    console.error('Production build missing. Run: cd frontend && yarn build')
    process.exit(1)
  }

  fs.mkdirSync(PATHS.artifacts, { recursive: true })

  const themes = ['light', 'dark']
  const results = []

  const chromePath = [
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
  ].find((p) => fs.existsSync(p))

  for (const theme of themes) {
    const server = await startParityServer({
      distDir: PATHS.dist,
      theme,
    })
    const browser = await chromium.launch({
      headless: true,
      executablePath: chromePath,
      args: ['--font-render-hinting=none', '--disable-lcd-text', '--no-sandbox'],
    })
    try {
      const row = await runTheme({
        screen,
        theme,
        origin: server.origin,
        browser,
      })
      results.push(row)
      console.log(
        `[parity] ${screen.id}/${theme}: vsHtml=${fmt(row.realVsHtmlPct)} vsPng=${fmt(row.realVsPngPct)} floor=${fmt(row.floorPct)} pass=${row.pass}`,
      )
    } finally {
      await browser.close()
      await server.close()
    }
  }

  const report = {
    clock: PARITY_CLOCK,
    generatedAt: new Date().toISOString(),
    note: 'Pass: (a) real vs source HTML ≤ 0.05%; (b) real vs PNG ≤ floor (sourceHtml↔PNG).',
    results,
  }
  const jsonPath = path.join(PATHS.artifacts, `${screenId}-report.json`)
  const mdPath = path.join(PATHS.artifacts, `${screenId}-report.md`)
  fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2))
  const md = [
    `# Parity — ${screenId}`,
    '',
    `Frozen clock: \`${PARITY_CLOCK}\``,
    '',
    printTable(results),
    '',
    '## Pass bar',
    '',
    '- **(a) real vs HTML %** — Vue build ↔ `p-*.html` in Chrome (same viewport/fixtures/clock). Target: **0%**.',
    '- **(b) real vs PNG %** — Vue build ↔ Figma PNG. Must be **≤ floor** (~0.75% MCP noise).',
    '- **floor %** — source HTML ↔ Figma PNG (same engine as Vue).',
    '- Full-page mask: only the design-only **Example data** tag (login has none).',
    '',
  ].join('\n')
  fs.writeFileSync(mdPath, md)
  console.log('\n' + md)
  console.log(`Wrote ${jsonPath}`)
  console.log(`Wrote ${mdPath}`)

  const fail = results.some((r) => !r.pass)
  process.exit(fail ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
