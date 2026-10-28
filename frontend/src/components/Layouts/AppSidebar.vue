<template>
  <div class="relative flex h-full text-[color:var(--crm-nav-fg)]">
    <Sidebar
      v-model:collapsed="isSidebarCollapsed"
      :collapsible="!mobile"
      :width="mobile ? '260px' : '240px'"
      collapsed-width="64px"
    >
      <div class="flex h-full flex-col">
        <div
          class="flex h-14 shrink-0 items-center gap-2 px-[18px]"
          :class="isCollapsed && 'justify-center px-0'"
        >
          <img
            :src="brandLogo.src"
            :srcset="brandLogo.srcset"
            :alt="brand.name || 'Astra CRM'"
            class="object-contain"
            :class="isCollapsed ? 'astra-brand-mark size-7' : 'h-6 max-w-[168px]'"
            height="24"
            decoding="async"
          />
          <button
            v-if="!mobile && !isCollapsed"
            type="button"
            class="ml-auto inline-flex size-7 items-center justify-center rounded-crm-chip text-[color:var(--crm-nav-faint)] hover:text-white"
            :aria-label="__('Collapse')"
            @click="isSidebarCollapsed = true"
          >
            <CollapseSidebar class="size-4" />
          </button>
          <button
            v-else-if="!mobile && isCollapsed"
            type="button"
            class="inline-flex size-7 items-center justify-center rounded-crm-chip text-[color:var(--crm-nav-faint)] hover:text-white"
            :aria-label="__('Expand')"
            @click="isSidebarCollapsed = false"
          >
            <CollapseSidebar class="size-4 [transform:rotateY(180deg)]" />
          </button>
        </div>

        <div class="flex min-h-0 flex-1 flex-col overflow-y-auto px-2.5 pb-2">
          <SidebarItem
            v-if="mobile"
            id="notifications-btn"
            :label="__('Notifications')"
            :route="{ name: 'Notifications' }"
            :active="activeItem === 'Notifications'"
            @click="onNotificationsClick"
          >
            <template #prefix>
              <NotificationsIcon class="astra-nav-icon size-4" />
            </template>
            <span class="flex-1 truncate text-[13px] font-medium">
              {{ __('Notifications') }}
            </span>
            <Badge
              v-if="unreadNotificationsCount"
              class="mr-2"
              :label="unreadNotificationsCount"
              variant="subtle"
            />
          </SidebarItem>

          <section
            v-for="section in navSections"
            :key="section.id"
            class="mt-1"
          >
            <div
              v-if="!section.hideLabel && !isCollapsed"
              class="px-5 pb-1 pt-3 text-[10.5px] font-semibold uppercase tracking-[0.06em] text-[color:var(--crm-nav-faint)]"
            >
              {{ __(section.label) }}
            </div>
            <nav class="flex flex-col gap-px">
              <SidebarItem
                v-for="link in section.views"
                :key="link.key"
                :route="link.to"
                :label="__(link.label)"
                :active="!link.external && activeItem === link.key"
                @click="onNavClick($event, link)"
              >
                <template #prefix>
                  <Icon :icon="link.icon" class="astra-nav-icon size-4 text-[color:var(--crm-nav-faint)]" />
                </template>
                <Tooltip
                  :text="__(link.label)"
                  side="right"
                  :hoverDelay="1500"
                  :disabled="isCollapsed"
                >
                  <span class="min-w-0 flex-1 truncate text-[13px] font-medium">
                    {{ __(link.label) }}
                  </span>
                </Tooltip>
                <template v-if="!isCollapsed && (link.external || link.count != null)" #suffix>
                  <span
                    v-if="link.count != null"
                    class="text-[11px] font-semibold text-[color:var(--crm-nav-faint)]"
                  >
                    {{ link.count }}
                  </span>
                  <Icon
                    v-if="link.external"
                    icon="lucide-external-link"
                    class="size-3 text-[color:var(--crm-nav-faint)]"
                    aria-hidden="true"
                  />
                </template>
              </SidebarItem>
            </nav>
          </section>

          <CollapsibleSection
            v-for="section in extraViews"
            :key="section.name"
            :label="section.name"
            :hideLabel="section.hideLabel"
            :opened="section.opened"
          >
            <template #header="{ opened, hide, toggle }">
              <div
                v-if="!hide && !isCollapsed"
                class="cursor-pointer px-5 pb-1 pt-3 text-[10.5px] font-semibold uppercase tracking-[0.06em] text-[color:var(--crm-nav-faint)]"
                @click="toggle()"
              >
                <span class="inline-flex items-center gap-1">
                  <span
                    class="lucide-chevron-right size-3.5 transition-transform"
                    :class="{ 'rotate-90': opened }"
                    aria-hidden="true"
                  />
                  {{ __(section.name) }}
                </span>
              </div>
            </template>
            <nav class="flex flex-col gap-px">
              <SidebarItem
                v-for="link in section.views"
                :key="link.key"
                :route="link.to"
                :label="__(link.label)"
                :active="activeItem === link.key"
                @click="selectItem($event, link.key)"
              >
                <template #prefix>
                  <Icon :icon="link.icon" class="astra-nav-icon size-4 text-[color:var(--crm-nav-faint)]" />
                </template>
                <span class="truncate text-[13px] font-medium">
                  {{ __(link.label) }}
                </span>
              </SidebarItem>
            </nav>
          </CollapsibleSection>
        </div>

        <div class="mt-auto flex flex-col gap-1 px-2.5 pb-2 pt-2">
          <div v-if="!mobile" class="mb-1 flex flex-col gap-2">
            <SignupBanner
              v-if="isDemoSite && isFCSite"
              :isSidebarCollapsed="isCollapsed"
              :afterSignup="() => capture('signup_from_demo_site')"
            />
            <TrialBanner
              v-if="isFCSite"
              :isSidebarCollapsed="isCollapsed"
              :afterUpgrade="() => capture('upgrade_plan_from_trial_banner')"
            />
            <GettingStartedBanner
              v-if="!isOnboardingStepsCompleted"
              :isSidebarCollapsed="isCollapsed"
            />
          </div>

          <SidebarItem
            v-if="!mobile && isManager() && isDemoDataCreated"
            :label="__('Clear Demo Data')"
            class="!text-crm-danger"
            @click="() => clearDemoData()"
          >
            <template #prefix>
              <BrushCleaningIcon class="size-4" />
            </template>
          </SidebarItem>

          <SidebarItem
            v-if="!mobile && isOnboardingStepsCompleted"
            :label="__('Help')"
            @click="toggleHelpModal"
          >
            <template #prefix>
              <HelpIcon class="astra-nav-icon size-4 text-[color:var(--crm-nav-faint)]" />
            </template>
          </SidebarItem>

          <SidebarItem
            v-for="link in footerLinks"
            :key="link.key"
            :label="__(link.label)"
            :active="link.action === 'settings' && showSettings"
            @click="onNavClick($event, link)"
          >
            <template #prefix>
              <Icon :icon="link.icon" class="astra-nav-icon size-4 text-[color:var(--crm-nav-faint)]" />
            </template>
            <span class="truncate text-[13px] font-medium">{{ __(link.label) }}</span>
          </SidebarItem>

          <div
            class="mt-1 flex items-center gap-2.5 border-t border-[color:var(--crm-nav-border)] px-1 py-3.5"
            :class="isCollapsed && 'justify-center px-0'"
          >
            <AstraAvatar
              :name="currentUser.full_name || currentUser.email || '?'"
              size="md"
            />
            <div v-if="!isCollapsed" class="min-w-0 flex-1">
              <div class="truncate text-[12.5px] font-semibold text-[#E8EDF5]">
                {{ currentUser.full_name || currentUser.email }}
              </div>
              <div class="truncate text-[11.5px] text-[color:var(--crm-nav-faint)]">
                {{ userRole }}
              </div>
            </div>
            <AstraThemeToggle v-if="!isCollapsed" />
          </div>
        </div>
      </div>
    </Sidebar>
    <Notifications v-if="!mobile" />
  </div>

  <template v-if="!mobile">
    <Settings />
    <HelpModal
      v-if="showHelpModal"
      v-model="showHelpModal"
      v-model:articles="articles"
      title="Astra CRM"
      appName="crm"
      docsLink=""
      :logo="CRMLogo"
      :afterSkip="(step) => capture('onboarding_step_skipped_' + step)"
      :afterSkipAll="() => capture('onboarding_steps_skipped')"
      :afterReset="(step) => capture('onboarding_step_reset_' + step)"
      :afterResetAll="() => capture('onboarding_steps_reset')"
    />
    <IntermediateStepModal
      v-model="showIntermediateModal"
      :currentStep="currentStep"
    />
  </template>
