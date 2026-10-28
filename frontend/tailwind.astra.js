/**
 * Astra CRM — Tailwind 3 theme extension. Merge into frontend/tailwind.config.js:
 *
 *   import astra from './tailwind.astra.js'
 *   export default { presets: [/* existing UI-kit preset */], …, theme: { extend: astra.extend } }
 *
 * Classes are prefixed `crm-` so they never shadow the UI-kit preset names (gray, ink-*, surface-*, outline-*).
 * Dark mode needs no `dark:` variants: the CSS variables in astra-crm-tokens.css swap under [data-theme="dark"].
 */
const v = (name) => `var(--crm-${name})`
const colors = [
  'bg', 'card', 'muted', 'border', 'border-strong', 'neutral-soft', 'row-hover', 'row-selected',
  'fg', 'muted-fg', 'faint',
  'primary', 'primary-hover', 'primary-soft', 'primary-fg', 'ring',
  'blue', 'blue-soft', 'teal', 'teal-soft',
  'success', 'success-soft', 'warning', 'warning-soft', 'danger', 'danger-soft',
  'nav', 'nav-fg', 'nav-faint', 'nav-active', 'nav-border', 'nav-indicator',
  'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'bulk-bg', 'bulk-fg',
]

export default {
  extend: {
    colors: { crm: Object.fromEntries(colors.map((c) => [c, v(c)])) },
    fontSize: {
      // [size, lineHeight]
      'crm-caps': ['10.5px', '1.3'],    // section labels: 700, uppercase, tracking .06em
      'crm-micro': ['11px', '1.35'],    // counts, times, chip-mini
      'crm-meta': ['11.5px', '1.4'],    // table headers, sub lines, chips
      'crm-label': ['12.5px', '1.45'],  // table cells, buttons-sm, form inputs
      'crm-body': ['13px', '1.45'],     // base, nav items, buttons
      'crm-panel': ['14px', '1.35'],    // panel titles (600)
      'crm-dialog': ['15px', '1.3'],    // modal titles (600)
      'crm-record': ['19px', '1.2'],    // record header name (600, -0.015em)
      'crm-page': ['20px', '1.2'],      // page header h1 (600, -0.015em)
      'crm-kpi': ['24px', '1.1'],       // KPI numbers (600, -0.02em)
      'crm-tile': ['26px', '1.1'],      // dashboard tile big number (600, -0.02em)
    },
    letterSpacing: { 'crm-caps': '0.06em', 'crm-tight': '-0.015em', 'crm-num': '-0.02em' },
    spacing: {
      'crm-nav': '240px',        // left nav width
      'crm-appbar': '52px',      // app bar height
      'crm-search': '420px',     // global search width
      'crm-control': '34px',     // button / search height
      'crm-control-sm': '28px',  // small button, filter chip
      'crm-input': '32px',       // form input height
      'crm-chip': '22px',
      'crm-th': '34px',
      'crm-td': '44px',
      'crm-navitem': '32px',
      'crm-side': '340px',       // record right column
      'crm-settings-nav': '220px',
      'crm-kanban-col': '258px',
      'crm-page-x': '24px',      // page side padding
    },
    borderRadius: {
      'crm-mini': '4px',
      'crm-tag': '5px',
      'crm-chip': '6px',
      'crm-control-sm': '7px',
      'crm-control': '8px',
      'crm-card': '8px',         // kanban card, timeline card
      'crm-rail': '9px',         // milestone rail group, composer, bulk bar, option card
      'crm-panel': '10px',       // panels, KPI, dashboard tile, kanban column
      'crm-modal': '12px',
    },
    boxShadow: {
      'crm-focus': v('focus'),
      'crm-input-focus': v('input-focus'),
      'crm-modal': v('shadow-modal'),
      'crm-drag': v('shadow-drag'),
      'crm-tile-drag': v('shadow-tile-drag'),
      'crm-bulk': v('shadow-bulk'),
      'crm-nav-active': 'inset 3px 0 0 var(--crm-nav-indicator)',
      'crm-selected': '0 0 0 2px var(--crm-primary)',
    },
    gridTemplateColumns: {
      'crm-record': '1fr 340px',
      'crm-settings': '220px 1fr',
      'crm-conversations': '330px 1fr 300px',
      'crm-timeline': '30px 1fr',
      'crm-dashboard': 'repeat(12, minmax(0, 1fr))',
    },
    gridAutoRows: { 'crm-dashboard': '92px' },
  },
}
