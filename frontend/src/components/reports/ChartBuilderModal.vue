<template>
  <Dialog
    v-model="show"
    :options="{ title: chartTitle, size: '4xl' }"
  >
    <template #body-content>
      <div class="-mt-1 mb-3 text-[12px] font-medium text-[color:var(--crm-muted-fg,#5b6478)]">
        {{ __('Step 2 of 2 · data') }}
      </div>
      <div class="grid gap-0 md:grid-cols-[1fr_320px]">
        <div class="space-y-4 border-r-0 pr-0 md:border-r md:border-[color:var(--crm-border,#e1e7ec)] md:pr-[18px]">
          <div>
            <div class="mb-1 text-[12px] font-semibold text-[color:var(--crm-fg,#0b1324)]">
              {{ __('Chart type') }}
            </div>
            <div
              class="inline-flex overflow-hidden rounded-[7px] border border-[color:var(--crm-border-strong,#d0d9e0)] bg-[color:var(--crm-card,#fff)]"
            >
              <button
                v-for="(t, idx) in chartTypes"
                :key="t"
                type="button"
                class="inline-flex h-[30px] items-center gap-1.5 px-2.5 text-[12px] font-medium capitalize"
                :class="[
                  idx < chartTypes.length - 1
                    ? 'border-r border-[color:var(--crm-border,#e1e7ec)]'
                    : '',
                  draft.chart_type === t
                    ? 'bg-[color:var(--crm-primary-soft,#e4f2f6)] font-semibold text-[color:var(--crm-primary,#0a7393)]'
                    : 'text-[color:var(--crm-muted-fg,#5b6478)]',
                ]"
                @click="draft.chart_type = t"
              >
                {{ __(t === 'donut' ? 'Pie' : t) }}
              </button>
            </div>
          </div>

          <FormControl v-model="draft.title" :label="__('Title')" type="text" />

          <div class="grid grid-cols-2 gap-3">
            <FormControl
              v-model="draft.doctype"
              type="select"
              :label="__('Module')"
              :options="moduleOptions"
            />
            <FormControl
              v-model="draft.group_by"
              type="select"
              :label="__('X axis')"
              :options="dimensionOptions"
            />
            <FormControl
              v-model="draft.aggregation"
              type="select"
              :label="__('Y axis')"
              :options="aggOptions"
            />
            <FormControl
              v-if="draft.aggregation !== 'count'"
              v-model="draft.field"
              type="select"
              :label="__('Field')"
              :options="numericOptions"
            />
            <FormControl
              v-model="draft.series_by"
              type="select"
              :label="__('Group by')"
              :options="[{ label: __('None'), value: '' }, ...dimensionOptions]"
            />
            <FormControl
              v-model="draft.date_field"
              type="select"
              :label="__('Date field')"
              :options="dateOptions"
            />
            <FormControl
              v-if="isDateDimension"
              v-model="draft.date_bucket"
              type="select"
              :label="__('Bucket')"
              :options="bucketOptions"
            />
          </div>

          <div class="flex items-center gap-4">
            <label class="flex items-center gap-2 text-[12.5px]">
              <input v-model="draft.stacked" type="checkbox" class="rounded" />
              {{ __('Stacked') }}
            </label>
            <label class="flex items-center gap-2 text-[12.5px]">
              <input v-model="draft.show_totals" type="checkbox" class="rounded" />
              {{ __('Show totals') }}
            </label>
          </div>

          <div>
            <div class="mb-2 text-[12.5px] text-[color:var(--crm-muted-fg,#5b6478)]">
              {{ __('Series colours') }} · {{ __('Astra palette') }}
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="sw in astraPaletteSwatches()"
                :key="sw.key"
                type="button"
                class="size-[22px] rounded-md border-2 border-[color:var(--crm-card,#fff)]"
                :class="
                  selectedSwatch === sw.key
                    ? 'shadow-[0_0_0_2px_var(--crm-primary,#0a7393)]'
                    : 'shadow-[0_0_0_1px_var(--crm-border-strong,#d0d9e0)]'
                "
                :style="{ background: sw.css }"
                :title="sw.label"
                @click="selectedSwatch = sw.key"
              />
            </div>
          </div>
        </div>

        <aside class="bg-[color:var(--crm-muted,#f6f8fa)] p-0 md:pl-[18px]">
          <div class="mb-2 flex flex-wrap items-center gap-2 text-[12px]">
            <span class="font-semibold text-[color:var(--crm-muted-fg,#5b6478)]">
              {{ __('Live preview') }}
            </span>
            <span class="text-[11px] text-[color:var(--crm-faint,#8a94a6)]">
              8 × 3 {{ __('tile') }}
            </span>
            <span
              class="inline-flex h-6 items-center gap-1.5 rounded-md border border-dashed border-[color:var(--crm-border-strong,#d0d9e0)] px-2 text-[11.5px] font-medium text-[color:var(--crm-muted-fg,#5b6478)]"
            >
              <i
                class="block size-1.5 rounded-full bg-[color:var(--crm-warning,#a86a0b)]"
                aria-hidden="true"
              />
              {{ __('Example data') }}
            </span>
          </div>
          <div
            class="h-56 rounded-[10px] border border-[color:var(--crm-border,#e1e7ec)] bg-[color:var(--crm-card,#fff)] p-3"
          >
            <ReportChartTile
              :title="draft.title || __('Untitled chart')"
              :subtitle="previewSubtitle"
              :tile-type="draft.chart_type"
              :data="preview"
            />
          </div>
          <div
            v-if="previewSummary"
            class="mt-3 text-[11.5px] text-[color:var(--crm-muted-fg,#5b6478)]"
          >
            {{ previewSummary }}
          </div>
        </aside>
      </div>
    </template>
    <template #actions>
      <div class="flex w-full items-center justify-end gap-2">
        <Button size="sm" :label="__('Cancel')" @click="show = false" />
        <Button
          size="sm"
          variant="solid"
          :label="__('Add to dashboard')"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import ReportChartTile from './ReportChartTile.vue'
