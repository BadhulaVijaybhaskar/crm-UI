<template>
  <div
    class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg [text-rendering:geometricPrecision]"
  >
    <div class="min-h-0 flex-1 overflow-y-auto">
      <header class="flex items-center gap-3 px-crm-page-x pb-3.5 pt-[19px]">
        <div class="min-w-0">
          <h1
            class="m-0 text-[20px] font-semibold leading-[1.45] tracking-[-0.015em] text-crm-fg"
          >
            {{ __('Call logs') }}
          </h1>
          <p
            class="relative top-px m-0 -mt-px text-[13px] leading-[1.45] tracking-[-0.005em] text-crm-muted-fg"
          >
            {{ __('Calls logged by Astra Connect or by hand') }}
          </p>
        </div>
        <div class="flex-1" />
        <AstraButton size="sm" :label="__('Log a call')" @click="createCallLog">
          <template #prefix>
            <LucidePlus class="size-3.5" aria-hidden="true" />
          </template>
        </AstraButton>
      </header>

      <div
        class="flex h-[38px] items-start px-crm-page-x shadow-[inset_0_-1px_0_var(--crm-border)]"
        role="tablist"
        :aria-label="__('Call logs')"
      >
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          role="tab"
          :aria-selected="activeTab === tab.value"
          class="inline-flex h-[38px] items-center gap-1.5 whitespace-nowrap border-b-2 px-3 text-[12.5px]"
          :class="
            activeTab === tab.value
              ? 'border-crm-primary font-semibold text-crm-fg'
              : 'border-transparent font-medium text-crm-muted-fg'
          "
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
          <span class="text-[11px] font-medium text-crm-faint">{{ tab.count }}</span>
        </button>
        <span
          class="inline-flex h-[38px] items-center gap-1.5 whitespace-nowrap border-b-2 border-transparent px-3 text-[12.5px] font-semibold text-crm-primary"
        >
          <LucidePlus class="size-3.5" aria-hidden="true" />
          {{ __('Save view') }}
        </span>
      </div>

      <div class="flex h-12 items-center gap-2 px-crm-page-x pt-[2px]">
        <label
          class="relative inline-flex h-crm-control-sm items-center gap-1.5 rounded-crm-control-sm border border-crm-border-strong bg-crm-card pl-[10px] pr-[9px] text-[12.5px] font-medium"
        >
          <span class="text-crm-muted-fg">{{ __('Logged by') }}</span>
          <span class="font-semibold text-crm-fg">{{ loggedByLabel }}</span>
          <LucideChevronDown class="size-3.5 text-crm-faint" aria-hidden="true" />
          <select
            v-model="loggedBy"
            class="absolute inset-0 cursor-pointer opacity-0"
            :aria-label="__('Logged by')"
          >
            <option value="">{{ __('Any') }}</option>
            <option v-for="u in crmUsers" :key="u.name" :value="u.name">
              {{ u.full_name || u.name }}
            </option>
          </select>
        </label>
        <button
          type="button"
          class="inline-flex h-crm-control-sm items-center gap-1.5 rounded-crm-control-sm border border-crm-primary bg-crm-primary-soft px-[9px] text-[12.5px] font-medium"
          @click="days = days === 30 ? 0 : 30"
        >
          <span class="text-crm-muted-fg">{{ __('Started') }}</span>
          <span class="font-semibold text-crm-primary">
            {{ days ? __('Last 30 days') : __('Any time') }}
          </span>
          <LucideX v-if="days" class="size-3.5 text-crm-faint" aria-hidden="true" />
        </button>
        <AstraButton size="sm" class="!px-[9px]" :label="__('Filter')">
          <template #prefix>
            <LucidePlus class="size-3.5 text-crm-faint" aria-hidden="true" />
          </template>
        </AstraButton>
        <div class="flex-1" />
        <span class="text-[12.5px] font-semibold text-crm-muted-fg">
          {{ __('Export') }}
        </span>
      </div>

      <div
        v-if="board.loading && !board.data"
        class="px-crm-page-x text-crm-body text-crm-muted-fg"
      >
        {{ __('Loading…') }}
      </div>

      <AstraEmptyState
        v-else-if="board.data && !rows.length"
        :title="__('No call logs yet')"
        :body="
          __(
            'Calls made through Astra Connect are logged here, along with calls you log by hand on a lead or deal.',
          )
        "
      >
        <AstraButton variant="primary" :label="__('Log a call')" @click="createCallLog" />
      </AstraEmptyState>

      <div
        v-else
        class="grid items-start gap-4 px-crm-page-x pb-6 lg:grid-cols-[1fr_300px]"
      >
        <section
          class="min-w-0 overflow-hidden rounded-crm-panel border border-crm-border bg-crm-card"
        >
          <div
            class="grid h-[34px] items-center border-b border-crm-border bg-crm-muted pt-[3px] text-[11px] font-semibold uppercase tracking-[0.06em] text-crm-muted-fg"
            :style="{ gridTemplateColumns: COLUMNS }"
          >
            <span />
            <span>{{ __('Contact') }}</span>
            <span>{{ __('Status') }}</span>
            <span class="pr-5 text-right">{{ __('Duration') }}</span>
            <span>{{ __('Outcome') }}</span>
            <span>{{ __('Disposition') }}</span>
            <span>{{ __('Started') }}</span>
          </div>
          <div
            v-for="(row, index) in rows"
            :key="row.name"
            class="grid h-[44px] cursor-pointer items-center text-[12.5px]"
            :class="[
              index ? 'border-t border-crm-border pt-px' : 'pt-[3px]',
              selectedName === row.name
                ? 'bg-crm-row-selected'
                : 'hover:bg-crm-row-hover',
            ]"
            :style="{ gridTemplateColumns: COLUMNS }"
            role="button"
            tabindex="0"
            :aria-pressed="selectedName === row.name"
            @click="selectedName = row.name"
            @keydown.enter="selectedName = row.name"
          >
            <span
              class="ml-2.5 flex size-5 items-center justify-center rounded-[5px]"
              :class="
                row.type === 'Incoming' && row.channel !== 'whatsapp'
                  ? 'bg-crm-blue-soft text-crm-blue'
                  : 'bg-crm-success-soft text-crm-success'
              "
              aria-hidden="true"
            >
              <component :is="directionIcon(row)" class="size-3" />
            </span>
            <div class="flex min-w-0 items-center gap-[11px]">
              <span
                class="flex size-6 shrink-0 items-center justify-center rounded-full bg-crm-primary-soft text-[9.5px] font-bold text-crm-primary"
                aria-hidden="true"
              >
                {{ initialsFrom(row.contact_name || '') }}
              </span>
              <div class="flex min-w-0 flex-col leading-[1.3]">
                <b
                  class="relative truncate text-[12.5px] font-semibold text-crm-fg"
                  :class="{ 'top-px': index }"
                >
                  {{ row.contact_name }}
                </b>
                <span class="truncate text-[11.5px] tracking-[-0.007em] text-crm-muted-fg">
                  {{ row.record_label }}
                </span>
              </div>
            </div>
            <span>
              <AstraBadge
                :label="__(row.status)"
                :tone="statusTone(row.status)"
              />
            </span>
            <span
              class="pr-5 text-right text-crm-fg"
              :class="{ 'relative -top-px': row.duration_label === '—' }"
              >{{ row.duration_label }}</span
            >
            <span class="truncate pr-3 text-crm-fg">{{ row.outcome || '—' }}</span>
            <span class="truncate text-crm-muted-fg">{{ row.disposition }}</span>
            <span class="truncate text-crm-muted-fg">{{ row.started_label }}</span>
          </div>
          <div
            v-if="board.data?.footer"
            class="flex h-[38px] items-center justify-between border-t border-crm-border px-4 text-[12px] text-crm-muted-fg"
          >
            <span>
              {{
                __('{0} of {1} calls · {2}', [
                  board.data.footer.shown,
                  board.data.footer.total,
                  board.data.footer.range,
                ])
              }}
            </span>
            <span>
              {{
                __('Avg duration {0} · {1} qualified', [
                  board.data.footer.avg_duration,
                  board.data.footer.qualified,
                ])
              }}
            </span>
          </div>
        </section>

        <aside
          v-if="detail.data"
          class="hidden self-stretch overflow-hidden rounded-crm-panel border border-crm-border bg-crm-card lg:block"
        >
          <div
            class="flex h-[51px] items-center gap-2.5 border-b border-crm-border px-[18px]"
          >
            <h2
              class="m-0 truncate text-[14px] font-semibold tracking-[-0.005em] text-crm-fg"
            >
              {{ __('Call') }} · {{ detail.data.contact_name }}
            </h2>
            <div class="flex-1" />
            <AstraBadge
              :label="__(detail.data.status)"
              :tone="statusTone(detail.data.status)"
            />
          </div>
          <div class="p-[17px]">
            <dl
              class="relative -top-px m-0 grid grid-cols-[100px_1fr] gap-x-3.5 gap-y-[9px] text-[12.5px] leading-[18px]"
            >
              <dt class="text-crm-muted-fg">{{ __('Type') }}</dt>
              <dd class="m-0 font-medium text-crm-fg">{{ detail.data.type_label }}</dd>
              <dt class="text-crm-muted-fg">{{ __('To') }}</dt>
              <dd class="m-0 font-medium text-crm-fg">{{ detail.data.to || '—' }}</dd>
              <dt class="text-crm-muted-fg">{{ __('Started') }}</dt>
              <dd class="m-0 font-medium text-crm-fg">{{ detail.data.started_detail }}</dd>
              <dt class="text-crm-muted-fg">{{ __('Linked to') }}</dt>
              <dd class="m-0 font-medium">
                <router-link
                  v-if="recordRoute"
                  :to="recordRoute"
                  class="text-crm-primary hover:underline"
                >
                  {{ detail.data.linked_label }}
                </router-link>
                <span v-else class="text-crm-fg">{{ detail.data.linked_label || '—' }}</span>
              </dd>
              <dt class="text-crm-muted-fg">{{ __('Outcome') }}</dt>
              <dd class="m-0 font-medium text-crm-fg">{{ detail.data.outcome || '—' }}</dd>
              <dt class="text-crm-muted-fg">{{ __('Disposition') }}</dt>
              <dd class="m-0 font-medium text-crm-fg">{{ detail.data.disposition }}</dd>
              <dt class="text-crm-muted-fg">{{ __('Qualified') }}</dt>
              <dd class="m-0">
                <AstraBadge
                  :label="detail.data.qualified ? __('Yes') : __('No')"
                  :tone="detail.data.qualified ? 'ok' : 'mute'"
                />
              </dd>
              <dt class="text-crm-muted-fg">{{ __('Logged by') }}</dt>
              <dd class="m-0">
                <AstraBadge :label="detail.data.logged_by" tone="teal" />
              </dd>
            </dl>
            <div
              v-if="detail.data.summary"
              class="mt-3.5 rounded-crm-card border border-crm-border bg-crm-muted py-2.5 pl-3 pr-1.5 text-[12.5px] leading-[1.45] text-crm-muted-fg"
            >
              <b class="mb-[5px] block font-semibold text-crm-fg">{{ __('Summary') }}</b>
              {{ detail.data.summary }}
            </div>
            <AstraButton
              v-if="detail.data.has_recording && connectReady"
              size="sm"
              block
              class="mt-[9px] whitespace-nowrap"
              :label="__('Recording & transcript in Astra Connect')"
              @click="openAstraConnect('calls')"
            >
              <template #prefix>
                <LucidePlay class="size-3.5 shrink-0" aria-hidden="true" />
              </template>
              <template #suffix>
                <LucideExternalLink class="size-3.5 shrink-0" aria-hidden="true" />
              </template>
            </AstraButton>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { createResource, usePageMeta } from 'frappe-ui'
