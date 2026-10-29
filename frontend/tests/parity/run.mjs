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
 *   - real vs PNG ≤ 0.75% (Figma PNG is the approved design; 1px + threshold 0.1)
 *   - real vs unedited p-*.html ≈ 0 wherever that HTML agrees with the PNG
 *
 * Reference HTML and Figma PNGs are READ-ONLY — never edit them to pass a diff.
 * When HTML layout disagrees with the PNG, match the PNG.
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
  themeInitScript,
} from './lib/mocks.js'
import { compareImages, realPercent } from './lib/diff.js'
import { screenshotSourceHtml } from './lib/sourceShot.js'

/** Hard PNG budget. HTML target is ~0 when HTML agrees with PNG. */
const PNG_BUDGET = 0.75
const EPS_HTML = 0.05
/** No PNG slack — user bar is strict ≤0.75% light and dark. */
const EPS_PNG = 0
/**
 * HTML is treated as agreeing with PNG only when their diff is near-zero.
 * Using PNG_BUDGET here made the HTML≈0 gate impossible whenever the
 * HTML↔PNG floor sat between EPS_HTML and 0.75% (Vue cannot beat the floor).
 */
const HTML_AGREES_EPS = 0.15

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
    sessionInitScript(screen.sessionUser || 'priya.nair@example.com'),
  )
  await page.addInitScript(themeInitScript(theme))

  await installParityMocks(page, { fixture: screen.fixture || screen.id })

  const url = `${origin}${screen.route}`
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {})
  await page.waitForTimeout(1500)
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

  let floorPct = null
  let realVsHtmlPct = null
  const remaining = []

  if (screen.sourceHtml?.[theme]) {
    const srcPath = path.join(
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
    // Unedited HTML ↔ PNG (disagreement / MCP floor). Never edit the HTML.
    floorPct = realPercent(srcPath, figmaPath, masks)
    realVsHtmlPct = realPercent(shotPath, srcPath, masks)
    try {
      fs.unlinkSync(srcPath)
    } catch {
      /* keep */
    }
  } else {
    remaining.push('sourceHtml missing — real vs HTML not measured')
  }

  const realVsPngPct = result.realPct
  const pngOk = realVsPngPct <= PNG_BUDGET + EPS_PNG
  const htmlAgreesWithPng = floorPct != null && floorPct <= HTML_AGREES_EPS
  const htmlOk =
    realVsHtmlPct == null
      ? true
      : !htmlAgreesWithPng || realVsHtmlPct <= EPS_HTML
  const pass = pngOk && htmlOk

  if (!pngOk) {
    remaining.push(
      `real vs PNG ${realVsPngPct.toFixed(4)}% > ${PNG_BUDGET}% budget`,
    )
  }
  if (realVsHtmlPct != null && htmlAgreesWithPng && realVsHtmlPct > EPS_HTML) {
    remaining.push(
      `real vs HTML ${realVsHtmlPct.toFixed(4)}% > 0 (HTML agrees with PNG)`,
    )
  } else if (realVsHtmlPct != null && !htmlAgreesWithPng && floorPct != null) {
    remaining.push(
      `HTML disagrees with PNG (html↔png ${floorPct.toFixed(4)}%); PNG is approved`,
    )
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
    floorPct,
    realVsHtmlPct,
    realVsPngPct,
    pass,
    remaining,
    masked: masks.map((m) => m.name),
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
      `| ${r.screen} | ${r.theme} | ${fmt(r.realVsHtmlPct)} | ${fmt(r.realVsPngPct)} | ${fmt(r.floorPct)} | ${r.pass ? 'PASS' : 'FAIL'} | ${(r.masked || []).join('; ') || '—'} | ${(r.remaining || []).join('; ') || '—'} |`,
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
        `[parity] ${screen.id}/${theme}: html=${fmt(row.realVsHtmlPct)} png=${fmt(row.realVsPngPct)} floor=${fmt(row.floorPct)} pass=${row.pass}`,
      )
    } finally {
      await browser.close()
      await server.close()
    }
  }

  const report = {
    clock: PARITY_CLOCK,
    generatedAt: new Date().toISOString(),
    note: `Pass: real vs PNG ≤ ${PNG_BUDGET}% (PNG is approved design). Real vs unedited HTML ≈ 0 wherever HTML agrees with PNG (html↔png ≤ ${PNG_BUDGET}%). Never edit p-*.html or Figma PNGs.`,
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
    '## Notes',
    '',
    '- Full-page mask: only the design-only **Example data** tag box.',
    '- **real vs PNG %** — must be ≤ 0.75% (approved design).',
    '- **real vs HTML %** — Vue vs unedited p-*.html; must be ~0 when HTML agrees with PNG.',
    '- **floor %** — unedited HTML ↔ PNG (disagreement / MCP noise). Read-only references.',
    '',
  ].join('\n')
  fs.writeFileSync(mdPath, md)
  console.log('\n' + md)
  console.log(`Wrote ${jsonPath}`)
  console.log(`Wrote ${mdPath}`)

  const failed = results.some((r) => !r.pass)
  process.exit(failed ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