</template>

<script setup>
import BrushCleaningIcon from '~icons/lucide/brush-cleaning'
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import InviteIcon from '@/components/Icons/InviteIcon.vue'
import ConvertIcon from '@/components/Icons/ConvertIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import Icon from '@/components/Icon.vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CollapseSidebar from '@/components/Icons/CollapseSidebar.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import HelpIcon from '@/components/Icons/HelpIcon.vue'
import Notifications from '@/components/Notifications.vue'
import Settings from '@/components/Settings/Settings.vue'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import AstraThemeToggle from '@/components/astra/AstraThemeToggle.vue'
import {
  getFooterNavItems,
  getNavigationSections,
} from '@/utils/navigation'
import { openAstraConnect } from '@/utils/astraConnect'
import {
  ASTRA_NAV_LOCKUP,
  ASTRA_NAV_LOCKUP_SRCSET,
  ASTRA_NAV_MARK,
  ASTRA_NAV_MARK_SRCSET,
} from '@/assets/brand'
import { viewsStore } from '@/stores/views'
import { navCountMap } from '@/stores/navCounts'
import {
  unreadNotificationsCount,
  notificationsStore,
} from '@/stores/notifications'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'
import { getSettings } from '@/stores/settings'
import {
  showSettings,
  activeSettingsPage,
  mobileSidebarOpened,
} from '@/composables/settings'
import { useBroadcast } from '@/composables/useBroadcast.js'
import { call, Sidebar, SidebarItem, Tooltip, Badge } from 'frappe-ui'
import { SignupBanner } from '@framework/ui/components/SignupBanner'
import { TrialBanner } from '@framework/ui/components/TrialBanner'
import {
  HelpModal,
  GettingStartedBanner,
  useOnboarding,
  showHelpModal,
  minimize,
  IntermediateStepModal,
} from '@framework/ui/components/Onboarding'
import { useTelemetry } from '@framework/ui/telemetry'
import router from '@/router'
import { useStorage } from '@vueuse/core'
import { useDemoData } from '@/composables/demoData'
import { useCrmOnboarding } from '@/composables/onboarding'
import { ref, reactive, computed, markRaw, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  mobile: { type: Boolean, default: false },
})

