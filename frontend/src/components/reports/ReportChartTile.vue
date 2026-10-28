<template>
  <div class="flex h-full min-h-0 flex-col">
    <div
      class="mb-2 truncate text-[12px] font-semibold text-[color:var(--crm-muted-fg,#64748b)]"
    >
      {{ title }}
    </div>

    <!-- Funnel -->
    <div v-if="kind === 'funnel'" class="flex flex-1 flex-col justify-center gap-2">
      <div
        v-for="(step, i) in funnelSteps"
        :key="i"
        class="flex items-center gap-2"
      >
        <div
          class="h-7 rounded transition-all"
          :style="{
            width: `${step.width}%`,
            background: chartColor(i),
          }"
        />
        <div class="min-w-0 flex-1 text-[11.5px] text-[color:var(--crm-fg,#0f172a)]">
          <span class="font-semibold">{{ step.label }}</span>
          <span class="text-[color:var(--crm-muted-fg,#64748b)]"> · {{ step.value }}</span>
        </div>
      </div>
      <div
        v-if="data?.summary"
        class="mt-1 text-[11px] text-[color:var(--crm-muted-fg,#64748b)]"
      >
        {{ __('Conversion') }}
        {{ Number(data.summary.conversion_pct || 0).toFixed(1) }}%
      </div>
    </div>

    <!-- Donut legend list -->
    <div v-else-if="kind === 'donut'" class="flex flex-1 items-center gap-4">
      <div
        class="relative size-28 shrink-0 rounded-full"
        :style="donutStyle"
      />
      <ul class="min-w-0 flex-1 space-y-1.5">
        <li
          v-for="(row, i) in donutRows"
          :key="i"
          class="flex items-center gap-2 text-[11.5px]"
        >
          <span
            class="size-2.5 shrink-0 rounded-sm"
            :style="{ background: stageColor(row.label) || chartColor(i) }"
          />
          <span class="truncate text-[color:var(--crm-fg,#0f172a)]">{{ row.label }}</span>
          <span class="ml-auto text-[color:var(--crm-muted-fg,#64748b)]">{{
            formatKpiValue(row.value, 'number')
          }}</span>
        </li>
      </ul>
    </div>

    <!-- Table -->
    <div v-else-if="kind === 'table'" class="min-h-0 flex-1 overflow-auto">
      <table class="w-full text-left text-[12px]">
        <thead>
          <tr class="text-[color:var(--crm-muted-fg,#64748b)]">
            <th
              v-for="col in data?.columns || []"
              :key="col"
              class="pb-1 font-medium"
            >
              {{ col }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, i) in data?.rows || []"
            :key="i"
            class="border-t border-[color:var(--crm-border,#e2e8f0)]"
          >
            <td
              v-for="col in data?.columns || []"
              :key="col"
              class="py-1.5 text-[color:var(--crm-fg,#0f172a)]"
            >
              {{ row[col] }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Bar / line via frappe-ui charts when axis data present -->
    <div v-else class="min-h-0 flex-1">
      <div v-if="bars.length" class="flex h-full items-end gap-2.5 px-1 pb-5">
        <div
          v-for="(bar, i) in bars"
          :key="i"
          class="flex min-w-0 flex-1 flex-col items-center justify-end"
        >
          <div
            class="w-full rounded-t"
            :style="{
              height: `${bar.height}%`,
              background: stageColor(bar.label) || chartColor(i),
              minHeight: bar.value ? '4px' : '0',
            }"
          />
          <div
            class="mt-1 w-full truncate text-center text-[10.5px] text-[color:var(--crm-muted-fg,#64748b)]"
          >
            {{ bar.short }}
          </div>
        </div>
      </div>
      <div
        v-else
        class="flex h-full items-center justify-center text-[12px] text-[color:var(--crm-muted-fg,#64748b)]"
      >
        {{ __('No data for this period') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { chartColor, stageColor } from '@/utils/reports/chartColors'
import { formatKpiValue } from '@/utils/reports/formatKpi'
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  tileType: { type: String, default: 'bar' },
  data: { type: Object, default: null },
})

const kind = computed(() => {
  const t = (props.tileType || props.data?.type || 'bar').toLowerCase()
  if (t === 'pie' || t === 'donut' || t === 'donut_chart') return 'donut'
  if (t === 'funnel') return 'funnel'
  if (t === 'table') return 'table'
  if (t === 'line') return 'line'
  return 'bar'
})

const funnelSteps = computed(() => {
  const steps = props.data?.data || []
  const max = Math.max(...steps.map((s) => Number(s.value) || 0), 1)
  return steps.map((s) => ({
    label: s.label,
    value: s.value,
    width: Math.max(12, ((Number(s.value) || 0) / max) * 100),
  }))
})

const donutRows = computed(() => props.data?.data || [])

const donutStyle = computed(() => {
  const rows = donutRows.value
  const total = rows.reduce((s, r) => s + (Number(r.value) || 0), 0) || 1
  let acc = 0
  const stops = rows.map((r, i) => {
    const start = (acc / total) * 360
    acc += Number(r.value) || 0
    const end = (acc / total) * 360
    const color = stageColor(r.label) || chartColor(i)
    return `${color} ${start}deg ${end}deg`
  })
  return {
    background: `conic-gradient(${stops.join(', ')})`,
    mask: 'radial-gradient(farthest-side, transparent 55%, #000 56%)',
    WebkitMask: 'radial-gradient(farthest-side, transparent 55%, #000 56%)',
  }
})

const bars = computed(() => {
  const rows = props.data?.data || []
  const max = Math.max(...rows.map((r) => Number(r.value) || 0), 1)
  return rows.slice(0, 8).map((r) => ({
    label: r.label,
    value: r.value,
    height: ((Number(r.value) || 0) / max) * 100,
    short: String(r.label || '').split(/[\s/]/)[0] || r.label,
  }))
})
</script>