import LucideArrowDownLeft from '~icons/lucide/arrow-down-left'
import LucideArrowUpRight from '~icons/lucide/arrow-up-right'
import LucideChevronDown from '~icons/lucide/chevron-down'
import LucideExternalLink from '~icons/lucide/external-link'
import LucideMessageCircle from '~icons/lucide/message-circle'
import LucidePlay from '~icons/lucide/play'
import LucidePlus from '~icons/lucide/plus'
import LucideX from '~icons/lucide/x'
import { AstraBadge, AstraButton, AstraEmptyState } from '@/components/astra'
import { initialsFrom } from '@/components/astra/format'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { usersStore } from '@/stores/users'
import { isAstraConnectConfigured, openAstraConnect } from '@/utils/astraConnect'
import { useTelemetry } from '@framework/ui/telemetry'
import { getSettings } from '@/stores/settings'
import { ASTRA_FAVICON } from '@/assets/brand'

const COLUMNS = '52px 201px 104px 83px 175px 107px 1fr'

const { brand } = getSettings()
const { crmUsers: crmUsersRef } = usersStore()
const { showModal } = useDoctypeModal()
const { capture } = useTelemetry()

const crmUsers = computed(() => crmUsersRef.value || [])
const activeTab = ref('all')
const loggedBy = ref('')
const days = ref(30)
const selectedName = ref(null)
const connectReady = computed(() => isAstraConnectConfigured())

