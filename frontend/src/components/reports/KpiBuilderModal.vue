<template>
  <Dialog
    v-model="show"
    :options="{ title: __('KPI tile'), size: '4xl' }"
  >
    <template #body-content>
      <p class="mb-3 text-[12px] text-[color:var(--crm-muted-fg,#64748b)]">
        {{ __('Step 2 of 2 · data') }}
      </p>
      <div class="grid gap-5 md:grid-cols-[1fr_280px]">
        <div class="space-y-4">
          <FormControl
            v-model="draft.title"
            :label="__('KPI name')"
            type="text"
          />

          <div>
            <div class="mb-1 text-[12.5px] text-[color:var(--crm-muted-fg,#64748b)]">
              {{ __('Type') }}
            </div>
            <div class="inline-flex rounded-md border border-[color:var(--crm-border,#e2e8f0)] p-0.5">
              <button
                v-for="t in ['simple', 'calculated']"
                :key="t"
                type="button"
                class="rounded px-3 py-1 text-[12.5px] capitalize"
                :class="
                  draft.kpi_type === t
                    ? 'bg-[color:var(--crm-primary,#0a7393)] text-[color:var(--crm-primary-fg,#fff)]'
                    : 'text-[color:var(--crm-fg,#0f172a)]'
                "
                @click="draft.kpi_type = t"
              >
                {{ __(t) }}
              </button>
            </div>
          </div>

          <template v-if="draft.kpi_type === 'calculated'">
            <div>
              <div class="mb-1 text-[12.5px] text-[color:var(--crm-muted-fg,#64748b)]">
                {{ __('Formula') }}
              </div>
              <div
                class="rounded-[7px] border border-[color:var(--crm-primary,#0a7393)] bg-[color:var(--crm-card,#fff)] p-2.5 font-mono text-[12.5px] shadow-[0_0_0_3px_var(--crm-primary-soft,#e6f4f8)]"
              >
                <input
                  v-model="draft.formula"
                  class="w-full bg-transparent outline-none"
                  :placeholder="'{won_value} / {won_deals}'"
                />
              </div>
              <div class="mt-2 flex flex-wrap gap-1.5">
                <button
                  v-for="op in ['+', '-', '×', '÷', '( )']"
                  :key="op"
                  type="button"
                  class="rounded px-2 py-1 text-[12px] font-bold text-[color:var(--crm-muted-fg,#64748b)] ring-1 ring-[color:var(--crm-border,#e2e8f0)]"
                  @click="insertOp(op)"
                >
                  {{ op }}
                </button>
                <button
                  v-for="key in Object.keys(draft.formula_inputs)"
                  :key="key"
                  type="button"
                  class="h-[22px] rounded-[5px] bg-[color:var(--crm-primary-soft,#e6f4f8)] px-2 text-[11.5px] font-semibold text-[color:var(--crm-primary,#0a7393)]"
                  @click="insertRef(key)"
                >
                  + {{ key }}
                </button>
                <button
                  type="button"
                  class="h-[22px] rounded-[5px] px-2 text-[11.5px] font-semibold text-[color:var(--crm-primary,#0a7393)] ring-1 ring-[color:var(--crm-border,#e2e8f0)]"
                  @click="addInput"
                >
                  + {{ __('KPI') }}
                </button>
              </div>
            </div>

            <div class="space-y-2">
              <div class="text-[12.5px] font-semibold text-[color:var(--crm-fg,#0f172a)]">
                {{ __('Inputs') }}
              </div>
              <div
                v-for="(cfg, key) in draft.formula_inputs"
                :key="key"
                class="rounded-md border border-[color:var(--crm-border,#e2e8f0)] p-3"
              >
                <div class="mb-2 flex items-center justify-between">
                  <input
                    class="bg-transparent text-[13px] font-semibold outline-none"
                    :value="key"
                    @change="renameInput(key, $event.target.value)"
                  />
                  <button
                    type="button"
                    class="text-[11px] text-[color:var(--crm-danger,#dc2626)]"
                    @click="delete draft.formula_inputs[key]"
                  >
                    {{ __('Remove') }}
                  </button>
                </div>
                <SimpleKpiFields v-model="draft.formula_inputs[key]" :meta="meta" />
              </div>
            </div>
          </template>

          <SimpleKpiFields v-else v-model="draft" :meta="meta" />

          <div class="grid grid-cols-2 gap-3">
            <FormControl
              v-model="draft.format"
              type="select"
              :label="__('Format')"
              :options="[
                { label: __('Number'), value: 'number' },
                { label: __('Currency'), value: 'currency' },
                { label: __('Percent'), value: 'percent' },
              ]"
            />
            <FormControl
              v-model="draft.compare_with"
              type="select"
              :label="__('Compare with')"
              :options="[
                { label: __('None'), value: 'none' },
                { label: __('Previous period'), value: 'previous_period' },
              ]"
            />
          </div>

          <div
            class="rounded-md bg-[color:var(--crm-primary-soft,#e6f4f8)] px-3 py-2 text-[11.5px] text-[color:var(--crm-fg,#0f172a)]"
          >
            {{ __('Sales users see this KPI on their own records only.') }}
          </div>
        </div>

        <aside
          class="rounded-[10px] border border-[color:var(--crm-border,#e2e8f0)] bg-[color:var(--crm-card,#fff)] p-3"
        >
          <div class="mb-2 text-[12px] font-semibold text-[color:var(--crm-muted-fg,#64748b)]">
            {{ __('Live preview') }}
          </div>
          <ReportKpiTile :title="draft.title || __('Untitled KPI')" :data="preview" />
          <div
            v-if="preview?.breakdown"
            class="mt-4 space-y-1 border-t border-[color:var(--crm-border,#e2e8f0)] pt-3 text-[11.5px]"
          >
            <div class="font-semibold text-[color:var(--crm-muted-fg,#64748b)]">
              {{ __('How it is worked out') }}
            </div>
            <div
              v-for="(val, key) in preview.breakdown"
              :key="key"
              class="flex justify-between text-[color:var(--crm-fg,#0f172a)]"
            >
              <span>{{ key }}</span>
              <span>{{ formatKpiValue(val, 'number') }}</span>
            </div>
            <div class="flex justify-between font-semibold">
              <span>{{ __('Result') }}</span>
              <span>{{ formatKpiValue(preview.value, draft.format) }}</span>
            </div>
          </div>
        </aside>
      </div>
    </template>
    <template #actions>
      <Button :label="__('Cancel')" @click="show = false" />
      <Button
        variant="solid"
        :label="__('Add to dashboard')"
        :loading="previewing"
        @click="submit"
      />
    </template>
  </Dialog>