const route = useRoute()
const { getPinnedViews, getPublicViews } = viewsStore()
const { toggle: toggleNotificationPanel } = notificationsStore()
const { capture } = useTelemetry()
const { clearDemoData, isDemoDataCreated } = useDemoData()
const { send } = useBroadcast()
const { settings, brand } = getSettings()

const isSidebarCollapsed = useStorage('isSidebarCollapsed', false)
const isCollapsed = computed(() => isSidebarCollapsed.value && !props.mobile)

const isFCSite = ref(window.is_fc_site)
const isDemoSite = ref(window.is_demo_site)

const brandLogo = computed(() => {
  if (settings.value?.brand_logo) {
    return { src: settings.value.brand_logo, srcset: undefined }
  }
  if (isCollapsed.value) {
    return { src: ASTRA_NAV_MARK, srcset: ASTRA_NAV_MARK_SRCSET }
  }
  return { src: ASTRA_NAV_LOCKUP, srcset: ASTRA_NAV_LOCKUP_SRCSET }
})

function navLinkFromItem(link) {
  const count =
    link.countKey && navCountMap.value[link.countKey] != null
      ? navCountMap.value[link.countKey]
      : null
  if (link.connect) {
    return {
      label: link.label,
      icon: link.icon,
      key: `connect:${link.connect}`,
      external: true,
      connect: link.connect,
      count: null,
    }
  }
  if (link.action === 'settings') {
    return {
      label: link.label,
      icon: link.icon,
      key: 'settings',
      action: 'settings',
      count: null,
    }
  }
  return {
    label: link.label,
    icon: link.icon,
    key: link.route,
    to: { name: link.route },
    count,
  }
}