const board = createResource({
  url: 'crm.api.call_log_board.get_call_logs',
  auto: true,
  makeParams: () => ({
    tab: activeTab.value,
    days: days.value || 0,
    logged_by: loggedBy.value || undefined,
  }),
})

const detail = createResource({
  url: 'crm.api.call_log_board.get_call_log_detail',
  makeParams: () => ({ name: selectedName.value }),
})

const rows = computed(() => board.data?.rows || [])
const counts = computed(() => board.data?.tabs || {})
const tabs = computed(() => [
  { value: 'all', label: __('All calls'), count: counts.value.all ?? 0 },
  { value: 'mine', label: __('Mine'), count: counts.value.mine ?? 0 },
  { value: 'missed', label: __('Missed'), count: counts.value.missed ?? 0 },
  { value: 'qualified', label: __('Qualified'), count: counts.value.qualified ?? 0 },
])
const loggedByLabel = computed(() => {
  const u = crmUsers.value.find((x) => x.name === loggedBy.value)
  return u ? u.full_name || u.name : __('Any')
})
const recordRoute = computed(() => {
  const d = detail.data
  if (!d?.reference_docname) return null
  if (d.reference_doctype === 'CRM Deal')
    return { name: 'Deal', params: { dealId: d.reference_docname } }
  if (d.reference_doctype === 'CRM Lead')
    return { name: 'Lead', params: { leadId: d.reference_docname } }
  return null
})

