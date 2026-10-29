/**
 * Stroke icons copied from Figma capture HTML (p-*.html / app.css svg.i).
 * 16×16, stroke 1.75, round caps — keep in sync with design source, not Lucide.
 */
import { h } from 'vue'

const base = {
  xmlns: 'http://www.w3.org/2000/svg',
  fill: 'none',
  viewBox: '0 0 24 24',
  'stroke-width': '1.75',
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round',
  stroke: 'currentColor',
  'aria-hidden': 'true',
}

function icon(name, children) {
  const Comp = (props, { attrs }) => {
    const { class: attrClass, ...rest } = attrs
    // Default 16×16 via size-4 only when the caller does not set a size-*.
    // Never combine size-4 + size-3.5 — Tailwind order is stylesheet-order, not
    // class-list order, and the larger icon made the New button 2px too wide.
    const hasSize =
      typeof attrClass === 'string'
        ? /\bsize-/.test(attrClass)
        : Array.isArray(attrClass)
          ? attrClass.some((c) => typeof c === 'string' && /\bsize-/.test(c))
          : false
    return h(
      'svg',
      {
        ...base,
        ...rest,
        class: ['astra-nav-icon', hasSize ? null : 'size-4', attrClass],
      },
      children,
    )
  }
  Comp.displayName = name
  return Comp
}

const path = (...ds) => ds.map((d) => h('path', { d }))
const circle = (attrs) => h('circle', attrs)
const rect = (attrs) => h('rect', attrs)

export const FigmaHomeIcon = icon('FigmaHomeIcon', path('M3 10.5 12 3l9 7.5', 'M5 9.5V21h14V9.5', 'M10 21v-6h4v6'))

export const FigmaWorkQueueIcon = icon(
  'FigmaWorkQueueIcon',
  path('M3 6h18M3 12h12M3 18h7', 'm16 16 2 2 4-4'),
)

export const FigmaConversationsIcon = icon(
  'FigmaConversationsIcon',
  path(
    'M22 12h-6l-2 3h-4l-2-3H2',
    'M5.5 5.1 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.7 1.1z',
  ),
)

export const FigmaLeadsIcon = icon('FigmaLeadsIcon', [
  h('path', { d: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2' }),
  circle({ cx: '9', cy: '7', r: '4' }),
  h('path', { d: 'M22 21v-2a4 4 0 0 0-3-3.87' }),
  h('path', { d: 'M16 3.13a4 4 0 0 1 0 7.75' }),
])

export const FigmaDealsIcon = icon(
  'FigmaDealsIcon',
  path('M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6'),
)

export const FigmaContactsIcon = icon('FigmaContactsIcon', [
  circle({ cx: '12', cy: '8', r: '4' }),
  h('path', { d: 'M4 21a8 8 0 0 1 16 0' }),
])

export const FigmaCompaniesIcon = icon('FigmaCompaniesIcon', [
  rect({ x: '4', y: '3', width: '16', height: '18', rx: '1.5' }),
  h('path', { d: 'M9 7h1M14 7h1M9 11h1M14 11h1M9 15h1M14 15h1M10 21v-3h4v3' }),
])

export const FigmaTasksIcon = icon('FigmaTasksIcon', [
  rect({ x: '3', y: '3', width: '18', height: '18', rx: '2' }),
  h('path', { d: 'm8 12 3 3 5-6' }),
])

export const FigmaNotesIcon = icon(
  'FigmaNotesIcon',
  path('M15.5 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V8.5z', 'M15 3v6h6'),
)

export const FigmaCallLogsIcon = icon(
  'FigmaCallLogsIcon',
  path(
    'M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z',
  ),
)

export const FigmaReportsIcon = icon(
  'FigmaReportsIcon',
  path('M3 3v18h18', 'M8 17V11M13 17V7M18 17v-4'),
)

export const FigmaAICallingIcon = FigmaCallLogsIcon

export const FigmaMessagesIcon = icon(
  'FigmaMessagesIcon',
  path('M7.9 20A9 9 0 1 0 4 16.1L2 22Z'),
)

export const FigmaAIEmployeesIcon = icon('FigmaAIEmployeesIcon', [
  rect({ x: '4', y: '8', width: '16', height: '12', rx: '2' }),
  h('path', { d: 'M12 4v4M9 13v1M15 13v1M2 14h2M20 14h2' }),
])

export const FigmaSettingsIcon = icon('FigmaSettingsIcon', [
  circle({ cx: '12', cy: '12', r: '3' }),
  h('path', {
    d: 'M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z',
  }),
])

export const FigmaExternalIcon = icon(
  'FigmaExternalIcon',
  path('M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6'),
)

export const FigmaSearchIcon = icon(
  'FigmaSearchIcon',
  [
    circle({ cx: '11', cy: '11', r: '7' }),
    h('path', { d: 'm20 20-3.5-3.5' }),
  ],
)

export const FigmaBellIcon = icon(
  'FigmaBellIcon',
  path('M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9', 'M10.3 21a1.94 1.94 0 0 0 3.4 0'),
)

export const FigmaPlusIcon = icon('FigmaPlusIcon', path('M12 5v14M5 12h14'))

export const FigmaMoonIcon = icon(
  'FigmaMoonIcon',
  path('M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z'),
)

/** Dark-theme .tbtn glyph from p-*-dark.html */
export const FigmaSunIcon = icon('FigmaSunIcon', [
  circle({ cx: '12', cy: '12', r: '4' }),
  h('path', {
    d: 'M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4',
  }),
])
