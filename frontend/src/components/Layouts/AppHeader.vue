<template>
  <div class="astra-shell__topbar">
    <button
      type="button"
      class="flex h-[34px] w-crm-search items-center gap-2 rounded-crm-control bg-crm-muted px-2.5 text-left text-crm-label text-crm-faint shadow-[inset_0_0_0_1px_var(--crm-border)] hover:text-crm-muted-fg"
      @click="openCommandPalette"
    >
      <Icon
        icon="lucide-search"
        class="size-4 shrink-0"
        aria-hidden="true"
      />
      <span class="min-w-0 flex-1 truncate">
        {{ __('Search leads, deals, contacts, companies') }}
      </span>
      <kbd
        class="rounded-crm-mini border border-crm-border-strong bg-crm-card px-[5px] py-px text-crm-micro font-semibold text-crm-muted-fg"
      >
        Ctrl K
      </kbd>
    </button>

    <div class="flex-1" />

    <div class="flex items-center gap-2">
      <Dropdown :options="newOptions">
        <AstraButton variant="primary" size="sm">
          <template #prefix>
            <Icon icon="lucide-plus" class="size-4" aria-hidden="true" />
          </template>
          {{ __('New') }}
        </AstraButton>
      </Dropdown>

      <button
        type="button"
        class="relative inline-flex size-[34px] items-center justify-center rounded-crm-control bg-crm-card text-crm-muted-fg shadow-[inset_0_0_0_1px_var(--crm-border)] hover:text-crm-fg"
        :aria-label="__('Notifications')"
        @click="toggleNotifications"
      >
        <Icon icon="lucide-bell" class="size-4" aria-hidden="true" />
        <span
          v-if="unreadNotificationsCount"
          class="absolute right-[7px] top-1.5 size-[7px] rounded-full bg-crm-danger ring-2 ring-crm-card"
        />
      </button>

      <CallUI />
    </div>
  </div>

  <div id="app-header" class="astra-shell__page-header" />
</template>

<script setup>
import CallUI from '@/components/Telephony/CallUI.vue'
import AstraButton from '@/components/astra/AstraButton.vue'
import Icon from '@/components/Icon.vue'
import { openCommandPalette } from '@/composables/useCommandPalette'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useBroadcast } from '@/composables/useBroadcast.js'
import {
  unreadNotificationsCount,
  notificationsStore,
} from '@/stores/notifications'
import { Dropdown } from 'frappe-ui'
import { computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const { toggle } = notificationsStore()
const { showModal } = useDoctypeModal()
const { send } = useBroadcast()

function toggleNotifications() {
  toggle()
}

async function createLead() {
  await router.push({ name: 'Leads' })
  await nextTick()
  send('trigger_lead_create', true)
}

async function createDeal() {
  await router.push({ name: 'Deals' })
  await nextTick()
  send('trigger_deal_create', true)
}

const newOptions = computed(() => [
  {
    group: __('Create'),
    hideLabel: true,
    options: [
      { label: __('Lead'), onClick: createLead },
      { label: __('Deal'), onClick: createDeal },
      {
        label: __('Contact'),
        onClick: () => showModal({ doctype: 'Contact', title: __('Contact') }),
      },
      {
        label: __('Company'),
        onClick: () =>
          showModal({
            doctype: 'CRM Organization',
            title: __('Organization'),
          }),
      },
    ],
  },
])
</script>
