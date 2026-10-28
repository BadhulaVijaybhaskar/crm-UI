<template>
  <div class="flex h-full min-h-0 flex-col">
    <div
      class="mb-0 flex items-center gap-1.5 truncate text-[12px] font-semibold text-[color:var(--crm-muted-fg,#5b6478)]"
    >
      <LucideGripVertical
        v-if="editing"
        class="size-3.5 shrink-0 text-[color:var(--crm-faint,#8a94a6)]"
        aria-hidden="true"
      />
      <span class="truncate">{{ title }}</span>
      <span
        v-if="subtitle"
        class="shrink-0 font-medium text-[color:var(--crm-faint,#8a94a6)]"
      >
        · {{ subtitle }}
      </span>
      <span class="flex-1" />
      <LucideEllipsis
        v-if="editing"
        class="size-3.5 shrink-0 text-[color:var(--crm-faint,#8a94a6)]"
        aria-hidden="true"
      />
    </div>

    <!-- Funnel — centered taper (Figma PNG); label left, value right -->
    <div v-if="kind === 'funnel'" class="mt-2.5 flex min-h-0 flex-1 flex-col gap-1.5">
      <div
        v-for="(step, i) in funnelSteps"
        :key="i"
        class="grid grid-cols-[70px_1fr_36px] items-center gap-2 text-[11.5px]"
      >
        <span class="truncate text-[color:var(--crm-fg,#0b1324)]">{{
          step.label
        }}</span>
        <div class="flex min-w-0 justify-center">
          <div
            class="h-5 rounded"
            :style="{
              width: `${step.width}%`,
              background: step.color,
            }"
          />
        </div>
        <span
          class="text-right font-semibold tabular-nums text-[color:var(--crm-fg,#0b1324)]"
        >
          {{ step.value }}
        </span>
      </div>
      <div
        v-if="funnelFooter"
        class="mt-auto pt-2 text-[11.5px] text-[color:var(--crm-muted-fg,#5b6478)]"
      >
        {{ funnelFooter }}
      </div>
    </div>

    <!-- Donut legend list -->
    <div v-else-if="kind === 'donut'" class="mt-2 flex flex-1 items-center gap-4">
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
          <span class="truncate text-[color:var(--crm-fg,#0b1324)]">{{
            row.label
          }}</span>
          <span class="ml-auto text-[color:var(--crm-muted-fg,#5b6478)]">{{
            formatKpiValue(row.value, 'number')
          }}</span>
        </li>
      </ul>
    </div>

    <!-- Table / deal rows -->
    <div v-else-if="kind === 'table'" class="mt-1 min-h-0 flex-1 overflow-auto">
      <div
        v-for="(row, i) in tableRows"
        :key="i"
        class="flex h-11 items-center gap-2.5 border-t border-[color:var(--crm-border,#e1e7ec)] text-[12.5px] first:border-t-0"
      >
        <span
          class="min-w-0 flex-1 truncate font-semibold text-[color:var(--crm-fg,#0b1324)]"
        >
          {{ row.name || row.label || row[tableCols[0]] }}
        </span>
        <span
          v-if="row.status || row.stage || row[tableCols[1]]"
          class="inline-flex h-[22px] max-w-[140px] items-center gap-1.5 truncate rounded-md px-1.5 text-[11.5px] text-[color:var(--crm-muted-fg,#5b6478)]"
        >
          <i
            class="block size-1.5 shrink-0 rounded-[2px]"
            :style="{
              background:
                stageColor(row.status || row.stage || row[tableCols[1]]) ||
                'var(--crm-c6)',
            }"
            aria-hidden="true"
          />
          {{ row.status || row.stage || row[tableCols[1]] }}
        </span>
        <span
          class="w-16 text-right font-semibold tabular-nums text-[color:var(--crm-fg,#0b1324)]"
        >
          {{
            (() => {
              const raw = row.deal_value ?? row.value ?? row[tableCols[2]]
              if (typeof raw === 'string') return raw
              return formatKpiValue(
                raw,
                typeof raw === 'number' ? 'currency' : 'number',
              )
            })()
          }}
        </span>
        <span
          v-if="row.owner || row.deal_owner || row.initials"
          class="flex size-5 shrink-0 items-center justify-center rounded-full bg-[color:var(--crm-primary-soft,#e4f2f6)] text-[9px] font-bold text-[color:var(--crm-primary,#0a7393)]"
        >
          {{ rowInitials(row) }}
        </span>
      </div>
    </div>

    <!-- Line chart -->
    <div v-else-if="kind === 'line'" class="mt-2 min-h-0 flex-1">
      <svg
        v-if="lineSeries.length"
        class="h-full w-full"
        viewBox="0 0 520 140"
        preserveAspectRatio="none"
      >
        <line
          v-for="g in [28, 70, 112]"
          :key="g"
          x1="8"
          :y1="g"
          x2="512"
          :y2="g"
          stroke="var(--crm-border, #e1e7ec)"
          stroke-width="1"
        />
        <polyline
          v-for="(series, si) in lineSeries"
          :key="si"
          fill="none"
          :stroke="series.color"
          :stroke-width="series.dashed ? 2 : 2.5"
          :stroke-dasharray="series.dashed ? '4 3' : undefined"
          :points="series.points"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
      <div
        v-else
        class="flex h-full items-center justify-center text-[12px] text-[color:var(--crm-muted-fg,#5b6478)]"
      >
        {{ __('No data for this period') }}
      </div>
    </div>

    <!-- Bar chart with value labels -->
    <div v-else-if="kind === 'bar'" class="mt-2 min-h-0 flex-1">
      <div
        v-if="bars.length"
        class="hb flex h-full min-h-0 items-end gap-2 pb-[18px] pt-2"
      >
        <div
          v-for="(bar, i) in bars"
          :key="i"
          class="relative flex h-full min-w-0 flex-1 flex-col items-center justify-end gap-1"
        >
          <em
            class="absolute -top-4 text-[11px] font-semibold not-italic text-[color:var(--crm-fg,#0b1324)]"
          >
            {{ bar.display }}
          </em>
          <i
            class="block w-full rounded-t"
            :style="{
              height: `${bar.height}%`,
              background: bar.color,
              minHeight: bar.value ? '4px' : '0',
            }"
          />
          <span
            class="w-full truncate text-center text-[10.5px] text-[color:var(--crm-muted-fg,#5b6478)]"
          >
            {{ bar.short }}
          </span>
        </div>
      </div>
      <div
        v-else
        class="flex h-full items-center justify-center text-[12px] text-[color:var(--crm-muted-fg,#5b6478)]"
      >
        {{ __('No data for this period') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { chartColor, stageColor } from '@/utils/reports/chartColors'
import { formatKpiValue } from '@/utils/reports/formatKpi'
import LucideEllipsis from '~icons/lucide/ellipsis'
import LucideGripVertical from '~icons/lucide/grip-vertical'
import { computed } from 'vue'

/** Figma PNG funnel palette (centered taper) — PNG wins over HTML c2/c3/…. */
const FUNNEL_COLORS = [
  'var(--crm-c6)',
  'var(--crm-c4)',
  'var(--crm-c2)',
  'var(--crm-c5)',
  'var(--crm-c3)',
]

/** Measured from Figma PNG bar spans (relative to top bar). */
const FUNNEL_WIDTHS = [100, 40, 14, 10, 10]

const props = defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  tileType: { type: String, default: 'bar' },
  data: { type: Object, default: null },
  editing: { type: Boolean, default: false },
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
  const steps = props.data?.steps || props.data?.data || []
  const max = Math.max(...steps.map((s) => Number(s.value) || 0), 1)
  return steps.map((s, i) => {
    const width =
      s.width != null
        ? Number(s.width)
        : FUNNEL_WIDTHS[i] != null
          ? FUNNEL_WIDTHS[i]
          : Math.max(12, ((Number(s.value) || 0) / max) * 100)
    return {
      label: s.label,
      value: s.value,
      width,
      color: s.color || FUNNEL_COLORS[i % FUNNEL_COLORS.length],
    }
  })
})

