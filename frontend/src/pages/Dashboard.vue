<template>
  <div
    v-if="isMobile"
    class="min-h-0 flex-1 overflow-y-auto px-[14px] pb-24 pt-[14px] [text-rendering:geometricPrecision]"
  >
    <h1
      class="relative top-px m-0 text-[18.7px] font-semibold leading-[26px] tracking-[-0.02em] text-crm-fg"
    >
      {{ summary.data?.greeting || __('Home') }}
    </h1>
    <p class="relative top-px m-0 text-[12px] leading-[17px] tracking-[-0.005em] text-crm-muted-fg">
      {{ mobileDateLabel }}
    </p>

    <div class="mt-3.5 grid grid-cols-2 gap-x-2 gap-y-[9px]">
      <div
        v-for="kpi in visibleKpis"
        :key="kpi.id"
        class="h-[90px] rounded-crm-panel border border-crm-border bg-crm-card px-3 pt-[10px]"
      >
        <p class="m-0 text-[12px] leading-[1.45] text-crm-muted-fg">{{ kpi.label }}</p>
        <p
          class="m-0 mt-[7px] text-[20px] font-semibold leading-[1.2] tracking-[-0.02em] text-crm-fg"
        >
          {{ mobileKpiValue(kpi) }}
        </p>
        <p class="m-0 mt-[5px] text-[11.5px] leading-[1.45] text-crm-muted-fg">
          {{ mobileKpiSub(kpi) }}
        </p>
      </div>
    </div>

    <section class="mt-[13px] overflow-hidden rounded-crm-panel border border-crm-border bg-crm-card">
      <div class="flex h-[43px] items-center border-b-2 border-crm-border px-3.5">
        <h2 class="m-0 text-[14px] font-semibold text-crm-fg">{{ __('Today') }}</h2>
        <div class="flex-1" />
        <router-link
          :to="{ name: 'Tasks', params: { viewType: 'list' } }"
          class="text-[12.5px] font-semibold text-crm-primary"
        >
          {{ __('Tasks') }}
        </router-link>
      </div>
      <template v-for="(row, index) in mobileTodayRows" :key="row.key">
        <div
          v-if="row.now"
          class="flex h-[22px] items-center gap-2 border-t border-crm-border pl-[18px] pr-[18px] pt-[2px] text-[11px] font-semibold text-crm-danger"
        >
          <span class="size-1.5 shrink-0 rounded-full bg-crm-danger" />
          <span class="whitespace-nowrap">{{ row.label }}</span>
          <span class="h-px flex-1 bg-crm-danger opacity-[.45]" />
        </div>
        <div
          v-else
          class="flex items-center gap-0 px-3.5"
          :class="index ? 'h-[58px] border-t border-crm-border pt-1' : 'h-[56px] pt-[3px]'"
        >
          <span class="w-[62px] shrink-0 text-[12.5px] font-semibold text-crm-fg">
            {{ row.item.time_label || '—' }}
          </span>
          <div class="min-w-0 flex-1 leading-[1.45]">
            <div class="truncate text-[12.5px] font-semibold text-crm-fg">{{ row.item.title }}</div>
            <div class="truncate text-[11.5px] text-crm-muted-fg">{{ row.item.record_label }}</div>
          </div>
          <AstraBadge
            v-if="row.item.badge"
            :label="row.item.badge"
            :tone="todayBadgeTone(row.item)"
          />
        </div>
      </template>
    </section>

    <section
      v-if="mobileDeadlines.length"
      class="mt-3 overflow-hidden rounded-crm-panel border border-crm-border bg-crm-card"
    >
      <div class="flex h-[43px] items-center border-b-2 border-crm-border px-3.5 pt-1">
        <h2 class="m-0 text-[14px] font-semibold text-crm-fg">{{ __('Response deadlines') }}</h2>
        <div class="flex-1" />
        <router-link :to="{ name: 'Work Queue' }" class="text-[12.5px] font-semibold text-crm-primary">
          {{ __('Queue') }}
        </router-link>
      </div>
      <div
        v-for="(row, index) in mobileDeadlines"
        :key="row.name"
        class="flex items-center gap-2.5 px-3.5"
        :class="index ? 'h-[56px] border-t border-crm-border pt-[6px]' : 'h-[54px] pt-0.5'"
      >
        <span
          class="flex size-[26px] shrink-0 items-center justify-center rounded-full bg-crm-primary-soft text-[10.5px] font-bold text-crm-primary"
          aria-hidden="true"
        >
          {{ initialsFrom(row.title) }}
        </span>
        <div class="min-w-0 flex-1 leading-[1.45]">
          <div class="truncate text-[12.5px] font-semibold text-crm-fg">{{ row.title }}</div>
          <div class="truncate text-[11.5px] text-crm-muted-fg">{{ row.sub_label }}</div>
        </div>
        <span
          class="shrink-0 whitespace-nowrap text-[11.5px] font-semibold"
          :class="row.state === 'overdue' ? 'text-crm-danger' : 'text-crm-warning'"
        >
          {{ (row.label || '').replace(/^due /, '') }}
        </span>
      </div>
    </section>
  </div>
  <div
    v-else
    class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg [text-rendering:geometricPrecision]"
  >
    <div class="min-h-0 flex-1 overflow-y-auto">
      <header class="flex items-center gap-3 px-crm-page-x pb-3.5 pt-[19px]">
        <div class="min-w-0">
          <h1
            class="m-0 text-[20px] font-semibold leading-[1.45] tracking-[-0.02em] text-crm-fg"
          >
            {{ summary.data?.greeting || __('Home') }}
          </h1>
          <p
            class="relative top-px m-0 -mt-px text-[13px] leading-[1.45] tracking-[-0.005em] text-crm-muted-fg"
          >
            {{ dateLabel }}
          </p>
        </div>
        <div class="flex-1" />
        <div
          class="flex gap-0.5 rounded-crm-control border border-crm-border bg-crm-muted p-[3px]"
          role="group"
          :aria-label="__('Period')"
        >
          <button
            v-for="opt in periodOptions"
            :key="opt.value"
            type="button"
            class="inline-flex h-[26px] items-center rounded-crm-chip px-2.5 text-[12.5px]"
            :class="
              period === opt.value
                ? 'bg-crm-card font-semibold text-crm-fg shadow-[0_0_0_1px_var(--crm-border)]'
                : 'font-medium text-crm-muted-fg'
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
        <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <article
            v-for="kpi in visibleKpis"
            :key="kpi.id"
            class="rounded-crm-panel border border-crm-border bg-crm-card px-3.5 pb-[11px] pt-3"
          >
            <div
              class="flex items-center gap-1.5 text-[12px] leading-[1.45] text-crm-muted-fg"
            >
              <component
                :is="kpiIcon(kpi.id)"
                class="size-3.5"
                aria-hidden="true"
              />
              <span>{{ kpi.label }}</span>
            </div>
            <p
              class="m-0 mt-[5px] text-[24px] font-semibold leading-[1.45] tracking-crm-num text-crm-fg"
            >
              {{ formatKpiValue(kpi) }}
            </p>
            <p
              v-if="kpiSubtitle(kpi)"
              class="m-0 mt-0.5 text-[11.5px] leading-[1.45] text-crm-muted-fg"
            >
              <template v-if="kpiLead(kpi)">
                <span
                  class="font-semibold"
                  :class="
                    kpi.subtitle_tone === 'danger'
                      ? 'text-crm-danger'
                      : 'text-crm-success'
                  "
                  >{{ kpiLead(kpi) }}</span
                >{{ kpiSubtitle(kpi).slice(kpiLead(kpi).length) }}
              </template>
              <template v-else>{{ kpiSubtitle(kpi) }}</template>
            </p>
          </article>
        </div>

        <section
          v-if="pipelineGroups.length"
          class="rounded-crm-panel border border-crm-border bg-crm-card"
        >
          <div
            class="flex items-center gap-2.5 border-b border-crm-border px-[18px] py-3.5"
          >
            <h2
              class="m-0 text-crm-panel font-semibold leading-[21.5px] tracking-[-0.005em] text-crm-fg"
            >
              {{ __('Your pipeline') }}
            </h2>
            <span
              class="relative top-[2px] text-[12.5px] leading-[1.45] text-crm-muted-fg"
            >
              {{ __('Grouped by milestone · stages from Settings') }}
            </span>
            <div class="flex-1" />
            <router-link
              :to="{ name: 'Deals', params: { viewType: 'kanban' } }"
              class="relative top-[2px] inline-flex items-center gap-1 text-[12.5px] font-semibold leading-[1.45] text-crm-primary hover:underline"
            >
              {{ __('Deals board') }}
              <LucideChevronRight class="size-3.5" aria-hidden="true" />
            </router-link>
          </div>
          <div
            class="flex items-stretch gap-1.5 overflow-x-auto px-4 pb-3.5 pt-3"
          >
            <div
              v-for="group in pipelineGroups"
              :key="group.id"
              class="rail-card relative min-w-0 rounded-crm-rail border border-transparent bg-crm-card px-2.5 pb-2 pt-2 before:pointer-events-none before:absolute before:-inset-px before:rounded-[inherit] before:border before:content-['']"
              :class="
                group.current
                  ? 'before:border-crm-primary'
                  : 'before:border-crm-border'
              "
              :style="railGroupStyle(group)"
            >
              <div
                class="mb-1.5 flex items-center gap-1.5 whitespace-nowrap text-crm-caps font-bold uppercase leading-[1.45] tracking-[0.07em]"
                :class="
                  group.current ? 'text-crm-primary' : 'text-crm-muted-fg'
                "
              >
                <span>{{ group.label }}</span>
                <span class="ml-auto text-[12px] tracking-normal text-crm-fg">
                  {{ group.count }}
                </span>
              </div>
              <div class="flex gap-1">
                <div
                  v-for="stage in group.stages"
                  :key="stage.name"
                  class="min-w-0 flex-1"
                >
                  <div
                    class="rail-bar h-1.5 rounded-[3px]"
                    :class="stageBarClass(group, stage)"
                  />
                  <div
                    class="mt-1.5 truncate text-[11.5px] font-semibold leading-[1.45] text-crm-fg"
                  >
                    {{ stage.name }}
                  </div>
                  <div
                    class="mt-px whitespace-nowrap text-[11px] leading-[1.45] text-crm-muted-fg"
                  >
                    {{ stage.count }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <div
          class="grid grid-cols-1 items-start gap-4 lg:grid-cols-[1.355fr_1fr]"
        >
          <section
            class="rounded-crm-panel border border-crm-border bg-crm-card"
          >
            <div
              class="flex items-center gap-2.5 border-b border-crm-border px-[18px] py-3.5"
            >
              <h2
                class="m-0 text-crm-panel font-semibold leading-[21.5px] tracking-[-0.005em] text-crm-fg"
              >
                {{ __('Today') }}
              </h2>
              <span
                class="relative top-px truncate text-[12.5px] leading-[1.45] text-crm-muted-fg"
              >
                {{ __('Tasks, calls and meetings on your records') }}
              </span>
              <div class="flex-1" />
              <router-link
                :to="{ name: 'Tasks', params: { viewType: 'list' } }"
                class="relative top-px inline-flex shrink-0 items-center gap-1 text-[12.5px] font-semibold leading-[1.45] text-crm-primary hover:underline"
              >
                {{ __('Open tasks') }}
                <LucideChevronRight class="size-3.5" aria-hidden="true" />
              </router-link>
            </div>
            <ul v-if="todayRows.length" class="m-0 list-none p-0">
              <template v-for="(row, rowIndex) in todayRows" :key="row.key">
                <li
                  v-if="row.now"
                  class="flex h-[22px] items-center gap-2 border-t border-crm-border pl-[18px] pr-4 text-[11px] font-semibold text-crm-danger first:border-t-0"
                >
                  <span class="size-1.5 shrink-0 rounded-full bg-crm-danger" />
                  <span class="whitespace-nowrap">{{ row.label }}</span>
                  <span class="h-px flex-1 bg-crm-danger opacity-[.45]" />
                </li>
                <li
                  v-else
                  class="flex h-[53.9px] items-center gap-2.5 border-t border-crm-border px-4 pb-2 text-[12.5px] leading-[1.45] first:border-t-0"
                  :class="[1, 3, 6].includes(rowIndex) ? 'pt-2' : 'pt-2.5'"
                >
                  <span
                    class="w-[52px] shrink-0 text-[12px] font-semibold text-crm-fg"
                  >
                    {{ row.item.time_label || '—' }}
                    <span
                      v-if="todaySubLabel(row.item)"
                      class="block text-[11px] font-medium text-crm-faint"
                    >
                      {{ todaySubLabel(row.item) }}
                    </span>
                  </span>
                  <span
                    class="flex size-4 shrink-0 items-center justify-center rounded-full border-[1.5px]"
                    :class="
                      isDone(row.item)
                        ? 'border-crm-success bg-crm-success text-white'
                        : 'border-crm-border-strong'
                    "
                    aria-hidden="true"
                  >
                    <LucideCheck
                      v-if="isDone(row.item)"
                      class="size-2.5 [stroke-width:3.5]"
                    />
                  </span>
                  <div class="min-w-0 flex-1">
                    <div
                      class="truncate font-semibold tracking-[-0.005em]"
                      :class="
                        isDone(row.item)
                          ? 'text-crm-muted-fg line-through'
                          : 'text-crm-fg'
                      "
                    >
                      {{ row.item.title }}
                    </div>
                    <div
                      v-if="row.item.record_label"
                      class="truncate text-[11.5px] text-crm-muted-fg"
                    >
                      {{ row.item.record_label }}
                    </div>
                  </div>
                  <AstraBadge
                    v-if="row.item.badge"
                    :label="row.item.badge"
                    :tone="todayBadgeTone(row.item)"
                  />
                </li>
              </template>
            </ul>
            <AstraEmptyState
              v-else
              :title="__('Nothing due today')"
              :body="__('Open tasks with a due date will show up here.')"
            />
          </section>

          <div class="flex flex-col gap-4">
            <section
              v-if="deadlines.length"
              class="rounded-crm-panel border border-crm-border bg-crm-card"
            >
              <div
                class="flex items-center gap-2.5 border-b border-crm-border px-[18px] py-3.5"
              >
                <h2
                  class="m-0 text-crm-panel font-semibold leading-[21.5px] tracking-[-0.005em] text-crm-fg"
                >
                  {{ __('Response deadlines') }}
                </h2>
                <span
                  class="relative top-px truncate text-[12.5px] leading-[1.45] text-crm-muted-fg"
                >
                  {{ __('SLA on your leads') }}
                </span>
                <div class="flex-1" />
                <router-link
                  :to="{ name: 'Work Queue' }"
                  class="relative top-px inline-flex shrink-0 items-center gap-1 text-[12.5px] font-semibold leading-[1.45] text-crm-primary hover:underline"
                >
                  {{ __('Work queue') }}
                  <LucideChevronRight class="size-3.5" aria-hidden="true" />
                </router-link>
              </div>
              <ul class="m-0 list-none p-0">
                <li
                  v-for="row in deadlines"
                  :key="row.name"
                  class="flex h-[53.9px] items-center gap-2.5 border-t border-crm-border px-4 pb-2 pt-2.5 [&:not(:first-child)]:pt-2 text-[12.5px] leading-[1.45] first:border-t-0"
                >
                  <span
                    class="flex size-[26px] shrink-0 items-center justify-center rounded-full bg-crm-primary-soft text-[10.5px] font-bold text-crm-primary"
                    aria-hidden="true"
                  >
                    {{ initialsFrom(row.title) }}
                  </span>
                  <div class="min-w-0 flex-1">
                    <div
                      class="truncate font-semibold tracking-[-0.005em] text-crm-fg"
                    >
                      {{ row.title }}
                    </div>
                    <div class="truncate text-[11.5px] text-crm-muted-fg">
                      {{ deadlineSubLabel(row) }}
                    </div>
                  </div>
                  <span
                    class="shrink-0 whitespace-nowrap text-[11.5px] font-semibold"
                    :class="
                      row.state === 'overdue'
                        ? 'text-crm-danger'
                        : 'text-crm-warning'
                    "
                  >
                    {{ deadlineLabel(row) }}
                  </span>
                  <AstraButton
                    v-if="connectReady"
                    size="sm"
                    :label="__('Call')"
                    @click="callLead(row)"
                  >
                    <template #prefix>
                      <LucidePhone class="size-3.5" aria-hidden="true" />
                    </template>
                    <template #suffix>
                      <LucideExternalLink class="size-3.5" aria-hidden="true" />
                    </template>
                  </AstraButton>
                </li>
              </ul>
            </section>

            <section
              v-if="recentItems.length"
              class="rounded-crm-panel border border-crm-border bg-crm-card"
            >
              <div
                class="flex items-center gap-2.5 border-b border-crm-border px-[18px] py-3.5"
              >
                <h2
                  class="m-0 text-crm-panel font-semibold leading-[21.5px] tracking-[-0.005em] text-crm-fg"
                >
                  {{ __('Recent on your records') }}
                </h2>
                <div class="flex-1" />
                <router-link
                  :to="{ name: 'Activities' }"
                  class="relative top-px inline-flex shrink-0 items-center gap-1 text-[12.5px] font-semibold leading-[1.45] text-crm-primary hover:underline"
                >
                  {{ __('Activities') }}
                  <LucideChevronRight class="size-3.5" aria-hidden="true" />
                </router-link>
              </div>
              <ul class="m-0 list-none p-0">
                <li
                  v-for="item in recentItems"
                  :key="`${item.activity_type}-${item.name}`"
                  class="flex h-[53.9px] items-center gap-2.5 border-t border-crm-border px-4 pb-2 pt-2 text-[12.5px] leading-[1.45] first:border-t-0"
                >
                  <span
                    class="grid size-[22px] shrink-0 place-items-center rounded-crm-chip"
                    :class="recentIconClass(item.activity_type)"
                  >
                    <component
                      :is="recentIcon(item.activity_type)"
                      class="size-3.5"
                      aria-hidden="true"
                    />
                  </span>
                  <div class="min-w-0 flex-1">
                    <div
                      class="truncate font-semibold tracking-[-0.005em] text-crm-fg"
                    >
                      {{ recentTitle(item) }}
                    </div>
                    <div class="truncate text-[11.5px] text-crm-muted-fg">
                      <template v-if="recentOutcome(item)">
                        {{ __('Outcome:') }}
                        <span class="font-semibold">{{
                          recentOutcome(item)
                        }}</span>
                        <template v-if="recentDuration(item)">
                          · {{ recentDuration(item) }}
                        </template>
                      </template>
                      <template v-else>{{ recentBody(item) }}</template>
                    </div>
                  </div>
                  <span
                    class="shrink-0 whitespace-nowrap text-[11.5px] text-crm-faint"
                  >
                    {{ recentTime(item) }}
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
import { useMediaQuery } from '@vueuse/core'
import { createResource, usePageMeta } from 'frappe-ui'
import dayjs from 'dayjs'
import LucideUsers from '~icons/lucide/users'
import LucideDollarSign from '~icons/lucide/dollar-sign'
import LucideSquareCheck from '~icons/lucide/square-check'
import LucidePhone from '~icons/lucide/phone'
import LucideMail from '~icons/lucide/mail'
import LucideStickyNote from '~icons/lucide/sticky-note'
import LucideSquareKanban from '~icons/lucide/square-kanban'
import LucideChevronRight from '~icons/lucide/chevron-right'
import LucideCheck from '~icons/lucide/check'
import LucideExternalLink from '~icons/lucide/external-link'
import { AstraBadge, AstraButton, AstraEmptyState } from '@/components/astra'
import { initialsFrom } from '@/components/astra/format'
import { formatCompactCurrency } from '@/utils/compactCurrency'
import { formatDate } from '@/utils'
import {
  isAstraConnectConfigured,
  openConnectCompose,
} from '@/utils/astraConnect'
import { getSettings } from '@/stores/settings'
import { ASTRA_FAVICON } from '@/assets/brand'

const { brand } = getSettings()
const isMobile = useMediaQuery('(max-width: 639px)')
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
  return formatDate(raw, 'dddd D MMM') + ' · ' + __('showing your records')
})