</template>

<script setup>
import ReportKpiTile from './ReportKpiTile.vue'
import SimpleKpiFields from './SimpleKpiFields.vue'
import { formatKpiValue } from '@/utils/reports/formatKpi'
import { Button, Dialog, FormControl, call } from 'frappe-ui'
import { reactive, ref, watch } from 'vue'

const props = defineProps({
  meta: { type: Object, default: () => ({}) },
  initial: { type: Object, default: null },
})

const emit = defineEmits(['save'])
const show = defineModel({ type: Boolean, default: false })

const draft = reactive(emptyDraft())
const preview = ref(null)
const previewing = ref(false)
let previewTimer = null

watch(
  () => show.value,
  (open) => {
    if (!open) return
    Object.assign(draft, emptyDraft(), props.initial || {})
    queuePreview()
  },
)

watch(draft, () => queuePreview(), { deep: true })

function emptyDraft() {
  return {
    title: '',
    kpi_type: 'simple',
    doctype: 'CRM Deal',
    aggregation: 'sum',
    field: 'deal_value',
    date_field: 'creation',
    filters: [],
    formula: '',
    formula_inputs: {
      won_value: {
        doctype: 'CRM Deal',
        aggregation: 'sum',
        field: 'deal_value',
        date_field: 'closed_date',
        filters: [],
      },
      won_deals: {
        doctype: 'CRM Deal',
        aggregation: 'count',
        date_field: 'closed_date',
        filters: [],
      },
    },
    format: 'currency',
    compare_with: 'previous_period',
  }
}

function queuePreview() {
  clearTimeout(previewTimer)
  previewTimer = setTimeout(loadPreview, 350)
}

async function loadPreview() {
  previewing.value = true
  try {
    preview.value = await call('crm.api.reports.evaluate_kpi', {
      config: JSON.stringify(draft),
      period: 'this_quarter',
    })
  } catch (e) {
    preview.value = {
      title: draft.title,
      value: 0,
      format: draft.format,
      kpi_type: draft.kpi_type,
      formula: draft.formula,
    }
  } finally {
    previewing.value = false
  }
}

function insertOp(op) {
  if (op === '( )') {
    draft.formula = `${draft.formula || ''}()`
    return
  }
  const map = { '×': '*', '÷': '/' }
  draft.formula = `${draft.formula || ''} ${map[op] || op} `
}

function insertRef(key) {
  draft.formula = `${draft.formula || ''}{${key}}`
}

function addInput() {
  const key = `kpi_${Object.keys(draft.formula_inputs).length + 1}`
  draft.formula_inputs[key] = {
    doctype: 'CRM Deal',
    aggregation: 'count',
    date_field: 'creation',
    filters: [],
  }
}

function renameInput(oldKey, newKey) {
  const key = (newKey || '').trim().replace(/\W+/g, '_')
  if (!key || key === oldKey || draft.formula_inputs[key]) return
  draft.formula_inputs[key] = draft.formula_inputs[oldKey]
  delete draft.formula_inputs[oldKey]
  if (draft.formula) {
    draft.formula = draft.formula.replaceAll(`{${oldKey}}`, `{${key}}`)
  }
}

function submit() {
  emit('save', JSON.parse(JSON.stringify(draft)))
  show.value = false
}
</script>
