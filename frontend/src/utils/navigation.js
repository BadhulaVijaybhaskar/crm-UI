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
 * Flip these when the real page ships.
 * Items with ready:false are omitted from the sidebar and command palette.
 */
export const NAV_FEATURE_READY = Object.freeze({
  Conversations: true,
})

/**
 * Sidebar registry — labels/order/icons match Figma CRM v1 (p-*.html / crm.css).
 * Items are { route }, { connect, requiresConnect }, or Settings via route:'Settings'.
 * No placeholder/Soon entries. WhatsApp inbox is omitted on purpose.
 */
export const navigationItems = [
  {
    label: 'Home',
    icon: FigmaHomeIcon,
    route: 'Dashboard',
    section: 'main',
  },
  {
    label: 'Work queue',
    icon: FigmaWorkQueueIcon,
    route: 'Activities',
    section: 'main',
    count: 12,
  },
  {
    label: 'Conversations',
    icon: FigmaConversationsIcon,
    route: 'Conversations',
    ready: NAV_FEATURE_READY.Conversations,
    section: 'main',
  },
  {
    label: 'Leads',
    icon: FigmaLeadsIcon,
    route: 'Leads',
    section: 'records',
    count: 42,
  },
  {
    label: 'Deals',
    icon: FigmaDealsIcon,
    route: 'Deals',
    section: 'records',
    count: 14,
  },
  {
    label: 'Contacts',
    icon: FigmaContactsIcon,
    route: 'Contacts',
    section: 'records',
  },
  {
    label: 'Companies',
    icon: FigmaCompaniesIcon,
    route: 'Organizations',
    section: 'records',
  },
  {
    label: 'Tasks',
    icon: FigmaTasksIcon,
    route: 'Tasks',
    section: 'activity',
    count: 7,
  },
  {
    label: 'Notes',
    icon: FigmaNotesIcon,
    route: 'Notes',
    section: 'activity',
  },
  {
    label: 'Call logs',
    icon: FigmaCallLogsIcon,
    route: 'Call Logs',
    section: 'activity',
  },
  {
    label: 'Reports',
    icon: FigmaReportsIcon,
    route: 'Reports',
    section: 'insights',
  },
  {
    label: 'AI Calling',
    icon: FigmaAICallingIcon,
    connect: 'calls',
    requiresConnect: true,
    section: 'connect',
    external: true,
  },
  {
    label: 'Messages',
    icon: FigmaMessagesIcon,
    connect: 'messages',
    requiresConnect: true,
    section: 'connect',
    external: true,
  },
  {
    label: 'AI Employees',
    icon: FigmaAIEmployeesIcon,
    connect: 'employees',
    requiresConnect: true,
    section: 'connect',
    external: true,
  },
  {
    label: 'Settings',
    icon: FigmaSettingsIcon,
    route: 'Settings',
    section: 'footer',
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
