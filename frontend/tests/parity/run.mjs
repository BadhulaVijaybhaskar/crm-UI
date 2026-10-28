#!/usr/bin/env node
/**
 * yarn parity <screen>
 *
 * TEST-ONLY pixel-parity harness. Serves the production Vite build, mocks
 * Frappe APIs from fixtures/, freezes Date, screenshots at Figma size, and
 * writes built|figma|diff triplets under /opt/cursor/artifacts/parity/.
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
import { compareImages } from './lib/diff.js'

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
  await page.addInitScript(sessionInitScript('priya.nair@example.com'))
  await page.addInitScript(themeInitScript(theme))

  await installParityMocks(page, { fixture: screen.fixture || screen.id })

  const url = `${origin}${screen.route}`
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {})
  // Allow Vue + fonts to settle
  await page.waitForTimeout(1500)
  await page.evaluate(async () => {
    if (document.fonts?.ready) await document.fonts.ready
  })
  await page.waitForTimeout(400)

  // Force exact viewport clip (crm.css .app is 1440×960)
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

  try {
    fs.unlinkSync(shotPath)
  } catch {
    /* keep */
  }

  return {
    screen: screen.id,
    theme,
    ...result,
    masked: masks.map((m) => m.name),
  }
}

function fmt(pct) {
  return `${pct.toFixed(4)}%`
}

function printTable(rows) {
  const lines = [
    '| screen | theme | raw % | real % (1px/0.1) | shell real % | masked | triplet |',
    '|---|---|---:|---:|---:|---|---|',
  ]
  for (const r of rows) {
    lines.push(
      `| ${r.screen} | ${r.theme} | ${fmt(r.rawPct)} | ${fmt(r.realPct)} | ${fmt(r.shellRealPct)} | ${(r.masked || []).join('; ') || '—'} | \`${r.tripletPath}\` |`,
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

  for (const theme of themes) {
    const server = await startParityServer({
      distDir: PATHS.dist,
      theme,
    })
    const browser = await chromium.launch({
      headless: true,
      args: ['--font-render-hinting=none', '--disable-lcd-text'],
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
        `[parity] ${screen.id}/${theme}: raw=${fmt(row.rawPct)} real=${fmt(row.realPct)} shellReal=${fmt(row.shellRealPct)}`,
      )
    } finally {
      await browser.close()
      await server.close()
    }
  }

  const report = {
    clock: PARITY_CLOCK,
    generatedAt: new Date().toISOString(),
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
    '- **shell real %** crops nav (240×960) + app bar (1200×52) — shell agent target is 0%.',
    '- Page-content differences remain until screen agents restyle list/record pages.',
    '',
  ].join('\n')
  fs.writeFileSync(mdPath, md)
  console.log('\n' + md)
  console.log(`Wrote ${jsonPath}`)
  console.log(`Wrote ${mdPath}`)

  const shellFail = results.some((r) => r.shellRealPct > 0.0001)
  process.exit(shellFail ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
