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
            {{ __('Work queue') }}
          </h1>
          <p
            class="relative top-px m-0 -mt-px text-[13px] leading-[1.45] text-crm-muted-fg"
          >
            {{ __('What needs you next, ranked. Showing your records.') }}
          </p>
        </div>
      </header>

      <div class="flex h-11 items-center gap-2 px-crm-page-x pb-2.5">
        <div
          class="relative top-px flex gap-0.5 rounded-crm-control border border-crm-border bg-crm-muted p-[3px]"
          role="tablist"
          :aria-label="__('Queue')"
        >
          <button
            v-for="tab in tabs"
            :key="tab.value"
            type="button"
            role="tab"
            :aria-selected="activeTab === tab.value"
            class="inline-flex h-[26px] items-center gap-1.5 rounded-crm-chip px-2.5 text-[12.5px]"
            :class="
              activeTab === tab.value
                ? 'bg-crm-card font-semibold text-crm-fg shadow-[0_0_0_1px_var(--crm-border)]'
                : 'font-medium text-crm-muted-fg'
            "
            @click="setTab(tab.value)"
          >
            {{ tab.label }}
            <span
              class="text-[11px] font-semibold"
              :class="
                activeTab === tab.value ? 'text-crm-primary' : 'text-crm-faint'
              "
            >
              {{ tab.count }}
            </span>
          </button>
        </div>
        <span class="mx-1 block h-6 w-px bg-crm-border" aria-hidden="true" />
        <label
          class="relative top-px inline-flex h-crm-control-sm items-center gap-1.5 rounded-crm-control-sm border border-crm-border-strong bg-crm-card pl-3 pr-2.5 text-[12.5px] font-medium"
        >
          <span class="text-crm-muted-fg">{{ __('Priority') }}</span>
          <span class="font-semibold text-crm-fg">{{ priorityLabel }}</span>
          <LucideChevronDown
            class="size-3.5 text-crm-faint"
            aria-hidden="true"
          />
          <select
            v-model="priorityFilter"
            class="absolute inset-0 cursor-pointer opacity-0"
            :aria-label="__('Priority')"
            @change="reload"
          >
            <option
              v-for="opt in priorityOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </option>
          </select>
        </label>
        <div class="flex-1" />
        <span class="text-[12px] text-crm-muted-fg">{{ updatedLabel }}</span>
        <AstraButton
          size="sm"
          variant="ghost"
          :label="__('Refresh')"
          :loading="queue.loading"
          @click="reload"
        >
          <template #prefix>
            <LucideRefreshCw
              v-if="!queue.loading"
              class="size-3.5"
              aria-hidden="true"
            />
          </template>
        </AstraButton>
      </div>

      <div
        v-if="queue.loading && !queue.data"
        class="px-crm-page-x text-crm-body text-crm-muted-fg"
      >
        {{ __('Loading…') }}
      </div>

      <div
        v-else
        class="grid items-start gap-4 px-crm-page-x pb-6 lg:grid-cols-[1fr_340px]"
      >
        <section
          class="min-w-0 overflow-hidden rounded-crm-panel border border-crm-border bg-crm-card"
        >
          <AstraEmptyState
            v-if="!sections.length && !clearedCount"
            :title="__('Queue is clear')"
            :body="__('No follow-ups or quiet leads need you right now.')"
          />
          <template v-for="(section, index) in sections" :key="section.id">
            <div
              class="flex items-center gap-2.5 px-4 text-[13px]"
              :class="
                index ? 'h-[49px] border-t border-crm-border pt-1.5' : 'h-[46px] pt-1'
              "
            >
              <span
                class="flex size-[26px] shrink-0 items-center justify-center rounded-crm-control-sm"
                :class="sectionIconClass(section.id)"
              >
                <component
                  :is="sectionIcon(section.id)"
                  class="size-3.5"
                  aria-hidden="true"
                />
              </span>
              <b class="font-semibold text-crm-fg">{{ section.label }}</b>
              <span class="text-[12px] font-semibold text-crm-muted-fg">
                {{ section.count ?? section.items?.length ?? 0 }}
              </span>
              <span
                v-if="section.description"
                class="truncate text-[12px] text-crm-faint"
              >
                {{ section.description }}
              </span>
            </div>
            <div
              v-for="item in section.items"
              :key="item.id"
              class="grid h-[56.67px] cursor-pointer grid-cols-[26px_190px_1fr_auto_86px_auto] items-center gap-2.5 border-t border-crm-border px-4"
              :class="
                selectedId === item.id
                  ? 'bg-crm-row-selected shadow-[inset_3px_0_0_var(--crm-primary)]'
                  : 'hover:bg-crm-row-hover'
              "
              role="button"
              tabindex="0"
              :aria-pressed="selectedId === item.id"
              @click="selectItem(item)"
              @keydown.enter="selectItem(item)"
            >
              <span
                class="flex size-[26px] items-center justify-center rounded-full bg-crm-primary-soft text-[10.5px] font-bold text-crm-primary"
                aria-hidden="true"
              >
                {{ initialsFrom(personName(item)) }}
              </span>
              <div class="flex min-w-0 flex-col pt-0.5 leading-[1.3]">
                <b class="truncate text-[12.5px] font-semibold text-crm-fg">
                  {{ personName(item) }}
                </b>
                <span class="mt-0.5 truncate text-[11.5px] text-crm-muted-fg">
                  {{ item.record_label }}
                </span>
              </div>
              <div class="flex min-w-0 flex-col pt-[5.5px] leading-[1.45]">
                <b class="truncate text-[12.5px] font-semibold text-crm-fg">
                  {{ item.title }}
                </b>
                <span
                  class="mt-[0.5px] truncate whitespace-nowrap text-[11.5px] text-crm-muted-fg"
                >
                  {{ itemMeta(item) }}
                </span>
              </div>
              <AstraBadge
                v-if="item.priority"
                :label="item.priority"
                :tone="priorityTone(item.priority)"
              />
              <span v-else />
              <span class="text-right text-[12px] text-crm-muted-fg">
                {{ item.due_label }}
              </span>
              <AstraButton
                v-if="primaryAction(item)"
                size="sm"
                :label="primaryAction(item).label"
                @click.stop="primaryAction(item).run()"
              >
                <template #prefix>
                  <component
                    :is="primaryAction(item).icon"
                    class="size-3.5"
                    aria-hidden="true"
                  />
                </template>
                <template v-if="primaryAction(item).external" #suffix>
                  <LucideExternalLink class="size-3.5" aria-hidden="true" />
                </template>
              </AstraButton>
              <span v-else />
            </div>
          </template>

          <div
            v-if="clearedCount"
            class="flex h-[51px] items-center gap-2.5 px-4 text-[13px]"
            :class="{ 'border-t border-crm-border': sections.length }"
          >
            <span
              class="flex size-[26px] shrink-0 items-center justify-center rounded-crm-control-sm bg-crm-success-soft text-crm-success"
            >
              <LucideCircleCheck class="size-3.5" aria-hidden="true" />
            </span>
            <b class="font-semibold text-crm-fg">{{ __('Cleared today') }}</b>
            <span class="text-[12px] font-semibold text-crm-muted-fg">
              {{ clearedCount }}
            </span>
            <span class="truncate text-[12px] text-crm-faint">
              {{ clearedSummary }}
            </span>
            <div class="flex-1" />
            <button
              type="button"
              class="inline-flex items-center gap-1 text-[12.5px] font-semibold text-crm-primary"
              :aria-expanded="showCleared"
              @click="showCleared = !showCleared"
            >
              {{ showCleared ? __('Hide') : __('Show') }}
              <component
                :is="showCleared ? LucideChevronUp : LucideChevronDown"
                class="size-3.5"
                aria-hidden="true"
              />
            </button>
          </div>
          <ul v-if="showCleared && clearedCount" class="m-0 list-none p-0">
            <li
              v-for="item in queue.data.cleared_today"
              :key="item.id"
              class="flex h-10 items-center gap-2.5 border-t border-crm-border pl-[52px] pr-4 text-[12.5px] text-crm-muted-fg"
            >
              <span class="truncate text-crm-fg">{{ item.title }}</span>
              <div class="flex-1" />
              <span v-if="item.modified" class="text-[12px]">
                {{ formatDate(item.modified, 'HH:mm') }}
              </span>
            </li>
          </ul>
        </section>

        <aside
          v-if="detail.data"
          class="hidden min-h-[538px] overflow-hidden rounded-crm-panel border border-crm-border bg-crm-card lg:block"
        >
          <div
            class="flex items-center gap-2.5 border-b border-crm-border px-[18px] py-3.5"
          >
            <h2
              class="m-0 truncate text-[14px] font-semibold leading-[21.5px] tracking-[-0.005em] text-crm-fg"
            >
              {{ detail.data.title }}
            </h2>
            <div class="flex-1" />
            <router-link
              v-if="detail.data.route"
              :to="detail.data.route"
              class="inline-flex shrink-0 items-center gap-1 text-[12.5px] font-semibold text-crm-primary hover:underline"
            >
              {{ openRecordLabel }}
              <LucideChevronRight class="size-3.5" aria-hidden="true" />
            </router-link>
          </div>
          <div class="px-4 pb-4 pt-[15px]">
            <div class="flex items-center gap-2.5">
              <AstraBadge
                v-if="detail.data.status"
                :label="detail.data.status"
                :tone="statusTone(detail.data.status)"
                dot
              />
              <span
                v-if="detail.data.temperature"
                class="inline-flex items-center gap-1 text-[11px] font-semibold"
                :class="tempClass(detail.data.temperature)"
              >
                <i class="block size-1.5 rounded-full bg-current" />
                {{ detail.data.temperature }}
              </span>
            </div>
            <p
              v-if="slaLine"
              class="m-0 mt-1.5 text-[11.5px] font-semibold text-crm-danger"
            >
              {{ slaLine }}
            </p>
            <dl
              v-if="detailRows.length"
              class="m-0 mt-3 grid grid-cols-[96px_1fr] gap-x-3 gap-y-[9px] text-[12.5px] leading-[18px]"
            >
              <template v-for="row in detailRows" :key="row.label">
                <dt class="text-crm-muted-fg">{{ row.label }}</dt>
                <dd class="m-0 min-w-0 truncate font-medium text-crm-fg">
                  {{ row.value }}
                </dd>
              </template>
            </dl>
            <div
              v-if="detail.data.last_call"
              class="mt-2.5 flex gap-2.5 rounded-crm-card border border-crm-border bg-crm-muted px-[13px] py-[11px] text-[12px] leading-[1.5] text-crm-muted-fg"
            >
              <LucidePhone
                class="mt-0.5 size-3.5 shrink-0"
                aria-hidden="true"
              />
              <div class="min-w-0">
                <b class="font-semibold text-crm-fg">{{ lastCallTitle }}</b>
                <br />
                {{ lastCallOutcome }}
              </div>
            </div>
            <div class="mt-[11px] flex gap-2">
              <AstraButton
                v-if="connectReady"
                size="sm"
                variant="primary"
                class="w-[230px]"
                :label="__('Call in Astra Connect')"
                @click="callSelected"
              >
                <template #prefix>
                  <LucidePhone class="size-3.5" aria-hidden="true" />
                </template>
                <template #suffix>
                  <LucideExternalLink class="size-3.5" aria-hidden="true" />
                </template>
              </AstraButton>
              <AstraButton
                v-if="selectedItem?.task"
                size="sm"
                class="flex-1"
                :label="__('Snooze')"
                :loading="snooze.loading"
                @click="snoozeSelected"
              />
            </div>
            <p
              v-if="detail.data.shortcuts"
              class="m-0 mt-[13px] text-[11.5px] text-crm-faint"
            >
              {{ __('Shortcuts: {0}', [detail.data.shortcuts]) }}
            </p>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, usePageMeta } from 'frappe-ui'
