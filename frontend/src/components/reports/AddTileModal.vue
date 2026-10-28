<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Add tile to {0}', [dashboardTitle]), size: '3xl' }"
  >
    <template #body-content>
      <div class="flex gap-4">
        <div class="min-w-0 flex-1">
          <p class="mb-3 text-[13px] text-[color:var(--crm-muted-fg,#64748b)]">
            {{ __('Choose data and how it is counted.') }}
          </p>
          <div class="grid grid-cols-2 gap-2 sm:grid-cols-3">
            <button
              v-for="opt in tileOptions"
              :key="opt.value"
              type="button"
              class="flex flex-col gap-2 rounded-[9px] border p-3 text-left transition"
              :class="
                selected === opt.value
                  ? 'border-[color:var(--crm-primary,#0a7393)] bg-[color:var(--crm-primary-soft,#e6f4f8)] shadow-[inset_0_0_0_1px_var(--crm-primary,#0a7393)]'
                  : 'border-[color:var(--crm-border,#e2e8f0)] hover:border-[color:var(--crm-border-strong,#94a3b8)]'
              "
              @click="selected = opt.value"
            >
              <div
                class="flex h-16 items-center justify-center rounded-md bg-[color:var(--crm-muted,#f1f5f9)] text-[color:var(--crm-muted-fg,#64748b)]"
              >
                <component :is="opt.icon" class="size-6" />
              </div>
              <div class="text-[13px] font-semibold text-[color:var(--crm-fg,#0f172a)]">
                {{ opt.label }}
              </div>
              <div class="text-[11.5px] text-[color:var(--crm-muted-fg,#64748b)]">
                {{ opt.description }}
              </div>
            </button>
          </div>
        </div>

        <aside
          class="hidden w-56 shrink-0 border-l border-[color:var(--crm-border,#e2e8f0)] pl-4 md:block"
        >
          <div class="mb-2 text-[12px] font-semibold text-[color:var(--crm-muted-fg,#64748b)]">
            {{ __('Start from a template') }}
          </div>
          <ul class="space-y-2">
            <li
              v-for="tpl in templates"
              :key="tpl.id"
              class="rounded-md border border-[color:var(--crm-border,#e2e8f0)] p-2"
            >
              <div class="text-[12.5px] font-medium text-[color:var(--crm-fg,#0f172a)]">
                {{ tpl.title }}
              </div>
              <div class="text-[11px] text-[color:var(--crm-muted-fg,#64748b)]">
                {{ tpl.meta }}
              </div>
              <button
                type="button"
                class="mt-1 text-[12px] font-semibold text-[color:var(--crm-primary,#0a7393)]"
                @click="$emit('template', tpl)"
              >
                {{ __('Add') }}
              </button>
            </li>
          </ul>
        </aside>
      </div>
    </template>
    <template #actions>
      <div class="flex w-full items-center justify-between gap-3">
        <span class="text-[12px] text-[color:var(--crm-muted-fg,#64748b)]">
          {{ __('Next: choose data and how it is counted.') }}
        </span>
        <div class="flex gap-2">
          <Button :label="__('Cancel')" @click="show = false" />
          <Button
            variant="solid"
            :label="__('Continue')"
            @click="$emit('continue', selected)"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import LucideBarChart3 from '~icons/lucide/bar-chart-3'
import LucideFilter from '~icons/lucide/filter'
import LucideHash from '~icons/lucide/hash'
import LucideLineChart from '~icons/lucide/line-chart'
import LucidePieChart from '~icons/lucide/pie-chart'
import LucideTable from '~icons/lucide/table'
import { Button, Dialog } from 'frappe-ui'
import { ref } from 'vue'

defineProps({
  dashboardTitle: { type: String, default: '' },
})

defineEmits(['continue', 'template'])

const show = defineModel({ type: Boolean, default: false })
const selected = ref('kpi')

const tileOptions = [
  {
    value: 'kpi',
    label: __('KPI number'),
    description: __('One value with trend vs a previous period.'),
    icon: LucideHash,
  },
  {
    value: 'bar',
    label: __('Bar chart'),
    description: __('Compare values across stages, owners or sources.'),
    icon: LucideBarChart3,
  },
  {
    value: 'line',
    label: __('Line chart'),
    description: __('Trend over days, weeks or months.'),
    icon: LucideLineChart,
  },
  {
    value: 'donut',
    label: __('Pie chart'),
    description: __('Share of a total, up to 6 slices.'),
    icon: LucidePieChart,
  },
  {
    value: 'funnel',
    label: __('Funnel'),
    description: __('Conversion between milestones.'),
    icon: LucideFilter,
  },
  {
    value: 'table',
    label: __('Table'),
    description: __('Rows of records with chosen columns.'),
    icon: LucideTable,
  },
]

const templates = [
  {
    id: 'deals_created',
    title: __('Deals created this week'),
    meta: __('Count · Deals · created on'),
    type: 'kpi',
    config: {
      kpi_type: 'simple',
      doctype: 'CRM Deal',
      aggregation: 'count',
      date_field: 'creation',
      format: 'number',
      compare_with: 'previous_period',
    },
  },
  {
    id: 'calls_today',
    title: __('Calls connected today'),
    meta: __('Count · Call logs · status'),
    type: 'kpi',
    config: {
      kpi_type: 'simple',
      doctype: 'CRM Call Log',
      aggregation: 'count',
      date_field: 'start_time',
      filters: [['CRM Call Log', 'status', '=', 'Completed']],
      format: 'number',
    },
  },
  {
    id: 'deals_by_source',
    title: __('Deals by source'),
    meta: __('Count · Deals · group by Source'),
    type: 'bar',
    config: {
      doctype: 'CRM Deal',
      aggregation: 'count',
      group_by: 'source',
      date_field: 'creation',
    },
  },
  {
    id: 'lead_won_funnel',
    title: __('Lead → Won'),
    meta: __('Funnel · milestones'),
    type: 'funnel',
    config: {
      doctype: 'CRM Deal',
      date_field: 'creation',
      milestones: [
        { label: 'Open', field: 'status', value: '' },
        { label: 'Won', field: 'status', value: '' },
      ],
    },
  },
]
</script>