import { astraPaletteSwatches } from '@/utils/reports/chartColors'
import { Button, Dialog, FormControl, call } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  meta: { type: Object, default: () => ({}) },
  initialType: { type: String, default: 'bar' },
  initial: { type: Object, default: null },
})

const emit = defineEmits(['save'])
const show = defineModel({ type: Boolean, default: false })

const chartTypes = ['bar', 'line', 'donut', 'funnel', 'table']
const draft = reactive(emptyDraft())
const preview = ref(null)
const selectedSwatch = ref('c1')
let previewTimer = null

const chartTitle = computed(() => {
  const map = {
    bar: __('Bar chart tile'),
    line: __('Line chart tile'),
    donut: __('Pie chart tile'),
    funnel: __('Funnel tile'),
    table: __('Table tile'),
  }
  return map[draft.chart_type] || __('Chart tile')
})

const previewSubtitle = computed(() => {
  if (draft.aggregation === 'sum') return '₹ L'
  return ''
})

const previewSummary = computed(() => {
  const rows = preview.value?.data || []
  if (!rows.length) return ''
  return preview.value?.summary_text || ''
})

const moduleOptions = computed(() =>
  (props.meta.modules || []).map((m) => ({ label: m.label, value: m.value })),
)
const fields = computed(
  () => props.meta.fields_by_doctype?.[draft.doctype] || {},
)
const dimensionOptions = computed(() => fields.value.dimensions || [])
const numericOptions = computed(() => fields.value.numeric || [])
const dateOptions = computed(() => fields.value.dates || [])
const aggOptions = computed(
  () =>
    fields.value.aggregations || [
      { label: 'Count', value: 'count' },
      { label: 'Sum', value: 'sum' },
      { label: 'Avg', value: 'avg' },
    ],
)
const bucketOptions = computed(
  () =>
    fields.value.date_buckets || [
      { label: 'Day', value: 'day' },
      { label: 'Week', value: 'week' },
      { label: 'Month', value: 'month' },
      { label: 'Quarter', value: 'quarter' },
      { label: 'Year', value: 'year' },
    ],
)
const isDateDimension = computed(() =>
  (dateOptions.value || []).some((d) => d.value === draft.group_by),
)

watch(
  () => show.value,
  (open) => {
    if (!open) return
    Object.assign(draft, emptyDraft(), props.initial || {}, {
      chart_type: props.initial?.chart_type || props.initialType || 'bar',
    })
    queuePreview()
  },
)

watch(draft, () => queuePreview(), { deep: true })

function emptyDraft() {
  return {
    title: '',
    chart_type: 'bar',
    doctype: 'CRM Deal',
    aggregation: 'sum',
    field: 'deal_value',
    group_by: 'status',
    series_by: '',
    date_field: 'creation',
    date_bucket: 'month',
    filters: [],
    stacked: true,
    show_totals: true,
    columns: ['name', 'status', 'deal_value', 'deal_owner'],
    milestones: [
      { label: 'Qualification', field: 'status', value: 'Qualification' },
      { label: 'Negotiation', field: 'status', value: 'Negotiation' },
      { label: 'Won', field: 'status', value: 'Won' },
    ],
  }
}

function queuePreview() {
  clearTimeout(previewTimer)
  previewTimer = setTimeout(loadPreview, 350)
}

async function loadPreview() {
  try {
    preview.value = await call('crm.api.reports.evaluate_chart', {
      config: JSON.stringify(draft),
      period: 'this_quarter',
    })
  } catch (e) {
    preview.value = { type: draft.chart_type, data: [], title: draft.title }
  }
}

function submit() {
  emit('save', JSON.parse(JSON.stringify(draft)))
  show.value = false
}
</script>