const funnelFooter = computed(() => {
  if (props.data?.footer) return props.data.footer
  const s = props.data?.summary
  if (!s) return ''
  const conv = Number(s.conversion_pct || 0).toFixed(1)
  const median = s.median_days != null ? ` · median ${s.median_days} days` : ''
  return `${__('Lead to won')} ${conv}%${median}`
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

const tableCols = computed(() => props.data?.columns || [])
const tableRows = computed(() => props.data?.rows || props.data?.data || [])

const bars = computed(() => {
  let rows = props.data?.data || []
  if ((!rows || !rows.length) && props.data?.labels && props.data?.values) {
    rows = props.data.labels.map((label, i) => ({
      label,
      value: props.data.values[i],
      height: props.data.heights?.[i],
      color: props.data.colors?.[i],
    }))
  }
  if ((!rows || !rows.length) && props.data?.series?.[0]?.data) {
    const labels = props.data.labels || []
    rows = props.data.series[0].data.map((value, i) => ({
      label: labels[i] || String(i + 1),
      value,
      height: props.data.heights?.[i],
      color: props.data.colors?.[i],
    }))
  }
  const max = Math.max(...rows.map((r) => Number(r.value) || 0), 1)
  return rows.slice(0, 8).map((r, i) => {
    const n = Number(r.value) || 0
    const display =
      r.display != null
        ? String(r.display)
        : n >= 1000
          ? formatKpiValue(n, 'currency').replace('₹', '')
          : // Figma bar labels use one decimal (18.0, 22.2, …)
            Number(n).toFixed(1)
    const height =
      r.height != null
        ? Number(r.height)
        : (n / max) * 70 + (n ? 10 : 0)
    return {
      label: r.label,
      value: r.value,
      height,
      short: String(r.label || ''),
      display,
      color: r.color || stageColor(r.label) || chartColor(i),
    }
  })
})

const lineSeries = computed(() => {
  const labels = props.data?.labels || []
  const series = props.data?.series || []
  if (!series.length) return []

  const allVals = series.flatMap((s) => (s.data || []).map(Number)).filter(Number.isFinite)
  const max = Math.max(...allVals, 1)
  const min = Math.min(...allVals, 0)
  const span = Math.max(max - min, 1)
  const n = Math.max(labels.length, ...series.map((s) => (s.data || []).length), 1)
  const padX = 16
  const padY = 16
  const w = 520 - padX * 2
  const h = 140 - padY * 2

  return series.map((s, si) => {
    const data = s.data || []
    const pts = data.map((v, i) => {
      const x = padX + (n <= 1 ? w / 2 : (i / (n - 1)) * w)
      const y = padY + h - ((Number(v) - min) / span) * h
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    const dashed = Boolean(s.dashed || si > 0)
    return {
      name: s.name,
      dashed,
      color: s.color || (dashed ? 'var(--crm-c6)' : 'var(--crm-c1)'),
      points: pts.join(' '),
    }
  })
})

function rowInitials(row) {
  if (row.initials) return row.initials
  const name = String(row.owner || row.deal_owner || row.owner_name || '')
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.slice(0, 2).toUpperCase() || '—'
}
</script>