import LucideAlarmClock from '~icons/lucide/alarm-clock'
import LucideChevronDown from '~icons/lucide/chevron-down'
import LucideChevronRight from '~icons/lucide/chevron-right'
import LucideChevronUp from '~icons/lucide/chevron-up'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideExternalLink from '~icons/lucide/external-link'
import LucideEyeOff from '~icons/lucide/eye-off'
import LucideMail from '~icons/lucide/mail'
import LucidePhone from '~icons/lucide/phone'
import LucideRefreshCw from '~icons/lucide/refresh-cw'
import LucideStickyNote from '~icons/lucide/sticky-note'
import {
  AstraBadge,
  AstraButton,
  AstraEmptyState,
  STATUS_TONES,
  TEMPERATURE_TONES,
} from '@/components/astra'
import { initialsFrom } from '@/components/astra/format'
import { formatDate, sanitizeHTML } from '@/utils'
import {
  isAstraConnectConfigured,
  openConnectCompose,
} from '@/utils/astraConnect'
import { getSettings } from '@/stores/settings'
import { ASTRA_FAVICON } from '@/assets/brand'
import dayjs from 'dayjs'

const { brand } = getSettings()
const router = useRouter()
const activeTab = ref('all')
const priorityFilter = ref('High,Medium')
const selectedId = ref(null)
const selectedItem = ref(null)
const showCleared = ref(false)

