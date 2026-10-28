import LucideHouse from '~icons/lucide/house'
import LucideListTodo from '~icons/lucide/list-todo'
import LucideMessagesSquare from '~icons/lucide/messages-square'
import LucideUsers from '~icons/lucide/users'
import LucideHandshake from '~icons/lucide/handshake'
import LucideContact from '~icons/lucide/contact'
import LucideBuilding2 from '~icons/lucide/building-2'
import LucideSquareCheckBig from '~icons/lucide/square-check-big'
import LucideStickyNote from '~icons/lucide/sticky-note'
import LucidePhone from '~icons/lucide/phone'
import LucidePhoneCall from '~icons/lucide/phone-call'
import LucideBot from '~icons/lucide/bot'
import LucideChartColumn from '~icons/lucide/chart-column'
import LucideSettings from '~icons/lucide/settings'
import router from '@/router'
import { isAstraConnectConfigured } from '@/utils/astraConnect'

/**
 * Sidebar registry. Each item is one of:
 * - { route } — in-app vue-router name (must exist; hidden otherwise)
 * - { connect, requiresConnect: true } — Astra Connect path (only when configured)
 * - { action: 'settings' } — opens the settings modal
 *
 * `section` groups the rail to match SHELL_SPEC / Figma v1. Settings stays in
 * the footer. Rules: every selectable item must work. No placeholder/Soon entries.
 * Work queue / Conversations hide until their routes are registered.
 */
export const navigationItems = [
  {
    label: 'Home',
    icon: LucideHouse,
    route: 'Dashboard',
    section: 'main',
    countKey: null,
  },
  {
    label: 'Work queue',
    icon: LucideListTodo,
    route: 'Work Queue',
    section: 'main',
    countKey: 'work_queue',
  },
  {
    label: 'Conversations',
    icon: LucideMessagesSquare,
    route: 'Conversations',
    section: 'main',
    countKey: null,
  },
  {
    label: 'Leads',
    icon: LucideUsers,
    route: 'Leads',
    section: 'records',
    countKey: 'leads',
  },
  {
    label: 'Deals',
    icon: LucideHandshake,
    route: 'Deals',
    section: 'records',
    countKey: 'deals',
  },
  {
    label: 'Contacts',
    icon: LucideContact,
    route: 'Contacts',
    section: 'records',
    countKey: null,
  },
  {
    label: 'Companies',
    icon: LucideBuilding2,
    route: 'Organizations',
    section: 'records',
    countKey: null,
  },
  {
    label: 'Tasks',
    icon: LucideSquareCheckBig,
    route: 'Tasks',
    section: 'activity',
    countKey: 'tasks',
  },
  {
    label: 'Notes',
    icon: LucideStickyNote,
    route: 'Notes',
    section: 'activity',
    countKey: null,
  },
  {
    label: 'Call logs',
    icon: LucidePhone,
    route: 'Call Logs',
    section: 'activity',
    countKey: null,
  },
  {
    label: 'Reports',
    icon: LucideChartColumn,
    route: 'Reports',
    section: 'insights',
    countKey: null,
  },
  {
    label: 'AI Calling',
    icon: LucidePhoneCall,
    connect: 'calls',
    requiresConnect: true,
    section: 'connect',
    countKey: null,
  },
  {
    label: 'Messages',
    icon: LucideMessagesSquare,
    connect: 'messages',
    requiresConnect: true,
    section: 'connect',
    countKey: null,
  },
  {
    label: 'AI Employees',
    icon: LucideBot,
    connect: 'employees',
    requiresConnect: true,
    section: 'connect',
    countKey: null,
  },
  {
    label: 'Settings',
    icon: LucideSettings,
    action: 'settings',
    section: 'footer',
    countKey: null,
  },
]

export const NAV_SECTION_ORDER = Object.freeze([
  { id: 'main', label: '', hideLabel: true },
  { id: 'records', label: 'Records' },
  { id: 'activity', label: 'Activity' },
  { id: 'insights', label: 'Insights' },
  { id: 'connect', label: 'Astra Connect' },
])

export function isNavItemAvailable(item, { mobile = false } = {}) {
  if (!item) return false
  if (item.placeholder) return false
  if (item.ready === false) return false
  if (mobile && item.desktopOnly) return false
  if (item.requiresConnect && !isAstraConnectConfigured()) return false
  if (item.route && !router.hasRoute(item.route)) return false
  return true
}

export function getNavigationItems({ mobile = false } = {}) {
  return navigationItems.filter((item) => isNavItemAvailable(item, { mobile }))
}

export function getNavigationSections({ mobile = false } = {}) {
  const items = getNavigationItems({ mobile }).filter(
    (item) => item.section !== 'footer',
  )
  return NAV_SECTION_ORDER.map((section) => ({
    ...section,
    views: items.filter((item) => (item.section || 'main') === section.id),
  })).filter((section) => section.views.length > 0)
}

export function getFooterNavItems({ mobile = false } = {}) {
  return getNavigationItems({ mobile }).filter(
    (item) => item.section === 'footer',
  )
}
