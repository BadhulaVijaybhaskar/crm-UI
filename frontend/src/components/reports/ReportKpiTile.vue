<template>
  <div class="report-kpi-tile flex h-full flex-col">
    <div
      class="flex items-center gap-1.5 text-[12px] font-semibold text-[color:var(--crm-muted-fg,#5b6478)]"
    >
      <svg
        v-if="editing"
        class="size-3.5 shrink-0 text-[color:var(--crm-faint,#8a94a6)]"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <circle cx="9" cy="6" r="1" />
        <circle cx="15" cy="6" r="1" />
        <circle cx="9" cy="12" r="1" />
        <circle cx="15" cy="12" r="1" />
        <circle cx="9" cy="18" r="1" />
        <circle cx="15" cy="18" r="1" />
      </svg>
      <span class="min-w-0 truncate">{{ title }}</span>
      <span
        v-if="data?.kpi_type === 'calculated'"
        class="ml-1 inline-flex h-[18px] shrink-0 items-center rounded-[5px] px-[7px] text-[10px] font-semibold text-[color:var(--crm-primary,#0a7393)] bg-[color:var(--crm-primary-soft,#e4f2f6)]"
      >
        ƒ calc
      </span>
      <span class="flex-1" />
      <svg
        v-if="editing && !dragging && !selected"
        class="size-3.5 shrink-0 text-[color:var(--crm-faint,#8a94a6)]"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <circle cx="5" cy="12" r="1" />
        <circle cx="12" cy="12" r="1" />
        <circle cx="19" cy="12" r="1" />
      </svg>
    </div>
    <div
      class="mt-1.5 text-[26px] font-semibold tracking-[-0.02em] text-[color:var(--crm-fg,#0b1324)] tabular-nums"
    >
      {{ displayValue }}
    </div>
    <div
      v-if="deltaParts.lead || deltaParts.trail"
      class="text-[11.5px] font-semibold leading-[16.7px]"
    >
      <span
        v-if="deltaParts.lead"
        :class="
          delta?.direction === 'up'
            ? 'text-[color:var(--crm-success,#0f8a5f)]'
            : delta?.direction === 'down'
              ? 'text-[color:var(--crm-danger,#c93b3b)]'
              : 'text-[color:var(--crm-muted-fg,#5b6478)]'
        "
      >
        {{ deltaParts.lead }}
      </span>
      <span
        v-if="deltaParts.trail"
        class="font-medium text-[color:var(--crm-muted-fg,#5b6478)]"
        :class="deltaParts.lead ? '' : 'font-semibold'"
      >
        {{ deltaParts.trail }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { formatDelta, formatKpiValue } from '@/utils/reports/formatKpi'
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  data: { type: Object, default: null },
  editing: { type: Boolean, default: false },
  dragging: { type: Boolean, default: false },
  selected: { type: Boolean, default: false },
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

/** Figma: coloured lead (▲ 8.2%) + muted trailing copy (vs last quarter / · 4 deals). */
const deltaParts = computed(() => {
  if (props.data?.delta_label) {
    return { lead: '', trail: props.data.delta_label }
  }
  if (!delta.value) return { lead: '', trail: '' }
  const lead = delta.value.text
  if (props.data?.kpi_type === 'calculated' && props.data?.formula) {
    const hint = String(props.data.formula)
      .replace(/[{}]/g, '')
      .replace(/\*/g, '×')
      .replace(/\//g, '÷')
      .replace(/_/g, ' ')
    return { lead, trail: ` = ${hint}` }
  }
  if (props.data?.secondary) {
    // Figma: "▲ 14% 4 deals" — space only, no middle dot
    return { lead, trail: ` ${props.data.secondary}` }
  }
  const compare = props.data?.compare_label
  if (compare === '') return { lead, trail: '' }
  return { lead, trail: ` ${compare || __('vs last quarter')}` }
})
</script>