const queue = createResource({
  url: 'crm.api.work_queue.get_work_queue',
  auto: true,
  cache: ['crm-work-queue', activeTab, priorityFilter],
  makeParams: () => ({
    tab: activeTab.value,
    priority: priorityFilter.value,
  }),
})

const detail = createResource({
  url: 'crm.api.work_queue.get_work_queue_detail',
  auto: false,
  makeParams: () => ({
    reference_doctype: selectedItem.value?.reference_doctype,
    reference_docname: selectedItem.value?.reference_docname,
  }),
})

const snooze = createResource({
  url: 'frappe.client.set_value',
  onSuccess: () => reload(),
})

const sections = computed(() => queue.data?.sections || [])
const counts = computed(() => queue.data?.counts || {})
const connectReady = computed(() => isAstraConnectConfigured())
const flatItems = computed(() => sections.value.flatMap((s) => s.items || []))

const tabs = computed(() => [
  { value: 'all', label: __('All'), count: counts.value.all ?? 0 },
  {
    value: 'follow_ups',
    label: __('Follow-ups'),
    count: counts.value.follow_ups ?? 0,
  },
  {
    value: 'quiet_leads',
    label: __('Quiet leads'),
    count: counts.value.quiet_leads ?? 0,
  },
])

const priorityOptions = computed(() => [
  { value: 'High,Medium', label: __('High, Medium') },
  { value: 'High,Medium,Low', label: __('Any') },
  { value: 'High', label: __('High') },
])