const mobileDateLabel = computed(() => {
  const raw = summary.data?.date
  if (!raw) return ''
  return formatDate(raw, 'ddd D MMM') + ' · ' + __('your records')
})

const mobileTodayRows = computed(() => {
  const open = todayRows.value.filter((r) => r.now || !isDone(r.item))
  const out = []
  let items = 0
  for (const row of open) {
    if (!row.now && items >= 3) continue
    out.push(row)
    if (!row.now) items++
  }
  return out
})
const mobileDeadlines = computed(() => deadlines.value.slice(0, 2))

function mobileKpiValue(kpi) {
  if (kpi.value_is_currency) return formatCompactCurrency(kpi.value)
  return String(kpi.value ?? 0)
}

function mobileKpiSub(kpi) {
  if (kpi.id === 'open_leads' && kpi.delta) return __('{0} new', [kpi.delta])
  if (kpi.id === 'open_pipeline' && kpi.deal_count) return __('{0} deals', [kpi.deal_count])
  return (kpi.subtitle || '').split(' · ')[0]
}

const visibleKpis = computed(() => summary.data?.kpis || [])
const pipelineGroups = computed(() => summary.data?.pipeline || [])
const todayItems = computed(() => summary.data?.today || [])
const deadlines = computed(() => summary.data?.response_deadlines || [])
const recentItems = computed(() => summary.data?.recent || [])
const connectReady = computed(() => isAstraConnectConfigured())

