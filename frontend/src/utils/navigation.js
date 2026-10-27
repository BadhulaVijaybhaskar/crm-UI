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

/**
 * Sidebar registry. Each item is one of:
 * - { route } — in-app vue-router name (must exist)
 * - { connect } — Astra Connect path key (opens new tab; SSO placeholder)
 * - { action: 'settings' } — opens the settings modal
 * - { placeholder: true, route } — in-app page clearly labeled as placeholder
 *
 * WhatsApp inbox is intentionally omitted from this registry (app stays installed).
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
    // PLACEHOLDER: open Astra Connect until secure SSO deep-link exists
    placeholder: true,
  },
  {
    label: 'Messages',
    icon: LucideMessagesSquare,
    connect: 'messages',
    // PLACEHOLDER: open Astra Connect until secure SSO deep-link exists
    placeholder: true,
  },
  {
    label: 'AI Employees',
    icon: LucideBot,
    connect: 'employees',
    // PLACEHOLDER: open Astra Connect until secure SSO deep-link exists
    placeholder: true,
  },
  {
    label: 'Activities',
    icon: LucideActivity,
    route: 'Activities',
    placeholder: true,
  },
  {
    label: 'Reports',
    icon: LucideChartColumn,
    route: 'Reports',
    placeholder: true,
  },
  {
    label: 'Settings',
    icon: LucideSettings,
    action: 'settings',
  },
]

export function getNavigationItems({ mobile = false } = {}) {
  return navigationItems.filter((item) => {
    if (mobile && item.desktopOnly) return false
    if (item.route && !router.hasRoute(item.route)) return false
    return true
  })
}