watch([activeTab, loggedBy, days], () => board.reload())
watch(
  () => board.data,
  () => {
    const names = rows.value.map((r) => r.name)
    if (!names.length) {
      selectedName.value = null
    } else if (!selectedName.value || !names.includes(selectedName.value)) {
      selectedName.value = names[0]
    }
  },
)
watch(selectedName, (name) => name && detail.fetch(), { immediate: true })

function directionIcon(row) {
  if (row.channel === 'whatsapp') return LucideMessageCircle
  return row.type === 'Incoming' ? LucideArrowDownLeft : LucideArrowUpRight
}

function statusTone(status) {
  const key = String(status || '').toLowerCase()
  if (key === 'completed') return 'ok'
  if (['no answer', 'busy', 'canceled'].includes(key)) return 'warn'
  if (key === 'failed') return 'bad'
  return 'mute'
}

function createCallLog() {
  showModal({
    doctype: 'CRM Call Log',
    title: 'Call Log',
    callbacks: {
      afterInsert: () => {
        capture('call_log_created')
        board.reload()
      },
    },
  })
}

onMounted(() => {
  const searchParams = new URLSearchParams(window.location.search)
  const name = searchParams.get('open')
  if (!name) return
  selectedName.value = name
  searchParams.delete('open')
  window.history.replaceState(null, '', window.location.pathname)
})

usePageMeta(() => ({
  title: __('Call logs'),
  icon: brand?.favicon || ASTRA_FAVICON,
}))
</script>
