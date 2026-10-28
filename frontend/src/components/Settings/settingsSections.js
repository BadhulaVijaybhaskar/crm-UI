import { defineAsyncComponent, markRaw } from 'vue'
import { usersStore } from '@/stores/users'
import { isWhatsAppInstalled } from '@/composables/whatsapp'
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LucideNetwork from '~icons/lucide/network'
import LucideWorkflow from '~icons/lucide/workflow'
import LucideTextCursorInput from '~icons/lucide/text-cursor-input'
import LucideKeyRound from '~icons/lucide/key-round'
import MonitorCogIcon from '~icons/lucide/monitor-cog'
import SlidersIcon from '@/components/Icons/SlidersIcon.vue'
import SparkleIcon from '@/components/Icons/SparkleIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import ERPNextIcon from '@/components/Icons/ERPNextIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import EmailTemplateIcon from '@/components/Icons/EmailTemplateIcon.vue'
import SettingsIcon from '@/components/Icons/SettingsIcon.vue'
import SettingsIcon2 from '@/components/Icons/SettingsIcon2.vue'
import ShieldCheck from '~icons/lucide/shield-check'
import LucideZap from '~icons/lucide/zap'

function load(loader) {
  return markRaw(defineAsyncComponent(loader))
}

function manager() {
  return usersStore().isManager()
}

function admin() {
  return usersStore().isAdmin()
}

function erpIntegrationAvailable() {
  return Boolean(
    window.erp_integration_available || window.boot?.erp_integration_available,
  )
}

