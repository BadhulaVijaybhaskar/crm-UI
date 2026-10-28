import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import LucideHouse from '~icons/lucide/house'
import LucideListChecks from '~icons/lucide/list-checks'
import LucideInbox from '~icons/lucide/inbox'
import LucidePhone from '~icons/lucide/phone'
import LucideMessagesSquare from '~icons/lucide/messages-square'
import LucideBot from '~icons/lucide/bot'
import LucideChartColumn from '~icons/lucide/chart-column'
import LucideSettings from '~icons/lucide/settings'
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
 * Sidebar registry — labels/order match Figma CRM v1 (p-*.html / crm.css).
 * - { route } — in-app vue-router name
 * - { connect, requiresConnect: true } — Astra Connect path
 * - { action: 'settings' } — opens the settings modal
 * Optional `count` is a static design default; live counts can override later.
 */
export const navigationItems = [
  {
    label: 'Home',
    icon: LucideHouse,
    route: 'Dashboard',
    section: 'main',
  },
  {
    label: 'Work queue',
    icon: LucideListChecks,
    route: 'Activities',
    section: 'main',
    count: 12,
  },
  {
    label: 'Conversations',
    icon: LucideInbox,
    route: 'Conversations',
    ready: NAV_FEATURE_READY.Conversations,
    section: 'main',
  },
  {
    label: 'Leads',
    icon: LeadsIcon,
    route: 'Leads',
    section: 'records',
    count: 42,
  },
  {
    label: 'Deals',
    icon: DealsIcon,
    route: 'Deals',
    section: 'records',
    count: 14,
  },
  {
    label: 'Contacts',
    icon: ContactsIcon,
    route: 'Contacts',
    section: 'records',
  },
  {
    label: 'Companies',
    icon: OrganizationsIcon,
    route: 'Organizations',
    section: 'records',
  },
  {
    label: 'Tasks',
    icon: TaskIcon,
    route: 'Tasks',
    section: 'activity',
    count: 7,
  },
  {
    label: 'Notes',
    icon: NoteIcon,
    route: 'Notes',
    section: 'activity',
  },
  {
    label: 'Call logs',
    icon: PhoneIcon,
    route: 'Call Logs',
    section: 'activity',
  },
  {
    label: 'Reports',
    icon: LucideChartColumn,
    route: 'Reports',
    section: 'insights',
  },
  {
    label: 'AI Calling',
    icon: LucidePhone,
    connect: 'calls',
    requiresConnect: true,
    section: 'connect',
    external: true,
  },
  {
    label: 'Messages',
    icon: LucideMessagesSquare,
    connect: 'messages',
    requiresConnect: true,
    section: 'connect',
    external: true,
  },
  {
    label: 'AI Employees',
    icon: LucideBot,
    connect: 'employees',
    requiresConnect: true,
    section: 'connect',
    external: true,
  },
  {
    label: 'Settings',
    icon: LucideSettings,
    action: 'settings',
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
