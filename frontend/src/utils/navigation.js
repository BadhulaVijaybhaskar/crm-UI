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
import LucideListTodo from '~icons/lucide/list-todo'
import LucideInbox from '~icons/lucide/inbox'
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
  WorkQueue: true,
  Conversations: true,
  Reports: false,
})

/**
 * Sidebar registry. Each item is one of:
 * - { route } — in-app vue-router name (must exist and be ready)
 * - { connect, requiresConnect: true } — Astra Connect path (only when configured)
 * - { action: 'settings' } — opens the settings modal
 *
 * Rules: every selectable item must work. No placeholder/Soon entries.
 * WhatsApp inbox is intentionally omitted (app stays installed).
 */
export const navigationItems = [
  {
    label: 'Dashboard',
    icon: LucideLayoutDashboard,
    route: 'Dashboard',
    desktopOnly: true,
  },
  { label: 'Leads', icon: LeadsIcon, route: 'Leads' },
  { label: 'Contacts', icon: ContactsIcon, route: 'Contacts' },
  {
    label: 'Companies',
    icon: OrganizationsIcon,
    route: 'Organizations',
  },
  { label: 'Deals', icon: DealsIcon, route: 'Deals' },
  { label: 'Tasks', icon: TaskIcon, route: 'Tasks' },
  {
    label: 'AI Calling',
    icon: LucidePhone,
    connect: 'calls',
    requiresConnect: true,
  },
  {
    label: 'Messages',
    icon: LucideMessagesSquare,
    connect: 'messages',
    requiresConnect: true,
  },
  {
    label: 'AI Employees',
    icon: LucideBot,
    connect: 'employees',
    requiresConnect: true,
  },
  {
    label: 'Activities',
    icon: LucideActivity,
    route: 'Activities',
    ready: NAV_FEATURE_READY.Activities,
  },
  {
    label: 'Work queue',
    icon: LucideListTodo,
    route: 'Work Queue',
    ready: NAV_FEATURE_READY.WorkQueue,
  },
  {
    label: 'Conversations',
    icon: LucideInbox,
    route: 'Conversations',
    ready: NAV_FEATURE_READY.Conversations,
  },
  {
    label: 'Reports',
    icon: LucideChartColumn,
    route: 'Reports',
    ready: NAV_FEATURE_READY.Reports,
  },
  {
    label: 'Settings',
    icon: LucideSettings,
    action: 'settings',
  },
]

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
