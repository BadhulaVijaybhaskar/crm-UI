/**
 * Parity harness config — TEST ONLY. Never imported by production src/.
 *
 * Clock: Figma HTML shows “Today” / “28 Oct” on the leads list capture day.
 * Freeze to 2026-10-28T11:00:00+05:30 (IST) to match design relative dates.
 *
 * p-*.html under PATHS.figmaSrc and PNGs under figma/ are READ-ONLY references.
 * Never edit them to close a parity diff. Where HTML layout disagrees with the
 * PNG, match the PNG (approved design).
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

const EXAMPLE_DATA_MASK = (fallback) => ({
  name: 'Example data tag',
  selector: '[data-parity-mask="example-data"]',
  fallback,
})

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
    masks: [EXAMPLE_DATA_MASK({ x: 1188, y: 70, width: 118, height: 28 })],
    /** Regions owned by the shell agent. */
    shellRegions: [
      { name: 'nav', x: 0, y: 0, width: 240, height: 960 },
      { name: 'app-bar', x: 240, y: 0, width: 1200, height: 52 },
    ],
    fixture: '04-leads-list',
  },
  '21-settings-stages': {
    id: '21-settings-stages',
    route: '/crm/settings/pipeline-stages',
    sessionEmail: 'priya.n@example.in',
    sourceHtml: {
      light: 'p-21-settings-stages-light.html',
      dark: 'p-21-settings-stages-dark.html',
    },
    figma: {
      light: '21-settings-stages-light.png',
      dark: '21-settings-stages-dark.png',
    },
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 1,
    // Concept banner pushes Example data down (~y 112). Shell is unmasked —
    // ui/astra-v3-shell@597276c8 owns nav + app-bar and must pass in-frame.
    masks: [EXAMPLE_DATA_MASK({ x: 1115, y: 112, width: 95, height: 24 })],
    fixture: '21-settings',
  },
  '22-settings-users': {
    id: '22-settings-users',
    route: '/crm/settings/users',
    sessionEmail: 'priya.n@example.in',
    sourceHtml: {
      light: 'p-22-settings-users-light.html',
      dark: 'p-22-settings-users-dark.html',
    },
    figma: {
      light: '22-settings-users-light.png',
      dark: '22-settings-users-dark.png',
    },
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 1,
    masks: [EXAMPLE_DATA_MASK({ x: 1028, y: 82, width: 97, height: 24 })],
    fixture: '21-settings',
  },
  '23-settings-fields': {
    id: '23-settings-fields',
    route: '/crm/settings/fields-layout',
    sessionEmail: 'priya.n@example.in',
    sourceHtml: {
      light: 'p-23-settings-fields-light.html',
      dark: 'p-23-settings-fields-dark.html',
    },
    figma: {
      light: '23-settings-fields-light.png',
      dark: '23-settings-fields-dark.png',
    },
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 1,
    masks: [EXAMPLE_DATA_MASK({ x: 1130, y: 82, width: 95, height: 24 })],
    fixture: '21-settings',
  },
}

export function resolveFigmaPng(screenId, theme) {
  const screen = SCREENS[screenId]
  if (!screen) throw new Error(`Unknown screen: ${screenId}`)
  const name = screen.figma[theme]
  if (!name) throw new Error(`No figma png for ${screenId}/${theme}`)
  return name
}
