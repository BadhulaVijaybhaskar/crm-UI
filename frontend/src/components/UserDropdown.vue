<template>
  <Dropdown :options="dropdownItems" v-bind="$attrs">
    <template #default="{ open }">
      <button
        class="flex h-12 items-center rounded-5 py-2 duration-300 ease-in-out"
        :class="
          isCollapsed
            ? 'w-auto px-0'
            : open
              ? 'w-full px-2 bg-surface-elevation-3 shadow-sm'
              : 'w-full px-2 hover:bg-surface-gray-2'
        "
      >
        <img
          :src="sidebarLogo"
          :alt="brand.name || 'Astra CRM'"
          class="flex-shrink-0 object-contain"
          :class="isCollapsed ? 'size-8' : 'h-9 max-w-[168px]'"
        />
        <div
          class="flex flex-1 flex-col text-left duration-300 ease-in-out truncate"
          :class="
            isCollapsed
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 w-auto opacity-100'
          "
        >
          <div
            v-if="customBrandLogo"
            class="text-base-medium leading-none text-ink-gray-9 truncate"
          >
            {{ __(brand.name || 'Astra CRM') }}
          </div>
          <div
            class="text-sm leading-none text-ink-gray-7 truncate"
            :class="customBrandLogo ? 'mt-1' : ''"
          >
            {{ user.full_name }}
          </div>
        </div>
        <div
          class="duration-300 ease-in-out"
          :class="
            isCollapsed
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 w-auto opacity-100'
          "
        >
          <span
            class="lucide-chevron-down size-4 text-ink-gray-5"
            aria-hidden="true"
          />
        </div>
      </button>
    </template>
  </Dropdown>
</template>

<script setup>
import FrappeCloudIcon from '@/components/Icons/FrappeCloudIcon.vue'
import AppsIcon from '@/components/Icons/AppsIcon.vue'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { getSettings } from '@/stores/settings'
import { showSettings, isMobileView } from '@/composables/settings'
import { showAboutModal } from '@/composables/modals'
import { confirmLoginToFrappeCloud } from '@/composables/frappecloud'
import { spriteIcon } from '@/utils/spriteIcon'
import { createResource, Dropdown } from 'frappe-ui'
import { computed, h, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { ASTRA_LOGO_ON_DARK, ASTRA_MARK } from '@/assets/brand'

const router = useRouter()

const props = defineProps({
  isCollapsed: { type: Boolean, default: false },
})

const { settings, brand } = getSettings()
const { logout } = sessionStore()
const { getUser, isAdmin } = usersStore()

const user = computed(() => getUser() || {})
const userIsAdmin = computed(() => isAdmin())

// Brand Settings upload wins; otherwise the Astra lockup tuned for the dark rail.
const customBrandLogo = computed(() => settings.value?.brand_logo || '')
const sidebarLogo = computed(() => {
  if (customBrandLogo.value) return customBrandLogo.value
  return props.isCollapsed ? ASTRA_MARK : ASTRA_LOGO_ON_DARK
})

const apps = createResource({
  url: 'frappe.apps.get_apps',
  cache: 'apps',
  auto: true,
})

const dropdownItems = computed(() => {
  if (!settings.value?.dropdown_items) return []

  let items = settings.value.dropdown_items

  let _dropdownItems = [
    {
      group: 'Dropdown Items',
      hideLabel: true,
      options: [],
    },
  ]

  items.forEach((item) => {
    if (item.hidden) return
    if (item.type !== 'Separator') {
      _dropdownItems[_dropdownItems.length - 1].options.push(
        dropdownItemObj(item),
      )
    } else {
      _dropdownItems.push({
        group: '',
        hideLabel: true,
        options: [],
      })
    }
  })

  // Always expose Legal notices after About (post sign-in only — this menu is auth-gated).
  ensureLegalNoticesLink(_dropdownItems)

  return _dropdownItems
})

function ensureLegalNoticesLink(groups) {
  const hasLegal = groups.some((g) =>
    (g.options || []).some(
      (opt) => opt.label === __('Legal notices') || opt._name1 === 'legal_notices',
    ),
  )
  if (hasLegal) return

  const legalItem = {
    icon: spriteIcon('file-text'),
    label: __('Legal notices'),
    onClick: () => router.push({ name: 'Legal Notices' }),
  }

  for (const group of groups) {
    const opts = group.options || []
    const aboutIdx = opts.findIndex(
      (opt) => opt.label === __('About') || opt._name1 === 'about',
    )
    if (aboutIdx !== -1) {
      opts.splice(aboutIdx + 1, 0, legalItem)
      return
    }
  }

  if (groups.length) {
    groups[0].options = groups[0].options || []
    groups[0].options.push(legalItem)
  }
}

function dropdownItemObj(item) {
  let _item = JSON.parse(JSON.stringify(item))
  let icon = _item.icon || 'external-link'
  if (typeof icon === 'string' && icon.startsWith('<svg')) {
    icon = markRaw(h('div', { innerHTML: icon }))
  }
  _item.icon = spriteIcon(icon)

  if (_item.is_standard) {
    return getStandardItem(_item)
  }

  return {
    icon: _item.icon,
    label: __(_item.label),
    onClick: () =>
      window.open(_item.route, _item.open_in_new_window ? '_blank' : ''),
  }
}

function getStandardItem(item) {
  switch (item.name1) {
    case 'app_selector':
      return {
        icon: markRaw(AppsIcon),
        label: __(item.label),
        submenu: appMenuItems(),
        // Non-admins get an empty switcher; hide the entry entirely.
        condition: () => userIsAdmin.value && appMenuItems().length > 0,
      }
    case 'settings':
      return {
        icon: item.icon,
        label: __(item.label),
        onClick: () => (showSettings.value = true),
        condition: () => !isMobileView.value,
      }
    case 'login_to_fc':
      return {
        icon: h(FrappeCloudIcon),
        label: __(item.label),
        onClick: () => confirmLoginToFrappeCloud(),
        condition: () => !isMobileView.value && window.is_fc_site,
      }
    case 'about':
      return {
        _name1: 'about',
        icon: item.icon,
        label: __(item.label),
        onClick: () => (showAboutModal.value = true),
      }
    case 'legal_notices':
      return {
        _name1: 'legal_notices',
        icon: item.icon,
        label: __(item.label),
        onClick: () => router.push({ name: 'Legal Notices' }),
      }
    case 'logout':
      return {
        icon: item.icon,
        label: __(item.label),
        onClick: () => logout.submit(),
      }
  }
}

function appMenuItems() {
  return visibleApps(apps.data).map((app) => ({
    label: app.title,
    onClick: () => (window.location.href = app.route),
    slots: {
      prefix: () => h('img', { class: 'size-5 rounded-4', src: app.logo }),
    },
  }))
}

/** Non-admins: no Desk / WhatsApp / other apps. Admins: Desk → Admin. */
function visibleApps(data) {
  if (!userIsAdmin.value) return []
  return [
    {
      name: 'frappe',
      logo: '/assets/frappe/images/framework.png',
      title: __('Admin'),
      route: '/desk',
    },
    ...(data || [])
      .filter((app) => app.name !== 'crm')
      .map((app) => ({
        name: app.name,
        logo: app.logo,
        title: __(app.title),
        route: app.route,
      })),
  ]
}
</script>