const priorityLabel = computed(
  () =>
    priorityOptions.value.find((o) => o.value === priorityFilter.value)
      ?.label || priorityFilter.value,
)

const clearedCount = computed(
  () => counts.value.cleared_today ?? (queue.data?.cleared_today || []).length,
)

const clearedSummary = computed(() => {
  if (queue.data?.cleared_summary) return queue.data.cleared_summary
  return (queue.data?.cleared_today || []).map((i) => i.title).join(', ')
})

const updatedLabel = computed(() => {
  const ts = queue.data?.updated_at
  if (!ts) return ''
  return __('Updated {0}', [formatDate(ts, 'HH:mm')])
})

const openRecordLabel = computed(() => {
  if (detail.data?.doctype === 'CRM Deal') return __('Open deal')
  if (detail.data?.doctype === 'CRM Lead') return __('Open lead')
  return __('Open record')
})

const detailRows = computed(() => {
  const d = detail.data
  if (!d) return []
  const rows = []
  if (d.organization) rows.push({ label: __('Company'), value: d.organization })
  if (d.source) rows.push({ label: __('Source'), value: d.source })
  if (d.mobile_no) rows.push({ label: __('Mobile'), value: d.mobile_no })
  if (d.email) rows.push({ label: __('Email'), value: d.email })
  if (d.lead_score != null && d.lead_score !== '')
    rows.push({ label: __('Lead score'), value: String(d.lead_score) })
  if (d.value != null) rows.push({ label: __('Value'), value: String(d.value) })
  if (d.next_step) rows.push({ label: __('Next step'), value: d.next_step })
  return rows
})

const slaLine = computed(() => {
  const d = detail.data
  if (d?.sla_label) return d.sla_label
  if (!d?.response_by || !d.sla_status) return ''
  if (
    !['First Response Due', 'Rolling Response Due', 'Failed'].includes(
      d.sla_status,
    )
  )
    return ''
  return d.sla_status
})

const lastCallTitle = computed(() => {
  const call = detail.data?.last_call
  const ts = call?.start_time || call?.creation
  if (!ts) return __('Last call')
  return __('Last call · {0}', [formatDate(ts, 'D MMM')])
})

const lastCallOutcome = computed(() => {
  const call = detail.data?.last_call
  if (!call) return ''
  const text = call.outcome || call.call_summary
  if (text) return __('Outcome: {0}', [text])
  return call.status || ''
})

watch(
  () => sections.value,
  () => {
    const flat = flatItems.value
    if (!flat.length) {
      selectedId.value = null
      selectedItem.value = null
      return
    }
    if (!selectedId.value || !flat.find((i) => i.id === selectedId.value)) {
      selectItem(flat[0])
    }
  },
  { immediate: true },
)

