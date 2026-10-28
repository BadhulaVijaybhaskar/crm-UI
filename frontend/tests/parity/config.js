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

/** Home / Work queue / Tasks etc. were captured at 11:42 IST ("Now · 11:42", "42 m late"). */
export const ACTIVITY_CLOCK = '2026-10-28T11:42:00+05:30'

/**
 * Pass bar (see README) — p-*.html and Figma PNGs are READ-ONLY:
 *  (a) real Vue-built vs unedited sourceHtml = 0 % on pixels where that HTML
 *      agrees with the PNG (PNG wins on layout disagreements)
 *  (b) real Vue-built vs Figma PNG           ≤ 0.75 %
 * floor % (HTML-in-Chrome vs PNG) is reported for context only.
 */
export const PASS = {
  /** (a) tolerance for "0 %" on the HTML∩PNG agreement set. */
  htmlEpsilonPct: 0.01,
  /** (b) absolute real-vs-PNG ceiling (light and dark). */
  pngMaxPct: 0.75,
  /** Informational nominal when sourceHtml is missing. */
  nominalFloorPct: 0.75,
}

export const DEFAULT_SESSION_USER = {
  email: 'priya.nair@example.com',
  fullName: 'Priya Nair',
}

const ROHAN = { email: 'rohan.mehta@example.com', fullName: 'Rohan Mehta' }
const DESKTOP = { width: 1440, height: 960 }
const MOBILE = { width: 390, height: 844 }

/** Padded boxes of the design-only "Example data" tag measured on the Figma PNGs. */
function exampleDataMask(box) {
  return [
    {
      name: 'Example data tag',
      selector: '[data-parity-mask="example-data"]',
      fallback: box,
    },
  ]
}

const NAV_AND_APP_BAR = [
  { name: 'nav', x: 0, y: 0, width: 240, height: 960 },
  { name: 'app-bar', x: 240, y: 0, width: 1200, height: 52 },
]

function activityScreen({
  id,
  route,
  slug,
  maskBox,
  viewport = DESKTOP,
  fixture = id,
  clock = ACTIVITY_CLOCK,
  shellRegions = NAV_AND_APP_BAR,
}) {
  return {
    id,
    route,
    sourceHtml: {
      light: `p-${slug}-light.html`,
      dark: `p-${slug}-dark.html`,
    },
    figma: { light: `${id}-light.png`, dark: `${id}-dark.png` },
    viewport,
    deviceScaleFactor: 1,
    masks: exampleDataMask(maskBox),
    shellRegions,
    fixture,
    clock,
    sessionUser: ROHAN,
  }
}

/** Desktop captures are 1440×960 (crm.css .app). Mobile m* are 390×844. */
export const SCREENS = {
  '02-home': activityScreen({
    id: '02-home',
    slug: '02-home',
    route: '/crm/dashboard',
    maskBox: { x: 1148, y: 81, width: 109, height: 26 },
  }),
  '03-work-queue': activityScreen({
    id: '03-work-queue',
    slug: '03-work-queue',
    route: '/crm/work-queue',
    maskBox: { x: 1308, y: 81, width: 109, height: 26 },
  }),
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
    viewport: DESKTOP,
    deviceScaleFactor: 1,
    /** Design-only tag; only this box is masked in the full-page diff. */
    masks: exampleDataMask({ x: 1197, y: 81, width: 109, height: 26 }),
    /** Regions owned by the shell agent. */
    shellRegions: NAV_AND_APP_BAR,
    fixture: '04-leads-list',
    clock: PARITY_CLOCK,
    sessionUser: DEFAULT_SESSION_USER,
  },
  '13-conversations': activityScreen({
    id: '13-conversations',
    slug: '13-conversations',
    route: '/crm/conversations',
    maskBox: { x: 1308, y: 81, width: 109, height: 26 },
  }),
  '14-tasks': activityScreen({
    id: '14-tasks',
    slug: '14-tasks',
    route: '/crm/tasks/view/list',
    maskBox: { x: 1196, y: 81, width: 109, height: 26 },
  }),
  '15-notes': activityScreen({
    id: '15-notes',
    slug: '15-notes',
    route: '/crm/notes/view/list',
    maskBox: { x: 1195, y: 81, width: 109, height: 26 },
  }),
  '16-call-logs': activityScreen({
    id: '16-call-logs',
    slug: '16-call-logs',
    route: '/crm/call-logs/view/list',
    maskBox: { x: 1196, y: 81, width: 109, height: 26 },
  }),
  'm1-home': activityScreen({
    id: 'm1-home',
    slug: 'm1-home',
    route: '/crm/dashboard',
    viewport: MOBILE,
    maskBox: { x: 268, y: 86, width: 109, height: 26 },
    shellRegions: [],
  }),
}

export function resolveFigmaPng(screenId, theme) {
  const screen = SCREENS[screenId]
  if (!screen) throw new Error(`Unknown screen: ${screenId}`)
  const name = screen.figma[theme]
  if (!name) throw new Error(`No figma png for ${screenId}/${theme}`)
  return name
}
