<template>
  <div class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg">
    <AstraPageHeader
      :title="__('Work queue')"
      :description="__('What needs you next, ranked. Showing your records.')"
    >
      <template #actions>
        <span class="text-crm-meta text-crm-muted-fg">
          {{ updatedLabel }}
        </span>
        <AstraButton
          size="sm"
          variant="secondary"
          :label="__('Refresh')"
          :loading="queue.loading"
          @click="reload"
        />
      </template>
    </AstraPageHeader>

    <div
      class="flex flex-wrap items-center gap-2 border-b border-crm-border bg-crm-card px-crm-page-x py-2.5"
    >
      <button
        v-for="tab in tabs"
        :key="tab.value"
        type="button"
        class="inline-flex h-crm-control-sm items-center gap-1.5 rounded-full px-3 text-crm-label font-semibold"
        :class="
          activeTab === tab.value
            ? 'bg-crm-primary-soft text-crm-primary'
            : 'bg-crm-muted text-crm-muted-fg'
        "
        @click="setTab(tab.value)"
      >
        {{ tab.label }}
        <span v-if="tab.count != null">{{ tab.count }}</span>
      </button>
      <div class="ml-auto flex items-center gap-2">
        <label class="sr-only" for="wq-priority">{{ __('Priority') }}</label>
        <select
          id="wq-priority"
          v-model="priorityFilter"
          class="h-crm-control-sm rounded-crm-control-sm border-0 bg-crm-card px-2.5 text-crm-label shadow-[inset_0_0_0_1px_var(--crm-border-strong)]"
          @change="reload"
        >
          <option value="High,Medium">{{ __('Priority: High, Medium') }}</option>
          <option value="High,Medium,Low">{{ __('Priority: Any') }}</option>
          <option value="High">{{ __('Priority: High') }}</option>
        </select>
      </div>
    </div>

    <div class="flex min-h-0 flex-1">
      <div class="min-w-0 flex-1 overflow-y-auto">
        <div
          v-if="queue.loading && !queue.data"
          class="px-crm-page-x py-6 text-crm-body text-crm-muted-fg"
        >
          {{ __('Loading…') }}
        </div>
        <AstraEmptyState
          v-else-if="!sections.length"
          :title="__('Queue is clear')"
          :body="__('No follow-ups or quiet leads need you right now.')"
        />
        <template v-else>
          <section v-for="section in sections" :key="section.id" class="border-b border-crm-border">
            <div class="flex items-start gap-2 px-crm-page-x pb-2 pt-4">
              <div>
                <h2 class="m-0 text-crm-body font-semibold text-crm-fg">
                  {{ section.label }}
                  <span class="text-crm-muted-fg">{{ section.items?.length || 0 }}</span>
                </h2>
                <p
                  v-if="section.description"
                  class="m-0 mt-0.5 text-crm-meta text-crm-muted-fg"
                >
                  {{ section.description }}
                </p>
              </div>
            </div>
            <ul class="m-0 list-none p-0">
              <li
                v-for="item in section.items"
                :key="item.id"
                class="grid cursor-pointer grid-cols-[26px_1fr_auto] items-center gap-2.5 border-b border-crm-border px-crm-page-x py-3 hover:bg-crm-row-hover"
                :class="{
                  'bg-crm-row-selected': selectedId === item.id,
                }"
                @click="selectItem(item)"
              >
                <AstraAvatar :name="item.reference_title || item.title" size="md" />
                <div class="min-w-0">
                  <div class="flex flex-wrap items-baseline gap-x-2">
                    <span class="truncate text-crm-label font-semibold text-crm-fg">
                      {{ item.reference_title || item.title }}
                    </span>
                    <span class="truncate text-crm-meta text-crm-muted-fg">
                      {{ item.record_label }}
                    </span>
                  </div>
                  <p class="m-0 mt-0.5 truncate text-crm-label font-semibold text-crm-fg">
                    {{ item.title }}
                  </p>
                  <p
                    v-if="item.description"
                    class="m-0 mt-0.5 truncate text-crm-meta text-crm-muted-fg"
                  >
                    {{ stripHtml(item.description) }}
                  </p>
                </div>
                <div class="flex flex-col items-end gap-1.5">
                  <div class="flex items-center gap-1.5">
                    <AstraBadge
                      v-if="item.priority"
                      :label="item.priority"
                      :tone="priorityTone(item.priority)"
                    />
                    <span
                      class="text-crm-meta font-semibold"
                      :class="
                        item.late_minutes != null
                          ? 'text-crm-danger'
                          : 'text-crm-muted-fg'
                      "
                    >
                      {{ item.due_label }}
                    </span>
                  </div>
                  <AstraButton
                    v-if="primaryAction(item)"
                    size="sm"
                    :label="primaryAction(item).label"
                    @click.stop="primaryAction(item).run()"
                  />
                </div>
              </li>
            </ul>
          </section>

          <details
            v-if="(queue.data?.cleared_today || []).length"
            class="px-crm-page-x py-4"
          >
            <summary class="cursor-pointer text-crm-body font-semibold text-crm-muted-fg">
              {{ __('Cleared today') }}
              {{ queue.data.cleared_today.length }}
            </summary>
            <ul class="mt-2 list-none p-0">
              <li
                v-for="item in queue.data.cleared_today"
                :key="item.id"
                class="py-1.5 text-crm-label text-crm-fg"
              >
                {{ item.title }}
              </li>
            </ul>
          </details>
        </template>
      </div>

      <AstraSidePanel v-if="detail.data" class="hidden lg:block">
        <div class="flex items-start justify-between gap-2 border-b border-crm-border px-4 py-3">
          <h2 class="m-0 text-crm-dialog font-semibold text-crm-fg">
            {{ detail.data.title }}
          </h2>
          <router-link
            v-if="detail.data.route"
            :to="detail.data.route"
            class="shrink-0 text-crm-meta font-semibold text-crm-primary hover:underline"
          >
            {{ openRecordLabel }} →
          </router-link>
        </div>
        <div class="flex flex-wrap gap-1.5 px-4 pt-3">
          <AstraBadge
            v-if="detail.data.status"
            :label="detail.data.status"
            :tone="statusTone(detail.data.status)"
            dot
          />
          <AstraBadge
            v-if="detail.data.temperature"
            :label="detail.data.temperature"
            :tone="tempTone(detail.data.temperature)"
            dot
          />
        </div>
        <p
          v-if="slaLine"
          class="px-4 pt-2 text-crm-meta font-semibold text-crm-danger"
        >
          {{ slaLine }}
        </p>
        <AstraSidePanelSection :title="__('Details')" :entries="detailRows" />
        <div
          v-if="detail.data.last_call"
          class="mx-4 mb-3 rounded-lg border border-crm-border bg-crm-muted px-3 py-2.5 text-crm-label"
        >
          <p class="m-0 font-semibold text-crm-fg">
            {{ __('Last call') }}
            <span
              v-if="detail.data.last_call.creation"
              class="font-normal text-crm-muted-fg"
            >
              · {{ formatDate(detail.data.last_call.creation, 'D MMM') }}
            </span>
          </p>
          <p class="m-0 mt-1 text-crm-muted-fg">
            {{
              detail.data.last_call.outcome ||
              detail.data.last_call.call_summary ||
              detail.data.last_call.status
            }}
          </p>
        </div>
        <div class="flex flex-col gap-2 px-4 pb-4">
          <AstraButton
            v-if="connectReady"
            variant="primary"
            block
            :label="__('Call in Astra Connect')"
            @click="callSelected"
          />
        </div>
      </AstraSidePanel>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { createResource, usePageMeta } from 'frappe-ui'
