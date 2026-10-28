#!/usr/bin/env node
/**
 * yarn parity <screen>
 *
 * TEST-ONLY pixel-parity harness. Serves the production Vite build, mocks
 * Frappe APIs from fixtures/, freezes Date, screenshots at Figma size, and
 * writes dual triplets under /opt/cursor/artifacts/parity/:
 *   <screen>-<theme>-vs-html.png  — built | source HTML | diff
 *   <screen>-<theme>-vs-png.png   — built | Figma PNG  | diff
 *
 * Pass bar (full page after Example-data mask; shellRegions optional):
 *   (a) real vs unedited HTML === 0% on pixels where HTML agrees with PNG
 *   (b) real vs PNG ≤ 0.75%
 *
 * p-*.html and Figma PNGs are READ-ONLY. Never edit them to close a diff.
 * Where HTML layout disagrees with the PNG, the PNG is the approved design.
 *
 * Nothing here is imported by production src/.
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
import {
  compareImages,
  htmlAgreementRealPercent,
  shellRealPercent,
} from './lib/diff.js'
import { screenshotSourceHtml } from './lib/sourceShot.js'

/** (a) Vue vs HTML on HTML∩PNG agreement must be exactly 0. */
const HTML_PASS_EPS = 1e-9
/** (b) Vue vs PNG hard ceiling (design floor ≈ 0.75%). */
const PNG_PASS_MAX = 0.75

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

async function screenshotBuilt({ page, screen, theme }) {
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
  return shotPath
}

