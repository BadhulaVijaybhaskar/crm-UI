import {
  FigmaHomeIcon,
  FigmaWorkQueueIcon,
  FigmaConversationsIcon,
  FigmaLeadsIcon,
  FigmaDealsIcon,
  FigmaContactsIcon,
  FigmaCompaniesIcon,
  FigmaTasksIcon,
  FigmaNotesIcon,
  FigmaCallLogsIcon,
  FigmaReportsIcon,
  FigmaAICallingIcon,
  FigmaMessagesIcon,
  FigmaAIEmployeesIcon,
  FigmaSettingsIcon,
} from '@/components/Icons/FigmaNavIcons'
import router from '@/router'
import { isAstraConnectConfigured } from '@/utils/astraConnect'

/**
 * Sidebar registry — labels/order/icons match Figma CRM v1 (p-*.html / crm.css).
 * Counts come from `crm.api.nav.get_nav_counts` via `countKey` (never hard-coded).
 * Items whose `route` is not registered are hidden.
 *
 * Work queue currently lands on Activities until the dedicated Work Queue route
 * ships; Conversations is registered on this branch.
 */
export const navigationItems = [
  {
    label: 'Home',
    icon: FigmaHomeIcon,
    route: 'Dashboard',
    section: 'main',
    countKey: null,
  },
  {
    label: 'Work queue',
    icon: FigmaWorkQueueIcon,
    route: 'Activities',
    section: 'main',
    countKey: 'work_queue',
  },
  {
    label: 'Conversations',
    icon: FigmaConversationsIcon,
    route: 'Conversations',
    section: 'main',
    countKey: null,
  },
  {
    label: 'Leads',
    icon: FigmaLeadsIcon,
    route: 'Leads',
    section: 'records',
    countKey: 'leads',
  },
  {
    label: 'Deals',
    icon: FigmaDealsIcon,
    route: 'Deals',
    section: 'records',
    countKey: 'deals',
  },
  {
    label: 'Contacts',
    icon: FigmaContactsIcon,
    route: 'Contacts',
    section: 'records',
    countKey: null,
  },
  {
    label: 'Companies',
    icon: FigmaCompaniesIcon,
    route: 'Organizations',
    section: 'records',
    countKey: null,
  },
  {
    label: 'Tasks',
    icon: FigmaTasksIcon,
    route: 'Tasks',
    section: 'activity',
    countKey: 'tasks',
  },
  {
    label: 'Notes',
    icon: FigmaNotesIcon,
    route: 'Notes',
    section: 'activity',
    countKey: null,
  },
  {
    label: 'Call logs',
    icon: FigmaCallLogsIcon,
    route: 'Call Logs',
    section: 'activity',
    countKey: null,
  },
  {
    label: 'Reports',
    icon: FigmaReportsIcon,
    route: 'Reports',
    section: 'insights',
    countKey: null,
  },
  {
    label: 'AI Calling',
    icon: FigmaAICallingIcon,
    connect: 'calls',
    requiresConnect: true,
    section: 'connect',
    external: true,
    countKey: null,
  },
  {
    label: 'Messages',
    icon: FigmaMessagesIcon,
    connect: 'messages',
    requiresConnect: true,
    section: 'connect',
    external: true,
    countKey: null,
  },
  {
    label: 'AI Employees',
    icon: FigmaAIEmployeesIcon,
    connect: 'employees',
    requiresConnect: true,
    section: 'connect',
    external: true,
    countKey: null,
  },
  {
    label: 'Settings',
    icon: FigmaSettingsIcon,
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