const navSections = computed(() =>
  getNavigationSections({ mobile: props.mobile }).map((section) => ({
    ...section,
    views: section.views.map((link) => navLinkFromItem(link)),
  })),
)

const footerLinks = computed(() =>
  getFooterNavItems({ mobile: props.mobile }).map((link) => navLinkFromItem(link)),
)

const extraViews = computed(() => {
  const views = []
  if (getPublicViews().length) {
    views.push({
      name: 'Public Views',
      opened: true,
      views: parseView(getPublicViews()),
    })
  }
  if (getPinnedViews().length) {
    views.push({
      name: 'Pinned Views',
      opened: true,
      views: parseView(getPinnedViews()),
    })
  }
  return views
})

function parseView(views) {
  return views.map((view) => ({
    label: view.label,
    icon: getIcon(view.route_name, view.icon),
    key: view.name,
    to: {
      name: view.route_name,
      params: { viewType: view.type || 'list' },
      query: { view: view.name },
    },
  }))
}

function onNavClick(event, link) {
  if (link.connect) {
    openAstraConnect(link.connect)
    if (props.mobile) mobileSidebarOpened.value = false
    return
  }
  if (link.action === 'settings') {
    showSettings.value = true
    if (props.mobile) mobileSidebarOpened.value = false
    return
  }
  selectItem(event, link.key)
}

function getIcon(routeName, icon) {
  if (icon) return icon
  switch (routeName) {
    case 'Leads':
      return LeadsIcon
    case 'Deals':
      return DealsIcon
    case 'Contacts':
      return ContactsIcon
    case 'Organizations':
      return OrganizationsIcon
    case 'Notes':
      return NoteIcon
    case 'Call Logs':
      return PhoneIcon
    default:
      return PinIcon
  }
}

function currentRouteKey() {
  const key = route.query.view || route.name
  const flat = [
    ...navSections.value.flatMap((s) => s.views || []),
    ...extraViews.value.flatMap((s) => s.views || []),
  ]
  const known = flat.some((v) => v.key === key || v.key === route.name)
  if (!known && key !== 'Notifications') return null
  return key
}

const activeItem = ref(currentRouteKey())

function selectItem(event, key) {
  if (
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey ||
    event.button === 1
  ) {
    return
  }
  activeItem.value = key
  if (props.mobile) mobileSidebarOpened.value = false
}

watch(
  () => [route.name, route.query.view],
  () => (activeItem.value = currentRouteKey()),
)

function onNotificationsClick(event) {
  if (props.mobile) {
    selectItem(event, 'Notifications')
  } else {
    toggleNotificationPanel()
  }
}

function toggleHelpModal() {
  showHelpModal.value = minimize.value ? true : !showHelpModal.value
  minimize.value = !showHelpModal.value
}

const { user } = sessionStore()
const { users, isManager, getUser } = usersStore()
const { isOnboardingStepsCompleted, setUp } = useOnboarding('frappecrm')
const { flushPendingSteps } = useCrmOnboarding()