async function runTheme({ screen, theme, origin, browser }) {
  const context = await browser.newContext({
    viewport: screen.viewport,
    deviceScaleFactor: screen.deviceScaleFactor || 1,
    colorScheme: theme === 'dark' ? 'dark' : 'light',
  })
  const page = await context.newPage()

  const sessionEmail =
    screen.sessionEmail || 'priya.nair@example.com'
  await page.addInitScript(clockInitScript(PARITY_CLOCK))
  await page.addInitScript(sessionInitScript(sessionEmail))
  await page.addInitScript(themeInitScript(theme))

  await installParityMocks(page, { fixture: screen.fixture || screen.id })

  const url = `${origin}${screen.route}`
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {})
  await page.waitForTimeout(1500)
  await page.evaluate(async () => {
    if (document.fonts?.ready) await document.fonts.ready
  })
  await page.waitForTimeout(400)

  const builtPath = await screenshotBuilt({ page, screen, theme })
  const masks = await resolveMasks(page, screen)
  await context.close()

  const figmaPath = findFigma(resolveFigmaPng(screen.id, theme))
  const shellRegions = screen.shellRegions || []
  const hasShell = shellRegions.length > 0

  if (!screen.sourceHtml?.[theme]) {
    throw new Error(
      `Screen ${screen.id} missing sourceHtml.${theme} — required (read-only p-*.html)`,
    )
  }

  const htmlFile = screen.sourceHtml[theme]
  const htmlSrcPath = path.join(PATHS.figmaSrc, htmlFile)
  if (!fs.existsSync(htmlSrcPath)) {
    throw new Error(
      `Read-only source HTML missing: ${htmlSrcPath}. Unpack uploads/crm-figma-src.tgz — do not invent or edit p-*.html.`,
    )
  }

  const htmlPath = path.join(
    PATHS.artifacts,
    `_tmp-${screen.id}-${theme}-source.png`,
  )
  await screenshotSourceHtml({
    browser,
    htmlFile,
    theme,
    viewport: screen.viewport,
    outPath: htmlPath,
  })

  const vsHtmlTriplet = path.join(
    PATHS.artifacts,
    `${screen.id}-${theme}-vs-html.png`,
  )
  const vsPngTriplet = path.join(
    PATHS.artifacts,
    `${screen.id}-${theme}-vs-png.png`,
  )

  const vsHtml = compareImages({
    builtPath,
    figmaPath: htmlPath,
    outTripletPath: vsHtmlTriplet,
    masks,
    shellRegions,
  })

  const vsPng = compareImages({
    builtPath,
    figmaPath,
    outTripletPath: vsPngTriplet,
    masks,
    shellRegions,
  })

  // Informational: HTML↔PNG floor (MCP raster / layout drift). Not the pass ceiling.
  const floorPct = hasShell
    ? shellRealPercent(htmlPath, figmaPath, shellRegions)
    : compareImages({
        builtPath: htmlPath,
        figmaPath,
        outTripletPath: path.join(
          PATHS.artifacts,
          `_tmp-${screen.id}-${theme}-floor-triplet.png`,
        ),
        masks,
        shellRegions: [],
      }).realPct

  // Reported numbers: full-page (or shell crop when configured) real %.
  const realVsHtmlPct = hasShell ? vsHtml.shellRealPct : vsHtml.realPct
  const realVsPngPct = hasShell ? vsPng.shellRealPct : vsPng.realPct

  // Pass (a): Vue vs HTML only where unedited HTML agrees with PNG.
  const agreed = htmlAgreementRealPercent({
    builtPath,
    htmlPath,
    pngPath: figmaPath,
    masks,
    shellRegions,
  })
  const realVsHtmlAgreedPct = agreed.realVsHtmlAgreedPct

  const passA = realVsHtmlAgreedPct <= HTML_PASS_EPS
  const passB = realVsPngPct <= PNG_PASS_MAX
  const pass = passA && passB

  const remainingParts = []
  if (!passA) {
    remainingParts.push(
      `HTML-agree ${realVsHtmlAgreedPct.toFixed(4)}% (need 0)`,
    )
  }
  if (!passB) {
    remainingParts.push(
      `PNG ${realVsPngPct.toFixed(4)}% (need ≤ ${PNG_PASS_MAX})`,
    )
  }
  const remaining = remainingParts.length ? remainingParts.join('; ') : '—'

  for (const p of [builtPath, htmlPath]) {
    try {
      fs.unlinkSync(p)
    } catch {
      /* keep */
    }
  }
  try {
    fs.unlinkSync(
      path.join(PATHS.artifacts, `_tmp-${screen.id}-${theme}-floor-triplet.png`),
    )
  } catch {
    /* keep */
  }

  return {
    screen: screen.id,
    theme,
    realVsHtmlPct,
    realVsHtmlAgreedPct,
    realVsPngPct,
    floorPct,
    pass,
    passA,
    passB,
    masked: masks.map((m) => m.name),
    remaining,
    htmlPngDisagreePx: agreed.htmlPngDisagree,
    agreeTotal: agreed.agreeTotal,
    shell: {
      vsHtml: vsHtml.shell,
      vsPng: vsPng.shell,
    },
    tripletVsHtml: vsHtmlTriplet,
    tripletVsPng: vsPngTriplet,
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
      `| ${r.screen} | ${r.theme} | ${fmt(r.realVsHtmlPct)} | ${fmt(r.realVsPngPct)} | ${fmt(r.floorPct)} | ${r.pass ? 'yes' : 'no'} | ${(r.masked || []).join('; ') || '—'} | ${r.remaining} |`,
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
        `[parity] ${screen.id}/${theme}: vsHTML=${fmt(row.realVsHtmlPct)} (agree ${fmt(row.realVsHtmlAgreedPct)}) vsPNG=${fmt(row.realVsPngPct)} floor=${fmt(row.floorPct)} pass=${row.pass}`,
      )
    } finally {
      await browser.close()
      await server.close()
    }
  }

  const report = {
    clock: PARITY_CLOCK,
    generatedAt: new Date().toISOString(),
    passBar: {
      a: 'real vs unedited HTML === 0% on pixels where HTML agrees with PNG',
      b: `real vs PNG ≤ ${PNG_PASS_MAX}%`,
      refs: 'p-*.html and Figma PNGs are read-only; PNG wins on layout disagreement',
    },
    results,
  }
  const jsonPath = path.join(PATHS.artifacts, `${screenId}-report.json`)
  const mdPath = path.join(PATHS.artifacts, `${screenId}-report.md`)
  fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2))

  const tripletLines = results.flatMap((r) => [
    `- \`${r.tripletVsHtml}\` (built | HTML | diff)`,
    `- \`${r.tripletVsPng}\` (built | PNG | diff)`,
  ])

  const md = [
    `# Parity — ${screenId}`,
    '',
    `Frozen clock: \`${PARITY_CLOCK}\``,
    '',
    printTable(results),
    '',
    '## Triplets',
    '',
    ...tripletLines,
    '',
    '## Notes',
    '',
    '- **real vs HTML %** — Vue vs unedited capture HTML in Chrome (reported).',
    '- **pass (a)** — same comparison restricted to pixels where HTML **agrees** with the PNG must be **0%**.',
    `- **real vs PNG %** — Vue vs Figma PNG; pass (b) requires ≤ **${PNG_PASS_MAX}%**.`,
    '- **floor %** — HTML in Chrome vs PNG (informational MCP/layout drift).',
    '- Refs (`p-*.html`, PNGs) are **read-only**. Where HTML layout disagrees with PNG, match the PNG.',
    '- Full-page mask: only the design-only **Example data** tag box.',
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