export const settingsGroups = [
  {
    id: 'personal',
    label: 'Personal',
    items: [
      {
        slug: 'profile',
        label: 'Profile',
        icon: 'circle-user',
        component: load(
          () => import('@/components/Settings/Profile/ProfilePage.vue'),
        ),
      },
      {
        slug: 'preferences',
        label: 'Preferences',
        icon: markRaw(SlidersIcon),
        component: load(
          () => import('@/components/Settings/PreferencesSettings.vue'),
        ),
      },
    ],
  },
  {
    id: 'workspace',
    label: 'Workspace',
    condition: manager,
    items: [
      {
        slug: 'general',
        label: 'General',
        icon: markRaw(SettingsIcon),
        component: load(
          () => import('@/components/Settings/GeneralSettings.vue'),
        ),
      },
      {
        slug: 'dashboard',
        label: 'Dashboard',
        icon: markRaw(LucideLayoutDashboard),
        component: load(
          () => import('@/components/Settings/DashboardSettings.vue'),
        ),
      },
      {
        slug: 'defaults',
        label: 'Defaults',
        icon: markRaw(MonitorCogIcon),
        component: load(
          () => import('@/components/Settings/DefaultsSettings.vue'),
        ),
      },
      {
        slug: 'brand',
        label: 'Brand',
        icon: markRaw(SparkleIcon),
        component: load(() => import('@/components/Settings/BrandSettings.vue')),
      },
      {
        slug: 'home-actions',
        label: 'Home Actions',
        icon: 'house',
        component: load(() => import('@/components/Settings/HomeActions.vue')),
      },
    ],
  },
  {
    id: 'users',
    label: 'Users',
    condition: manager,
    items: [
      {
        slug: 'users',
        label: 'Users',
        icon: 'user',
        component: load(() => import('@/components/Settings/Users.vue')),
      },
      {
        slug: 'invite-user',
        label: 'Invite User',
        icon: 'user-plus',
        component: load(
          () => import('@/components/Settings/InviteUserPage.vue'),
        ),
      },
      {
        slug: 'sales-hierarchy',
        label: 'Sales Hierarchy',
        icon: markRaw(LucideNetwork),
        component: load(
          () => import('@/components/Settings/Hierarchy/Hierarchy.vue'),
        ),
      },
    ],
  },
  {
    id: 'pipeline',
    label: 'Pipeline & Fields',
    items: [
      {
        slug: 'pipeline-stages',
        label: 'Pipeline Stages',
        icon: 'list-tree',
        component: load(
          () => import('@/components/Settings/PipelineStagesSettings.vue'),
        ),
        condition: manager,
      },
      {
        slug: 'fields-layout',
        label: 'Fields Layout',
        icon: 'columns-2',
        component: load(
          () => import('@/components/Settings/FieldsLayoutSettings.vue'),
        ),
        condition: admin,
      },
    ],
  },
  {
    id: 'automation',
    label: 'Automation',
    condition: manager,
    items: [
      {
        slug: 'workflow-automations',
        label: 'Workflow Automations',
        icon: markRaw(LucideWorkflow),
        component: load(
          () =>
            import(
              '@/components/Settings/WorkflowAutomations/WorkflowAutomationPage.vue'
            ),
        ),
      },
      {
        slug: 'assignment-rules',
        label: 'Assignment Rules',
        icon: markRaw(SettingsIcon2),
        iconClass: 'rotate-90',
        component: load(
          () =>
            import(
              '@/components/Settings/AssignmentRules/AssignmentRulePage.vue'
            ),
        ),
      },
      {
        slug: 'sla-policies',
        label: 'SLA Policies',
        icon: markRaw(ShieldCheck),
        component: load(() => import('@/components/Settings/Sla/SlaConfig.vue')),
      },
      {
        slug: 'forms',
        label: 'Forms',
        icon: markRaw(LucideTextCursorInput),
        component: load(
          () => import('@/components/Settings/Forms/FormsSettings.vue'),
        ),
      },
      {
        slug: 'enrichment',
        label: 'Enrichment',
        icon: markRaw(LucideZap),
        component: load(
          () =>
            import('@/components/Settings/Enrichment/EnrichmentSettings.vue'),
        ),
      },
    ],
  },
  {
    id: 'email',
    label: 'Email',
    items: [
      {
        slug: 'accounts',
        label: 'Accounts',
        icon: markRaw(Email2Icon),
        component: load(() => import('@/components/Settings/EmailConfig.vue')),
        condition: manager,
      },
      {
        slug: 'templates',
        label: 'Templates',
        icon: markRaw(EmailTemplateIcon),
        component: load(
          () =>
            import('@/components/Settings/EmailTemplate/EmailTemplatePage.vue'),
        ),
      },
    ],
  },
  {
    id: 'integrations',
    label: 'Integrations',
    items: [
      {
        slug: 'astra-connect',
        label: 'Astra Connect',
        icon: markRaw(PhoneIcon),
        component: load(
          () => import('@/components/Settings/AstraConnectSettings.vue'),
        ),
        condition: manager,
      },
      {
        slug: 'api-webhooks',
        label: 'API & webhooks',
        icon: markRaw(LucideKeyRound),
        component: load(
          () => import('@/components/Settings/DeveloperAccess.vue'),
        ),
        condition: admin,
      },
      {
        slug: 'telephony',
        label: 'Telephony',
        icon: markRaw(PhoneIcon),
        component: load(
          () => import('@/components/Settings/Telephony/TelephonyPage.vue'),
        ),
      },
      {
        slug: 'whatsapp',
        label: 'WhatsApp',
        icon: markRaw(WhatsAppIcon),
        component: load(
          () => import('@/components/Settings/WhatsAppSettings.vue'),
        ),
        condition: () => isWhatsAppInstalled.value && manager(),
      },
      {
        slug: 'erp',
        label: 'ERP',
        icon: markRaw(ERPNextIcon),
        component: load(
          () => import('@/components/Settings/ERPNextSettings.vue'),
        ),
        condition: () => manager() && erpIntegrationAvailable(),
      },
      {
        slug: 'lead-syncing',
        label: 'Lead Syncing',
        icon: 'refresh-cw',
        component: load(
          () =>
            import('@/components/Settings/LeadSyncing/LeadSyncSourcePage.vue'),
        ),
        condition: manager,
      },
    ],
  },
]

export function visibleSettingsGroups() {
  return settingsGroups
    .filter((group) => !group.condition || group.condition())
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => !item.condition || item.condition()),
    }))
    .filter((group) => group.items.length)
}

export function sectionFromSlug(slug) {
  if (!slug) return null
  const needle = String(slug).trim().toLowerCase()
  for (const group of settingsGroups) {
    for (const item of group.items) {
      if (item.slug === needle) return item
    }
  }
  return null
}

export function slugFromLabel(label) {
  if (label == null) return null
  const text = String(label).trim()
  if (!text) return null
  const direct = sectionFromSlug(text)
  if (direct) return direct.slug
  const needle = text.toLowerCase()
  for (const group of settingsGroups) {
    for (const item of group.items) {
      if (item.label.toLowerCase() === needle) return item.slug
      if (typeof __ !== 'function') continue
      const translated = __(item.label)
      if (translated && String(translated).toLowerCase() === needle) {
        return item.slug
      }
    }
  }
  return null
}