const currentUser = computed(() => getUser() || {})
const userRole = computed(() => {
  const u = currentUser.value
  if (u?.role_profile_name) return u.role_profile_name
  if (isManager()) return __('Manager')
  return __('Sales user')
})

const ONBOARDING_KEY = 'frappecrm_onboarding_status'

async function reconcileOnboarding(currentSteps) {
  let store
  try {
    store = JSON.parse(localStorage.getItem('onboardingStatus') || '{}')
  } catch {
    return
  }
  const persisted = store?.[user]?.[ONBOARDING_KEY]
  if (!persisted?.length) return
  if (persisted.every((s) => s.completed)) return

  const doneByName = new Map(persisted.map((s) => [s.name, s.completed]))
  const currentNames = new Set(currentSteps.map((s) => s.name))
  const visible = currentSteps.map((s) => ({
    name: s.name,
    completed: doneByName.get(s.name) ?? false,
  }))
  const knownNames = new Set(steps.map((s) => s.name))
  const hidden = persisted.filter(
    (s) => !currentNames.has(s.name) && knownNames.has(s.name),
  )
  const merged = [...visible, ...hidden]

  const unchanged =
    merged.length === persisted.length &&
    merged.every(
      (m, i) =>
        persisted[i]?.name === m.name &&
        persisted[i]?.completed === m.completed,
    )
  if (unchanged) return

  store[user][ONBOARDING_KEY] = merged
  try {
    localStorage.setItem('onboardingStatus', JSON.stringify(store))
    await call('frappe.onboarding.update_user_onboarding_status', {
      steps: JSON.stringify(merged),
      appName: 'frappecrm',
    })
  } catch {
    return
  }
  window.location.reload()
}

async function getFirstLead() {
  return await getFirstRecord('firstLead', 'crm.api.onboarding.get_first_lead')
}

async function getFirstDeal() {
  return await getFirstRecord('firstDeal', 'crm.api.onboarding.get_first_deal')
}

async function getFirstRecord(key, method) {
  let storageKey = key + user
  let cached = localStorage.getItem(storageKey)
  let name = await call(method, { name: cached })
  if (name) {
    localStorage.setItem(storageKey, name)
  } else {
    localStorage.removeItem(storageKey)
  }
  return name
}

const showIntermediateModal = ref(false)
const currentStep = ref({})

const steps = reactive([
  {
    name: 'create_first_lead',
    title: __('Add your first lead'),
    icon: markRaw(LeadsIcon),
    completed: false,
    onClick: () => {
      minimize.value = true
      router.push({ name: 'Leads' })
      send('trigger_lead_create', true)
      capture('onboarding_step_clicked_create_first_lead')
    },
  },
  {
    name: 'connect_your_email',
    title: __('Connect your email'),
    icon: markRaw(EmailIcon),
    completed: false,
    onClick: () => {
      minimize.value = true
      showSettings.value = true
      activeSettingsPage.value = __('Accounts')
      capture('onboarding_step_clicked_connect_your_email')
    },
    condition: () => isManager(),
  },
  {
    name: 'invite_your_team',
    title: __('Invite your team'),
    icon: markRaw(InviteIcon),
    completed: false,
    onClick: () => {
      minimize.value = true
      showSettings.value = true
      activeSettingsPage.value = 'Invite User'
      capture('onboarding_step_clicked_invite_your_team')
    },
    condition: () => isManager(),
  },
  {
    name: 'convert_lead_to_deal',
    title: __('Convert lead to deal'),
    icon: markRaw(ConvertIcon),
    completed: false,
    dependsOn: 'create_first_lead',
    onClick: async () => {
      minimize.value = true
      capture('onboarding_step_clicked_convert_lead_to_deal')
      currentStep.value = {
        title: __('Convert lead to deal'),
        buttonLabel: __('Convert'),
        videoURL: '/assets/crm/videos/convertToDeal.mov',
        onClick: async () => {
          showIntermediateModal.value = false
          currentStep.value = {}

          let lead = await getFirstLead()
          if (lead) {
            router.push({ name: 'Lead', params: { leadId: lead } })
          } else {
            router.push({ name: 'Leads' })
          }
        },
      }
      showIntermediateModal.value = true
    },
  },
  {
    name: 'create_first_task',
    title: __('Schedule a follow-up task'),
    icon: markRaw(TaskIcon),
    completed: false,
    onClick: async () => {
      minimize.value = true
      let deal = await getFirstDeal()
      capture('onboarding_step_clicked_create_first_task')

      if (deal) {
        router.push({
          name: 'Deal',
          params: { dealId: deal },
          hash: '#tasks',
        })
      } else {
        router.push({ name: 'Tasks' })
      }
    },
  },
])

