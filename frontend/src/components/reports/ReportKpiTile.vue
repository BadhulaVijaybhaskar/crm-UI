<template>
  <div class="report-kpi-tile flex h-full flex-col">
    <div class="flex items-center gap-1.5 text-[12px] font-semibold text-[color:var(--crm-muted-fg,#64748b)]">
      <span
        v-if="data?.kpi_type === 'calculated'"
        class="inline-flex h-5 items-center rounded px-1.5 text-[10px] font-semibold text-[color:var(--crm-primary,#0a7393)] bg-[color:var(--crm-primary-soft,#e6f4f8)]"
      >
        f calc
      </span>
      <span class="truncate">{{ title }}</span>
    </div>
    <div
      class="mt-1.5 text-[26px] font-semibold tracking-[-0.02em] text-[color:var(--crm-fg,#0f172a)]"
    >
      {{ displayValue }}
    </div>
    <div
      v-if="delta"
      class="mt-1 text-[11.5px]"
      :class="
        delta.direction === 'up'
          ? 'text-[color:var(--crm-success,#16a34a)]'
          : delta.direction === 'down'
            ? 'text-[color:var(--crm-danger,#dc2626)]'
            : 'text-[color:var(--crm-muted-fg,#64748b)]'
      "
    >
      {{ delta.text }}
      <span class="text-[color:var(--crm-muted-fg,#64748b)]">
        {{ compareLabel }}
      </span>
    </div>
    <div
      v-if="data?.formula && data?.kpi_type === 'calculated'"
      class="mt-auto pt-2 text-[11px] text-[color:var(--crm-muted-fg,#64748b)]"
    >
      {{ formulaHint }}
    </div>
  </div>
</template>

<script setup>
import { formatDelta, formatKpiValue } from '@/utils/reports/formatKpi'
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  data: { type: Object, default: null },
})

const displayValue = computed(() =>
  formatKpiValue(props.data?.value, props.data?.format || 'number'),
)

const delta = computed(() => formatDelta(props.data?.delta_pct))

const compareLabel = computed(() => {
  if (!delta.value) return ''
  return 'vs previous period'
})

const formulaHint = computed(() => {
  if (!props.data?.formula) return ''
  return props.data.formula.replace(/[{}]/g, '')
})
</script>