/** Today agenda with a "Now" marker before the first item still ahead. */
const todayRows = computed(() => {
  const items = todayItems.value
  const rows = items.map((item) => ({
    key: item.name + (item.kind || ''),
    item,
  }))
  if (period.value !== 'today' || !items.length) return rows
  const now = summary.data?.now ? dayjs(summary.data.now) : dayjs()
  const idx = items.findIndex((item) => {
    const at = item.due_date || item.starts_on
    return at && dayjs(at).isAfter(now)
  })
  if (idx <= 0) return rows
  rows.splice(idx, 0, {
    key: '__now__',
    now: true,
    label: __('Now · {0}', [now.format('HH:mm')]),
  })
  return rows
})

function kpiIcon(id) {
  return (
    {
      open_leads: LucideUsers,
      open_pipeline: LucideDollarSign,
      due_today: LucideSquareCheck,
      calls_today: LucidePhone,
    }[id] || LucideUsers
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

/** Leading emphasised fragment of a KPI subtitle ("6 new", "2 overdue"). */
function kpiLead(kpi) {
  if (kpi.id === 'open_leads' && kpi.delta) {
    const lead = __('{0} new', [kpi.delta])
    return kpiSubtitle(kpi).startsWith(lead) ? lead : ''
  }
  if (kpi.subtitle_tone === 'danger') return kpiSubtitle(kpi)
  return ''
}

/** Groups share free width by stage count on top of their 22px padding + border. */
function railGroupStyle(group) {
  const n = group.stages?.length || 1
  return { flex: `${n} 1 22px` }
}

function stageBarClass(group, stage) {
  if (group.id === 'closed') {
    return /lost/i.test(stage.name) ? 'bg-crm-border-strong' : 'bg-crm-success'
  }
  return stage.count ? 'bg-crm-primary' : 'bg-crm-neutral-soft'
}

function isDone(item) {
  return Boolean(item.done) || item.status === 'Done'
}

function todaySubLabel(item) {
  if (item.sub_label != null) return item.sub_label
  if (isDone(item)) return __('Done')
  if (item.overdue) return __('Overdue')
  return ''
}

function todayBadgeTone(item) {
  const tones = { success: 'ok', warning: 'warn', danger: 'bad' }
  if (item.badge_tone) return tones[item.badge_tone] || item.badge_tone
  if (isDone(item)) return 'ok'
  const badge = (item.badge || '').toLowerCase()
  if (badge.includes('overdue')) return 'bad'
  if (badge.includes('due')) return 'info'
  return 'mute'
}

function deadlineSubLabel(row) {
  if (row.sub_label) return row.sub_label
  return [row.organization, row.kind].filter(Boolean).join(' · ')
}

function deadlineLabel(row) {
  const label = row.label || ''
  if (row.state === 'overdue' || label.startsWith(__('due'))) return label
  return __('due {0}', [label])
}

function recentIcon(type) {
  const t = (type || '').toLowerCase()
  if (t.includes('call')) return LucidePhone
  if (t.includes('communication') || t.includes('email') || t.includes('mail'))
    return LucideMail
  if (t.includes('stage') || t.includes('status')) return LucideSquareKanban
  return LucideStickyNote
}

function recentIconClass(type) {
  const t = (type || '').toLowerCase()
  if (t.includes('call')) return 'bg-crm-teal-soft text-crm-teal'
  if (t.includes('communication') || t.includes('email') || t.includes('mail'))
    return 'bg-crm-blue-soft text-crm-blue'
  if (t.includes('note')) return 'bg-crm-warning-soft text-crm-warning'
  if (t.includes('stage') || t.includes('status'))
    return 'bg-crm-primary-soft text-crm-primary'
  return 'bg-crm-neutral-soft text-crm-muted-fg'
}

function recentTitle(item) {
  if (item.title) return item.title
  const t = (item.activity_type || '').replace(/_/g, ' ')
  const label = t.charAt(0).toUpperCase() + t.slice(1)
  return item.reference_docname ? `${label} · ${item.reference_docname}` : label
}

function recentOutcome(item) {
  return item.activity_type === 'call' ? item.data?.outcome || '' : ''
}

function recentDuration(item) {
  const secs = Number(item.data?.duration) || 0
  if (!secs) return ''
  return __('{0} m {1} s', [Math.floor(secs / 60), secs % 60])
}

function recentBody(item) {
  if (item.body) return item.body
  const d = item.data || {}
  if (item.activity_type === 'stage_change') {
    return `${d.from || '—'} → ${d.to || ''}`
  }
  return d.call_summary || d.subject || d.title || d.content || ''
}

function recentTime(item) {
  if (item.time_label) return item.time_label
  if (!item.creation) return ''
  const at = dayjs(item.creation)
  const now = summary.data?.now ? dayjs(summary.data.now) : dayjs()
  if (at.isSame(now, 'day')) return at.format('HH:mm')
  if (at.isSame(now.subtract(1, 'day'), 'day')) return __('Yesterday')
  return formatDate(item.creation, 'D MMM')
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

<style scoped>
/* Figma places rail cards at fractional y; paint the border on a nudged layer. */
.rail-bar {
  transform: translateY(-0.13px);
}
.rail-card::before {
  transform-origin: top;
  transform: translateY(-0.15px) scaleY(1.0075);
}
</style>
