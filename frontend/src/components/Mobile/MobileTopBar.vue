<template>
  <div
    class="flex h-[52px] shrink-0 items-center gap-3 border-b border-crm-border bg-crm-card pl-[14px] pr-[13px]"
  >
    <template v-if="settings?.brand_logo">
      <img :src="settings.brand_logo" :alt="brand.name || 'Astra CRM'" class="block h-[22px] w-auto" />
    </template>
    <template v-else>
      <img :src="ASTRA_LOGO" :alt="brand.name || 'Astra CRM'" class="astra-logo-light block h-[22px] w-auto" />
      <img :src="ASTRA_LOGO_ON_DARK" :alt="brand.name || 'Astra CRM'" class="astra-logo-dark hidden h-[22px] w-auto" />
    </template>
    <div id="app-header" class="min-w-0 flex-1" />
    <button
      type="button"
      class="inline-flex size-8 items-center justify-center text-crm-muted-fg"
      :aria-label="__('Search')"
      @click="openCommandPalette"
    >
      <FigmaSearchIcon class="size-3.5" />
    </button>
    <button
      type="button"
      class="relative inline-flex size-8 items-center justify-center text-crm-muted-fg"
      :aria-label="__('Notifications')"
      @click="router.push({ name: 'Notifications' })"
    >
      <FigmaBellIcon class="size-3.5" />
      <span
        v-if="unreadNotificationsCount"
        class="absolute right-[7px] top-[6px] size-[7px] rounded-full border-2 border-crm-card bg-crm-danger"
      />
    </button>
    <button
      type="button"
      class="inline-flex"
      :aria-label="__('Menu')"
      @click="sidebarOpened = !sidebarOpened"
    >
      <AstraAvatar :name="user.full_name || user.email || '?'" size="sm" />
    </button>
  </div>
  <CallUI class="mr-3 mt-2" />
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import CallUI from '@/components/Telephony/CallUI.vue'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import { FigmaBellIcon, FigmaSearchIcon } from '@/components/Icons/FigmaNavIcons'
import { mobileSidebarOpened as sidebarOpened } from '@/composables/settings'
import { openCommandPalette } from '@/composables/useCommandPalette'
import { unreadNotificationsCount } from '@/stores/notifications'
import { getSettings } from '@/stores/settings'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { ASTRA_LOGO, ASTRA_LOGO_ON_DARK } from '@/assets/brand'

const router = useRouter()
const { settings, brand } = getSettings()
const { getUser } = usersStore()
const session = sessionStore()

const user = computed(() => getUser(session.user) || {})
</script>

<style>
[data-theme='dark'] .astra-logo-light {
  display: none;
}
[data-theme='dark'] .astra-logo-dark {
  display: block;
}
</style>
