import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LucidePhone from '~icons/lucide/phone'
import LucideMessagesSquare from '~icons/lucide/messages-square'
import LucideBot from '~icons/lucide/bot'
import LucideActivity from '~icons/lucide/activity'
import LucideChartColumn from '~icons/lucide/chart-column'
import LucideSettings from '~icons/lucide/settings'
import router from '@/router'
import { isAstraConnectConfigured } from '@/utils/astraConnect'

/**
 * Flip these when the real page ships (CRM-08 Activities, CRM-09 Reports).
 * Items with ready:false are omitted from the sidebar and command palette.
 */
export const NAV_FEATURE_READY = Object.freeze({
  Activities: true,
  Reports: true,
})

/**
 * Sidebar registry. Each item is one of:
 * - { route } — in-app vue-router name (must exist and be ready)
 * - { connect, requiresConnect: true } — Astra Connect path (only when configured)
 * - { action: 'settings' } — opens the settings modal
 *
 * `section` groups the rail to match Figma v1. Settings stays in the footer.
 * Rules: every selectable item must work. No placeholder/Soon entries.
 */
export const navigationItems = [
  {
    label: 'Dashboard',
    icon: LucideLayoutDashboard,
    route: 'Dashboard',
    section: 'main',
  },
  { label: 'Leads', icon: LeadsIcon, route: 'Leads', section: 'records' },
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
  { label: 'Deals', icon: DealsIcon, route: 'Deals', section: 'records' },
  { label: 'Tasks', icon: TaskIcon, route: 'Tasks', section: 'activity' },
  {
    label: 'AI Calling',
    icon: LucidePhone,
    connect: 'calls',
    requiresConnect: true,
    section: 'connect',
  },
  {
    label: 'Messages',
    icon: LucideMessagesSquare,
    connect: 'messages',
    requiresConnect: true,
    section: 'connect',
  },
  {
    label: 'AI Employees',
    icon: LucideBot,
    connect: 'employees',
    requiresConnect: true,
    section: 'connect',
  },
  {
    label: 'Activities',
    icon: LucideActivity,
    route: 'Activities',
    ready: NAV_FEATURE_READY.Activities,
    section: 'activity',
  },
  {
    label: 'Reports',
    icon: LucideChartColumn,
    route: 'Reports',
    ready: NAV_FEATURE_READY.Reports,
    section: 'insights',
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
