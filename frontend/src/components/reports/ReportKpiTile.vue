<template>
  <div class="report-kpi-tile flex h-full flex-col">
    <div
      class="flex items-center gap-1.5 text-[12px] font-semibold text-[color:var(--crm-muted-fg,#5b6478)]"
    >
      <LucideGripVertical
        v-if="editing"
        class="size-3.5 shrink-0 text-[color:var(--crm-faint,#8a94a6)]"
        aria-hidden="true"
      />
      <span
        v-if="data?.kpi_type === 'calculated'"
        class="inline-flex h-4 items-center rounded px-[5px] text-[10px] font-semibold text-[color:var(--crm-primary,#0a7393)] bg-[color:var(--crm-primary-soft,#e4f2f6)]"
      >
        ƒ calc
      </span>
      <span class="min-w-0 flex-1 truncate">{{ title }}</span>
      <LucideEllipsis
        v-if="editing"
        class="size-3.5 shrink-0 text-[color:var(--crm-faint,#8a94a6)]"
        aria-hidden="true"
      />
    </div>
    <div
      class="mt-1.5 text-[26px] font-semibold leading-[1.1] tracking-[-0.02em] text-[color:var(--crm-fg,#0b1324)]"
    >
      {{ displayValue }}
    </div>
    <div
      v-if="deltaLine"
      class="mt-1 text-[11.5px] font-semibold"
      :class="
        delta?.direction === 'up'
          ? 'text-[color:var(--crm-success,#0f8a5f)]'
          : delta?.direction === 'down'
            ? 'text-[color:var(--crm-danger,#c93b3b)]'
            : 'text-[color:var(--crm-muted-fg,#5b6478)]'
      "
    >
      {{ deltaLine }}
    </div>
  </div>
</template>

<script setup>
import { formatDelta, formatKpiValue } from '@/utils/reports/formatKpi'
import LucideEllipsis from '~icons/lucide/ellipsis'
import LucideGripVertical from '~icons/lucide/grip-vertical'
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  data: { type: Object, default: null },
  editing: { type: Boolean, default: false },
})

const displayValue = computed(() => {
  if (props.data?.display) return props.data.display
  return formatKpiValue(props.data?.value, props.data?.format || 'number')
})

const delta = computed(() => {
  if (props.data?.delta_pts != null) {
    const n = Number(props.data.delta_pts)
    if (!Number.isFinite(n)) return null
    const sign = n > 0 ? '▲' : n < 0 ? '▼' : '•'
    return {
      text: `${sign} ${Math.abs(Math.round(n * 10) / 10)} pts`,
      direction: n > 0 ? 'up' : n < 0 ? 'down' : 'flat',
    }
  }
  return formatDelta(props.data?.delta_pct)
})

const deltaLine = computed(() => {
  if (props.data?.delta_label) return props.data.delta_label
  if (!delta.value) return ''
  const base = delta.value.text
  if (props.data?.kpi_type === 'calculated' && props.data?.formula) {
    const hint = String(props.data.formula)
      .replace(/[{}]/g, '')
      .replace(/\*/g, '×')
      .replace(/\//g, '÷')
      .replace(/_/g, ' ')
    return `${base} = ${hint}`
  }
  if (props.data?.secondary) {
    return `${base} · ${props.data.secondary}`
  }
  const compare = props.data?.compare_label
  if (compare === '') return base
  return `${base} ${compare || __('vs last quarter')}`
})
</script>
