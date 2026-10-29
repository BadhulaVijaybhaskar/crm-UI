/**
 * Parity harness config — TEST ONLY. Never imported by production src/.
 *
 * Clock: Figma HTML shows “Today” / “28 Oct” on the leads list capture day.
 * Freeze to 2026-10-28T11:00:00+05:30 (IST) to match design relative dates.
 *
 * Reference p-*.html and Figma PNGs are READ-ONLY — never edit them to pass.
 * When HTML layout disagrees with the PNG, the PNG is the approved design.
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

const DESKTOP = { width: 1440, height: 960 }
const MOBILE = { width: 390, height: 844 }

function exampleDataMask(fallback) {
  return [
    {
      name: 'Example data tag',
      selector: '[data-parity-mask="example-data"]',
      fallback,
    },
  ]
}

function screenEntry({
  id,
  route,
  viewport = DESKTOP,
  fixture,
  exampleFallback = { x: 1188, y: 70, width: 118, height: 28 },
  shellRegions,
  sessionUser = 'priya.nair@example.com',
}) {
  return {
    id,
    route,
    sourceHtml: {
      light: `p-${id}-light.html`,
      dark: `p-${id}-dark.html`,
    },
    figma: {
      light: `${id}-light.png`,
      dark: `${id}-dark.png`,
    },
    viewport,
    deviceScaleFactor: 1,
    masks: exampleDataMask(exampleFallback),
    shellRegions:
      shellRegions ||
      (viewport.width >= 1440
        ? [
            { name: 'nav', x: 0, y: 0, width: 240, height: viewport.height },
            {
              name: 'app-bar',
              x: 240,
              y: 0,
              width: viewport.width - 240,
              height: 52,
            },
          ]
        : []),
    fixture: fixture || id,
    sessionUser,
  }
}

/** Desktop captures are 1440×960 (crm.css .app). Mobile m* are 390×844. */
export const SCREENS = {
  '04-leads-list': screenEntry({
    id: '04-leads-list',
    route: '/crm/leads/view/list',
    fixture: '04-leads-list',
  }),
  '05-lead-record': screenEntry({
    id: '05-lead-record',
    route: '/crm/leads/LEAD-MI',
    fixture: '05-lead-record',
  }),
  '06-deals-board': screenEntry({
    id: '06-deals-board',
    route: '/crm/deals/view/kanban',
    fixture: '06-deals-board',
  }),
  '07-deals-list': screenEntry({
    id: '07-deals-list',
    route: '/crm/deals/view/list',
    fixture: '07-deals-list',
  }),
  '08-deal-record': screenEntry({
    id: '08-deal-record',
    route: '/crm/deals/DEAL-LL',
    fixture: '08-deal-record',
  }),
  '09-contacts-list': screenEntry({
    id: '09-contacts-list',
    route: '/crm/contacts/view/list',
    fixture: '09-contacts-list',
    // PNG/HTML nav foot is Rohan Mehta · Sales user (not Priya).
    sessionUser: 'rohan.mehta@example.com',
  }),
  '10-contact-record': screenEntry({
    id: '10-contact-record',
    route: '/crm/contacts/CONTACT-AK',
    fixture: '10-contact-record',
  }),
  '11-companies-list': screenEntry({
    id: '11-companies-list',
    route: '/crm/organizations/view/list',
    fixture: '11-companies-list',
  }),
  '12-company-record': screenEntry({
    id: '12-company-record',
    route: '/crm/organizations/ORG-LL',
    fixture: '12-company-record',
  }),
  'm2-deal-record': screenEntry({
    id: 'm2-deal-record',
    route: '/crm/deals/DEAL-LL',
    viewport: MOBILE,
    fixture: 'm2-deal-record',
    exampleFallback: { x: 280, y: 12, width: 100, height: 24 },
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