function setTab(value) {
  activeTab.value = value
  reload()
}

function reload() {
  queue.reload()
}

function selectItem(item) {
  selectedId.value = item.id
  selectedItem.value = item
  if (item.reference_doctype && item.reference_docname) {
    detail.reload()
  }
}

function personName(item) {
  return item.person_name || item.reference_title || item.title
}

function itemMeta(item) {
  return item.meta_label || stripHtml(item.description)
}

function sectionIcon(id) {
  if (id === 'quiet_leads') return LucideEyeOff
  return LucideAlarmClock
}

function sectionIconClass(id) {
  if (id === 'follow_ups') return 'bg-crm-warning-soft text-crm-warning'
  return 'bg-crm-neutral-soft text-crm-muted-fg'
}

function priorityTone(priority) {
  if (priority === 'High') return 'bad'
  if (priority === 'Medium') return 'warn'
  return 'mute'
}

function statusTone(status) {
  return STATUS_TONES[status] || 'mute'
}

function tempClass(temp) {
  const tone = TEMPERATURE_TONES[temp]
  if (tone === 'danger') return 'text-crm-danger'
  if (tone === 'warning') return 'text-crm-warning'
  return 'text-crm-muted-fg'
}

function stripHtml(html) {
  if (!html) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = sanitizeHTML(html)
  return (tmp.textContent || '').trim()
}

function itemActionKind(item) {
  if (item.action) return item.action
  if (item.kind === 'quiet_lead' || /call/i.test(item.title || ''))
    return 'call'
  if (/email|mail/i.test(item.title || '')) return 'email'
  return 'note'
}

function openRecord(item, hash = '') {
  if (item.reference_doctype === 'CRM Lead') {
    router.push({
      name: 'Lead',
      params: { leadId: item.reference_docname },
      hash,
    })
  } else if (item.reference_doctype === 'CRM Deal') {
    router.push({
      name: 'Deal',
      params: { dealId: item.reference_docname },
      hash,
    })
  }
}

function primaryAction(item) {
  const kind = itemActionKind(item)
  if (kind === 'call' && connectReady.value) {
    return {
      label: __('Call'),
      icon: LucidePhone,
      external: true,
      run: () =>
        openConnectCompose('calls', {
          recordType: item.reference_doctype,
          recordId: item.reference_docname,
          phone: item.mobile_no,
        }),
    }
  }
  if (kind === 'email' && connectReady.value) {
    return {
      label: __('Email'),
      icon: LucideMail,
      run: () =>
        openConnectCompose('messages', {
          recordType: item.reference_doctype,
          recordId: item.reference_docname,
        }),
    }
  }
  if (!item.reference_doctype) return null
  return {
    label: __('Log note'),
    icon: LucideStickyNote,
    run: () => openRecord(item, '#notes'),
  }
}

function callSelected() {
  const d = detail.data
  if (!d) return
  openConnectCompose('calls', {
    recordType: d.doctype,
    recordId: d.name,
    phone: d.mobile_no,
  })
}

function snoozeSelected() {
  const task = selectedItem.value?.task
  if (!task) return
  snooze.submit({
    doctype: 'CRM Task',
    name: task,
    fieldname: 'due_date',
    value: dayjs()
      .add(1, 'day')
      .hour(9)
      .minute(0)
      .second(0)
      .format('YYYY-MM-DD HH:mm:ss'),
  })
}

function moveSelection(step) {
  const flat = flatItems.value
  if (!flat.length) return
  const index = flat.findIndex((i) => i.id === selectedId.value)
  const next = Math.min(flat.length - 1, Math.max(0, index + step))
  selectItem(flat[next])
}

function onKeydown(event) {
  if (event.metaKey || event.ctrlKey || event.altKey) return
  const target = event.target
  if (
    target?.isContentEditable ||
    ['INPUT', 'TEXTAREA', 'SELECT'].includes(target?.tagName)
  )
    return
  const item = selectedItem.value
  const key = event.key.toLowerCase()
  if (key === 'j') moveSelection(1)
  else if (key === 'k') moveSelection(-1)
  else if (!item) return
  else if (key === 'c' && connectReady.value) callSelected()
  else if (key === 'n') openRecord(item, '#notes')
  else if (key === 'e') openRecord(item)
  else return
  event.preventDefault()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

usePageMeta(() => ({
  title: __('Work queue'),
  icon: brand?.favicon || ASTRA_FAVICON,
}))
</script>