import {
  AstraAvatar,
  AstraBadge,
  AstraButton,
  AstraEmptyState,
  AstraPageHeader,
  AstraSidePanel,
  AstraSidePanelSection,
  STATUS_TONES,
  TEMPERATURE_TONES,
} from '@/components/astra'
import { formatDate, sanitizeHTML } from '@/utils'
import {
  isAstraConnectConfigured,
  openConnectCompose,
} from '@/utils/astraConnect'
import { getSettings } from '@/stores/settings'
import { ASTRA_FAVICON } from '@/assets/brand'

const { brand } = getSettings()
const activeTab = ref('all')
const priorityFilter = ref('High,Medium')
const selectedId = ref(null)
const selectedItem = ref(null)

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

const sections = computed(() => queue.data?.sections || [])
const counts = computed(() => queue.data?.counts || {})
const connectReady = computed(() => isAstraConnectConfigured())

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
  if (!d?.response_by || !d.sla_status) return ''
  if (!['First Response Due', 'Rolling Response Due', 'Failed'].includes(d.sla_status))
    return ''
  return d.sla_status
})

watch(
  () => sections.value,
  (secs) => {
    if (!secs?.length) {
      selectedId.value = null
      selectedItem.value = null
      return
    }
    const flat = secs.flatMap((s) => s.items || [])
    if (!flat.length) return
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

function priorityTone(priority) {
  if (priority === 'High') return 'bad'
  if (priority === 'Medium') return 'warn'
  return 'mute'
}

function statusTone(status) {
  return STATUS_TONES[status] || 'mute'
}

function tempTone(temp) {
  return TEMPERATURE_TONES[temp] === 'danger'
    ? 'bad'
    : TEMPERATURE_TONES[temp] === 'warning'
      ? 'warn'
      : 'mute'
}

function stripHtml(html) {
  if (!html) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = sanitizeHTML(html)
  return (tmp.textContent || '').trim()
}

function primaryAction(item) {
  if (!connectReady.value) return null
  if (item.kind === 'quiet_lead' || /call/i.test(item.title || '')) {
    return {
      label: __('Call'),
      run: () =>
        openConnectCompose('calls', {
          recordType: item.reference_doctype,
          recordId: item.reference_docname,
          phone: item.mobile_no,
        }),
    }
  }
  if (/email|mail/i.test(item.title || '')) {
    return {
      label: __('Email'),
      run: () =>
        openConnectCompose('messages', {
          recordType: item.reference_doctype,
          recordId: item.reference_docname,
        }),
    }
  }
  return {
    label: __('Log note'),
    run: () => {
      if (item.reference_doctype === 'CRM Lead') {
        window.location.href = `/crm/leads/${item.reference_docname}#notes`
      } else if (item.reference_doctype === 'CRM Deal') {
        window.location.href = `/crm/deals/${item.reference_docname}#notes`
      }
    },
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

usePageMeta(() => ({
  title: __('Work queue'),
  icon: brand?.favicon || ASTRA_FAVICON,
}))
</script>
