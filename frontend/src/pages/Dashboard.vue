<template>
  <div class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg">
    <div class="min-h-0 flex-1 overflow-y-auto">
      <header
        class="flex flex-wrap items-start justify-between gap-3 px-crm-page-x pb-3.5 pt-[18px]"
      >
        <div class="min-w-0">
          <h1 class="m-0 text-crm-page font-semibold tracking-crm-tight text-crm-fg">
            {{ summary.data?.greeting || __('Home') }}
          </h1>
          <p class="mt-1 text-crm-body text-crm-muted-fg">
            {{ dateLabel }}
          </p>
        </div>
        <div
          class="inline-flex rounded-crm-control bg-crm-muted p-0.5 shadow-[inset_0_0_0_1px_var(--crm-border)]"
          role="group"
          :aria-label="__('Period')"
        >
          <button
            v-for="opt in periodOptions"
            :key="opt.value"
            type="button"
            class="h-crm-control-sm rounded-[7px] px-3 text-crm-label font-semibold"
            :class="
              period === opt.value
                ? 'bg-crm-card text-crm-fg shadow-crm-sm'
                : 'text-crm-muted-fg'
            "
            @click="setPeriod(opt.value)"
          >
            {{ opt.label }}
          </button>
        </div>
      </header>

      <div
        v-if="summary.loading && !summary.data"
        class="px-crm-page-x text-crm-body text-crm-muted-fg"
      >
        {{ __('Loading…') }}
      </div>

      <div v-else class="flex flex-col gap-4 px-crm-page-x pb-6">
        <!-- KPI row -->
        <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <article
            v-for="kpi in visibleKpis"
            :key="kpi.id"
            class="rounded-crm-panel border border-crm-border bg-crm-card px-3.5 py-3"
          >
            <div class="flex items-center gap-1.5 text-crm-meta text-crm-muted-fg">
              <component :is="kpiIcon(kpi.id)" class="size-3.5" aria-hidden="true" />
              <span>{{ kpi.label }}</span>
            </div>
            <p class="mt-1 text-[24px] font-semibold tracking-[-0.02em] text-crm-fg">
              {{ formatKpiValue(kpi) }}
            </p>
            <p
              v-if="kpiSubtitle(kpi)"
              class="mt-0.5 text-crm-meta"
              :class="
                kpi.subtitle_tone === 'danger'
                  ? 'font-semibold text-crm-danger'
                  : 'text-crm-muted-fg'
              "
            >
              {{ kpiSubtitle(kpi) }}
            </p>
          </article>
        </div>

        <!-- Pipeline -->
        <section
          v-if="pipelineGroups.length"
          class="rounded-crm-panel border border-crm-border bg-crm-card p-3.5"
        >
          <div class="mb-3 flex items-center justify-between gap-2">
            <h2 class="m-0 text-crm-body font-semibold text-crm-fg">
              {{ __('Your pipeline') }}
            </h2>
            <router-link
              :to="{ name: 'Deals', params: { viewType: 'kanban' } }"
              class="text-crm-meta font-semibold text-crm-primary hover:underline"
            >
              {{ __('Deals board') }} →
            </router-link>
          </div>
          <div class="flex gap-2 overflow-x-auto pb-1">
            <div
              v-for="group in pipelineGroups"
              :key="group.id"
              class="min-w-[140px] flex-1 rounded-[9px] border bg-crm-card p-2.5"
              :class="
                group.current
                  ? 'border-crm-primary shadow-[inset_0_0_0_1px_var(--crm-primary)]'
                  : 'border-crm-border'
              "
            >
              <div class="mb-2 flex items-baseline justify-between gap-2">
                <span
                  class="text-[10.5px] font-bold uppercase tracking-[0.06em]"
                  :class="group.current ? 'text-crm-primary' : 'text-crm-muted-fg'"
                >
                  {{ group.label }}
                </span>
                <span class="text-crm-caption text-crm-fg">{{ group.count }}</span>
              </div>
              <div class="flex flex-col gap-1.5">
                <div
                  v-for="stage in group.stages"
                  :key="stage.name"
                  class="flex items-center justify-between gap-2 text-crm-meta"
                >
                  <span class="truncate text-crm-muted-fg">{{ stage.name }}</span>
                  <span class="font-semibold text-crm-fg">{{ stage.count }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <div class="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_340px]">
          <!-- Today -->
          <section
            v-if="todayItems.length"
            class="rounded-crm-panel border border-crm-border bg-crm-card"
          >
            <div
              class="flex items-center justify-between gap-2 border-b border-crm-border px-4 py-3"
            >
              <h2 class="m-0 text-crm-body font-semibold text-crm-fg">
                {{ __('Today') }}
              </h2>
              <router-link
                :to="{ name: 'Tasks', params: { viewType: 'list' } }"
                class="text-crm-meta font-semibold text-crm-primary hover:underline"
              >
                {{ __('Open tasks') }} →
              </router-link>
            </div>
            <ul class="relative m-0 list-none p-0">
              <li
                v-for="item in todayItems"
                :key="item.name + (item.kind || '')"
                class="grid grid-cols-[52px_1fr] gap-3 border-b border-crm-border px-4 py-3 last:border-b-0"
              >
                <span class="pt-0.5 text-crm-meta font-semibold text-crm-muted-fg">
                  {{ item.time_label || '—' }}
                </span>
                <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="truncate text-crm-label font-semibold text-crm-fg">
                      {{ item.title }}
                    </span>
                    <AstraBadge
                      :label="item.badge"
                      :tone="todayBadgeTone(item)"
                    />
                  </div>
                  <p
                    v-if="item.record_label"
                    class="mt-0.5 truncate text-crm-meta text-crm-muted-fg"
                  >
                    {{ item.record_label }}
                  </p>
                </div>
              </li>
            </ul>
          </section>
          <section
            v-else
            class="rounded-crm-panel border border-crm-border bg-crm-card"
          >
            <div class="border-b border-crm-border px-4 py-3">
              <h2 class="m-0 text-crm-body font-semibold text-crm-fg">
                {{ __('Today') }}
              </h2>
            </div>
            <AstraEmptyState
              :title="__('Nothing due today')"
              :body="__('Open tasks with a due date will show up here.')"
            />
          </section>

          <div class="flex flex-col gap-4">
            <!-- Response deadlines -->
            <section
              v-if="deadlines.length"
              class="rounded-crm-panel border border-crm-border bg-crm-card"
            >
              <div
                class="flex items-center justify-between gap-2 border-b border-crm-border px-4 py-3"
              >
                <h2 class="m-0 text-crm-body font-semibold text-crm-fg">
                  {{ __('Response deadlines') }}
                </h2>
                <router-link
                  :to="{ name: 'Work Queue' }"
                  class="text-crm-meta font-semibold text-crm-primary hover:underline"
                >
                  {{ __('Work queue') }} →
                </router-link>
              </div>
              <ul class="m-0 list-none p-0">
                <li
                  v-for="row in deadlines"
                  :key="row.name"
                  class="flex items-center gap-2.5 border-b border-crm-border px-4 py-2.5 last:border-b-0"
                >
                  <AstraAvatar :name="row.title" size="md" />
                  <div class="min-w-0 flex-1">
                    <p class="m-0 truncate text-crm-label font-semibold text-crm-fg">
                      {{ row.title }}
                    </p>
                    <p class="m-0 truncate text-crm-meta text-crm-muted-fg">
                      {{ row.kind }}
                    </p>
                  </div>
                  <span
                    class="shrink-0 text-crm-meta font-semibold"
                    :class="
                      row.state === 'overdue' ? 'text-crm-danger' : 'text-crm-warning'
                    "
                  >
                    {{ row.label }}
                  </span>
                  <AstraButton
                    v-if="connectReady"
                    size="sm"
                    :label="__('Call')"
                    @click="callLead(row)"
                  />
                </li>
              </ul>
            </section>

            <!-- Recent -->
            <section
              v-if="recentItems.length"
              class="rounded-crm-panel border border-crm-border bg-crm-card"
            >
              <div class="border-b border-crm-border px-4 py-3">
                <h2 class="m-0 text-crm-body font-semibold text-crm-fg">
                  {{ __('Recent on your records') }}
                </h2>
              </div>
              <ul class="m-0 list-none p-0">
                <li
                  v-for="item in recentItems"
                  :key="`${item.activity_type}-${item.name}`"
                  class="flex gap-2.5 border-b border-crm-border px-4 py-2.5 last:border-b-0"
                >
                  <span
                    class="grid size-[30px] shrink-0 place-items-center rounded-lg"
                    :class="recentIconClass(item.activity_type)"
                  >
                    <component
                      :is="recentIcon(item.activity_type)"
                      class="size-3.5"
                      aria-hidden="true"
                    />
                  </span>
                  <div class="min-w-0 flex-1">
                    <p class="m-0 truncate text-crm-label text-crm-fg">
                      <span class="font-semibold">{{ recentTitle(item) }}</span>
                      <span
                        v-if="item.reference_docname"
                        class="text-crm-muted-fg"
                      >
                        · {{ item.reference_docname }}
                      </span>
                    </p>
                    <p
                      v-if="recentBody(item)"
                      class="m-0 mt-0.5 truncate text-crm-meta text-crm-muted-fg"
                    >
                      {{ recentBody(item) }}
                    </p>
                  </div>
                  <span class="shrink-0 text-crm-micro text-crm-faint">
                    {{ formatRecentTime(item.creation) }}
                  </span>
                </li>
              </ul>
            </section>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { createResource, usePageMeta } from 'frappe-ui'
import LucideUser from '~icons/lucide/user'
import LucideIndianRupee from '~icons/lucide/indian-rupee'
import LucideCalendarCheck from '~icons/lucide/calendar-check'
import LucidePhone from '~icons/lucide/phone'
import LucideMail from '~icons/lucide/mail'
import LucideStickyNote from '~icons/lucide/sticky-note'
import LucideGitBranch from '~icons/lucide/git-branch'
import {
  AstraAvatar,
  AstraBadge,
  AstraButton,
  AstraEmptyState,
} from '@/components/astra'
import { formatCompactCurrency } from '@/utils/compactCurrency'
import { formatDate } from '@/utils'
import {
  isAstraConnectConfigured,
  openConnectCompose,
} from '@/utils/astraConnect'
import { getSettings } from '@/stores/settings'
import { ASTRA_FAVICON } from '@/assets/brand'

const { brand } = getSettings()
const period = ref('today')
const periodOptions = [
  { value: 'today', label: __('Today') },
  { value: 'week', label: __('This week') },
]

const summary = createResource({
  url: 'crm.api.home.get_home_summary',
  auto: true,
  cache: ['crm-home-summary', period],
  makeParams: () => ({ period: period.value }),
})

function setPeriod(value) {
  period.value = value
  summary.reload()
}

const dateLabel = computed(() => {
  const raw = summary.data?.date
  if (!raw) return ''
  return formatDate(raw, 'ddd D MMM') + ' · ' + __('your records')
})

const visibleKpis = computed(() => summary.data?.kpis || [])
const pipelineGroups = computed(() => summary.data?.pipeline || [])
const todayItems = computed(() => summary.data?.today || [])
const deadlines = computed(() => summary.data?.response_deadlines || [])
const recentItems = computed(() => summary.data?.recent || [])
const connectReady = computed(() => isAstraConnectConfigured())

function kpiIcon(id) {
  return (
    {
      open_leads: LucideUser,
      open_pipeline: LucideIndianRupee,
      due_today: LucideCalendarCheck,
      calls_today: LucidePhone,
    }[id] || LucideUser
  )
}

function formatKpiValue(kpi) {
  if (kpi.value_is_currency) {
    return formatCompactCurrency(kpi.value)
  }
  const base = String(kpi.value ?? 0)
  return kpi.value_suffix ? base + kpi.value_suffix : base
}

function kpiSubtitle(kpi) {
  if (kpi.id === 'open_pipeline' && kpi.deal_count) {
    return __('{0} deals · weighted {1}', [
      kpi.deal_count,
      formatCompactCurrency(kpi.weighted_value),
    ])
  }
  return kpi.subtitle || ''
}

function todayBadgeTone(item) {
  const badge = (item.badge || '').toLowerCase()
  if (badge.includes('overdue')) return 'bad'
  if (badge.includes('meeting')) return 'blue'
  if (badge.includes('due')) return 'info'
  if (item.kind === 'meeting') return 'blue'
  return 'mute'
}

function recentIcon(type) {
  const t = (type || '').toLowerCase()
  if (t.includes('call')) return LucidePhone
  if (t.includes('communication') || t.includes('email') || t.includes('mail'))
    return LucideMail
  if (t.includes('note')) return LucideStickyNote
  if (t.includes('stage')) return LucideGitBranch
  return LucideStickyNote
}

function recentIconClass(type) {
  const t = (type || '').toLowerCase()
  if (t.includes('call')) return 'bg-crm-teal-soft text-crm-teal'
  if (t.includes('communication') || t.includes('email') || t.includes('mail'))
    return 'bg-crm-blue-soft text-crm-blue'
  if (t.includes('note')) return 'bg-crm-warning-soft text-crm-warning'
  if (t.includes('stage')) return 'bg-crm-primary-soft text-crm-primary'
  return 'bg-crm-neutral-soft text-crm-muted-fg'
}

function recentTitle(item) {
  const t = (item.activity_type || '').replace(/_/g, ' ')
  return t.charAt(0).toUpperCase() + t.slice(1)
}

function recentBody(item) {
  const d = item.data || {}
  if (item.activity_type === 'stage_change') {
    return `${d.from || '—'} → ${d.to || ''}`
  }
  return d.outcome || d.call_summary || d.subject || d.title || d.content || ''
}

function formatRecentTime(ts) {
  if (!ts) return ''
  return formatDate(ts, 'HH:mm')
}

function callLead(row) {
  openConnectCompose('calls', {
    recordType: 'CRM Lead',
    recordId: row.name,
    phone: row.mobile_no,
  })
}

usePageMeta(() => ({
  title: __('Home'),
  icon: brand?.favicon || ASTRA_FAVICON,
}))
</script>
