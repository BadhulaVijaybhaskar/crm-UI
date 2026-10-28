<template>
  <Dialog
    v-model="show"
    :options="{ title: chartTitle, size: '4xl' }"
  >
    <template #body-content>
      <p class="mb-3 text-[12px] text-[color:var(--crm-muted-fg,#64748b)]">
        {{ __('Step 2 of 2 · data') }}
      </p>
      <div class="grid gap-5 md:grid-cols-[1fr_320px]">
        <div class="space-y-4">
          <div>
            <div class="mb-1 text-[12.5px] text-[color:var(--crm-muted-fg,#64748b)]">
              {{ __('Chart type') }}
            </div>
            <div class="flex flex-wrap gap-1 rounded-md border border-[color:var(--crm-border,#e2e8f0)] p-0.5">
              <button
                v-for="t in chartTypes"
                :key="t"
                type="button"
                class="rounded px-2.5 py-1 text-[12.5px] capitalize"
                :class="
                  draft.chart_type === t
                    ? 'bg-[color:var(--crm-primary,#0a7393)] text-[color:var(--crm-primary-fg,#fff)]'
                    : 'text-[color:var(--crm-fg,#0f172a)]'
                "
                @click="draft.chart_type = t"
              >
                {{ __(t === 'donut' ? 'pie' : t) }}
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
            <div class="mb-2 text-[12.5px] text-[color:var(--crm-muted-fg,#64748b)]">
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
                    ? 'ring-2 ring-[color:var(--crm-primary,#0a7393)]'
                    : 'ring-1 ring-[color:var(--crm-border-strong,#94a3b8)]'
                "
                :style="{ background: sw.css }"
                :title="sw.label"
                @click="selectedSwatch = sw.key"
              />
            </div>
          </div>
        </div>

        <aside
          class="rounded-[10px] border border-[color:var(--crm-border,#e2e8f0)] bg-[color:var(--crm-card,#fff)] p-3"
        >
          <div class="mb-2 flex items-center justify-between text-[12px]">
            <span class="font-semibold text-[color:var(--crm-muted-fg,#64748b)]">
              {{ __('Live preview') }}
            </span>
            <span class="text-[11px] text-[color:var(--crm-faint,#94a3b8)]">
              8 × 3 {{ __('tile') }}
            </span>
          </div>
          <div class="h-56">
            <ReportChartTile
              :title="draft.title || __('Untitled chart')"
              :tile-type="draft.chart_type"
              :data="preview"
            />
          </div>
        </aside>
      </div>
    </template>
    <template #actions>
      <Button :label="__('Cancel')" @click="show = false" />
      <Button variant="solid" :label="__('Add to dashboard')" @click="submit" />
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