onMounted(async () => {
  if (props.mobile) return

  await users.promise

  const filteredSteps = steps.filter((step) => {
    if (step.condition) {
      return step.condition()
    }
    return true
  })

  await reconcileOnboarding(filteredSteps)
  setUp(filteredSteps)
  flushPendingSteps()
})

const articles = ref([
  {
    title: __('Introduction'),
    opened: false,
    subArticles: [
      { name: 'introduction', title: __('Introduction') },
      { name: 'setting-up', title: __('Setting Up') },
    ],
  },
  {
    title: __('Settings'),
    opened: false,
    subArticles: [
      { name: 'profile', title: __('Profile') },
      { name: 'custom-branding', title: __('Custom Branding') },
      { name: 'home-actions', title: __('Home Actions') },
      { name: 'invite-users', title: __('Invite Users') },
    ],
  },
  {
    title: __('Masters'),
    opened: false,
    subArticles: [
      { name: 'lead', title: __('Lead') },
      { name: 'deal', title: __('Deal') },
      { name: 'contact', title: __('Contact') },
      { name: 'organization', title: __('Organization') },
      { name: 'note', title: __('Note') },
      { name: 'task', title: __('Task') },
      { name: 'call-log', title: __('Call Log') },
      { name: 'email-template', title: __('Email Template') },
    ],
  },
  {
    title: __('Capturing Leads'),
    opened: false,
    subArticles: [{ name: 'web-form', title: __('Web Form') }],
  },
  {
    title: __('Views'),
    opened: false,
    subArticles: [
      { name: 'view', title: __('Saved View') },
      { name: 'public-view', title: __('Public View') },
      { name: 'pinned-view', title: __('Pinned View') },
    ],
  },
  {
    title: __('Other Features'),
    opened: false,
    subArticles: [
      { name: 'email-communication', title: __('Email Communication') },
      { name: 'comment', title: __('Comment') },
      { name: 'data', title: __('Data') },
      { name: 'service-level-agreement', title: __('Service Level Agreement') },
      { name: 'assignment-rule', title: __('Assignment Rule') },
      { name: 'notification', title: __('Notification') },
    ],
  },
  {
    title: __('Customization'),
    opened: false,
    subArticles: [
      { name: 'custom-fields', title: __('Custom Fields') },
      { name: 'custom-actions', title: __('Custom Actions') },
      { name: 'custom-statuses', title: __('Custom Statuses') },
      { name: 'custom-list-actions', title: __('Custom List Actions') },
      { name: 'quick-entry-layout', title: __('Quick Entry Layout') },
    ],
  },
  {
    title: __('Integration'),
    opened: false,
    subArticles: [
      { name: 'twilio', title: __('Twilio') },
      { name: 'exotel', title: __('Exotel') },
      { name: 'whatsapp', title: __('WhatsApp') },
      { name: 'erpnext', title: __('ERP') },
    ],
  },
  {
    title: __('Astra CRM mobile'),
    opened: false,
    subArticles: [
      { name: 'mobile-app-installation', title: __('Mobile App Installation') },
    ],
  },
])
</script>
