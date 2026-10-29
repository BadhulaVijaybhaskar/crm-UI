<template>
  <div class="astra-shell__topbar relative">
    <button
      type="button"
      class="flex h-[34px] w-crm-search items-center gap-2 rounded-crm-control border border-crm-border bg-crm-muted px-2.5 text-left text-crm-label text-crm-faint hover:text-crm-muted-fg"
      @click="openCommandPalette"
    >
      <FigmaSearchIcon class="relative top-px size-3.5 shrink-0" />
      <span class="relative top-px min-w-0 flex-1 truncate">
        {{ __('Search leads, deals, contacts, companies') }}
      </span>
      <!-- crm.css .gsearch kbd — Inter 600/11px (override Tailwind kbd mono preflight) -->
      <kbd
        class="ml-auto rounded-[4px] border border-crm-border-strong bg-crm-card px-[5px] py-px text-[11px] font-semibold text-crm-muted-fg"
        style="
          font-family: Inter, var(--font-sans);
          font-weight: 600;
          font-size: 11px;
          line-height: normal;
          font-feature-settings: normal;
        "
      >
        Ctrl K
      </kbd>
    </button>

    <div class="flex-1" />

    <!-- crm.css .abar gap:10px — CallUI is out-of-flow so it cannot shift New/bell -->
    <div class="flex items-center gap-2.5">
      <Dropdown :options="newOptions">
        <AstraButton variant="primary" size="sm" :label="__('New')">
          <template #prefix>
            <FigmaPlusIcon class="size-3.5 shrink-0" />
          </template>
        </AstraButton>
      </Dropdown>

      <button
        type="button"
        class="relative inline-flex size-[34px] shrink-0 items-center justify-center rounded-crm-control border border-crm-border bg-crm-card text-crm-muted-fg hover:text-crm-fg"
        :aria-label="__('Notifications')"
        @click="toggleNotifications"
      >
        <FigmaBellIcon class="size-3.5" />
        <!-- crm.css .ibtn .dotn — 7×7 incl. 2px card border (border-box) -->
        <span
          v-if="unreadNotificationsCount"
          class="pointer-events-none absolute right-[7px] top-[6px] box-border size-[7px] rounded-full border-2 border-crm-card bg-crm-danger"
        />
      </button>
    </div>

    <!-- zero-size host: telephony popups are fixed/absolute and must not shift abar -->
    <div class="absolute left-0 top-0 h-0 w-0 overflow-visible">
      <CallUI />
    </div>
  </div>

  <div id="app-header" class="astra-shell__page-header" />
</template>

<script setup>
import CallUI from '@/components/Telephony/CallUI.vue'
import AstraButton from '@/components/astra/AstraButton.vue'
import {
  FigmaBellIcon,
  FigmaPlusIcon,
  FigmaSearchIcon,
} from '@/components/Icons/FigmaNavIcons'
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
