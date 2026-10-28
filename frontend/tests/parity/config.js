/**
 * Parity harness config — TEST ONLY. Never imported by production src/.
 *
 * Clock: Figma HTML shows “Today” / “28 Oct” on the leads list capture day.
 * Freeze to 2026-10-28T11:00:00+05:30 (IST) to match design relative dates.
 */
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const FRONTEND = join(HERE, '../..')
const REPO = join(FRONTEND, '..')

export const PARITY_CLOCK = '2026-10-28T11:00:00+05:30'

export const PATHS = {
  frontend: FRONTEND,
  repo: REPO,
  dist: join(REPO, 'crm/public/frontend'),
  figmaDir: join(HERE, 'figma'),
  figmaFallback: '/tmp/crm-figma-v1-all',
  /** Exact HTML/CSS the Figma MCP capture used (from uploads/crm-figma-src.tgz). */
  figmaSrc: '/tmp/crm-figma-src/figma-crm',
  artifacts: '/opt/cursor/artifacts/parity',
  fixtures: join(HERE, 'fixtures'),
  screens: join(HERE, 'screens'),
}

/** Desktop captures are 1440×960 (crm.css .app). Mobile m* are 390×844. */
export const SCREENS = {
  '04-leads-list': {
    id: '04-leads-list',
    route: '/crm/leads/view/list',
    /** Source HTML captured into the Figma PNG (same basename as p-*.html). */
    sourceHtml: {
      light: 'p-04-leads-list-light.html',
      dark: 'p-04-leads-list-dark.html',
    },
    figma: {
      light: '04-leads-list-light.png',
      dark: '04-leads-list-dark.png',
    },
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 1,
    /** Design-only tag; only this box is masked in the full-page diff. */
    masks: [
      {
        name: 'Example data tag',
        // Approximate box from p-04 ph2 row (right side before New lead).
        // Harness also tries [data-parity-mask="example-data"] if present.
        selector: '[data-parity-mask="example-data"]',
        fallback: { x: 1188, y: 70, width: 118, height: 28 },
      },
    ],
    /** Regions owned by the shell agent — driven to 0% real difference. */
    shellRegions: [
      { name: 'nav', x: 0, y: 0, width: 240, height: 960 },
      { name: 'app-bar', x: 240, y: 0, width: 1200, height: 52 },
    ],
    fixture: '04-leads-list',
  },
  '17-reports-edit': {
    id: '17-reports-edit',
    route: '/crm/reports?parityModal=edit',
    sourceHtml: {
      light: 'p-17-reports-edit-light.html',
      dark: 'p-17-reports-edit-dark.html',
    },
    figma: {
      light: '17-reports-edit-light.png',
      dark: '17-reports-edit-dark.png',
    },
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 1,
    /** Fixed PNG pass bar (Vijay): ≤ 0.75% real vs PNG. */
    pngMaxPct: 0.75,
    masks: [
      {
        name: 'Example data tag',
        selector: '[data-parity-mask="example-data"]',
        fallback: { x: 1188, y: 95, width: 118, height: 28 },
      },
    ],
    fixture: '17-reports-edit',
  },
  '18-reports-add-tile': {
    id: '18-reports-add-tile',
    route: '/crm/reports?parityModal=add',
    sourceHtml: {
      light: 'p-18-reports-add-tile-light.html',
      dark: 'p-18-reports-add-tile-dark.html',
    },
    figma: {
      light: '18-reports-add-tile-light.png',
      dark: '18-reports-add-tile-dark.png',
    },
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 1,
    pngMaxPct: 0.75,
    masks: [
      {
        name: 'Example data tag',
        selector: '[data-parity-mask="example-data"]',
        fallback: { x: 1188, y: 95, width: 118, height: 28 },
      },
    ],
    fixture: '17-reports-edit',
  },
  '19-reports-kpi-builder': {
    id: '19-reports-kpi-builder',
    route: '/crm/reports?parityModal=kpi',
    sourceHtml: {
      light: 'p-19-reports-kpi-builder-light.html',
      dark: 'p-19-reports-kpi-builder-dark.html',
    },
    figma: {
      light: '19-reports-kpi-builder-light.png',
      dark: '19-reports-kpi-builder-dark.png',
    },
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 1,
    pngMaxPct: 0.75,
    masks: [
      {
        name: 'Example data tag',
        selector: '[data-parity-mask="example-data"]',
        fallback: { x: 1188, y: 95, width: 118, height: 28 },
      },
    ],
    fixture: '17-reports-edit',
  },
  '20-reports-chart-builder': {
    id: '20-reports-chart-builder',
    route: '/crm/reports?parityModal=chart',
    sourceHtml: {
      light: 'p-20-reports-chart-builder-light.html',
      dark: 'p-20-reports-chart-builder-dark.html',
    },
    figma: {
      light: '20-reports-chart-builder-light.png',
      dark: '20-reports-chart-builder-dark.png',
    },
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 1,
    pngMaxPct: 0.75,
    masks: [
      {
        name: 'Example data tag',
        selector: '[data-parity-mask="example-data"]',
        fallback: { x: 1188, y: 95, width: 118, height: 28 },
      },
    ],
    fixture: '17-reports-edit',
  },
}

export function resolveFigmaPng(screenId, theme) {
  const screen = SCREENS[screenId]
  if (!screen) throw new Error(`Unknown screen: ${screenId}`)
  const name = screen.figma[theme]
  if (!name) throw new Error(`No figma png for ${screenId}/${theme}`)
  return name
}
