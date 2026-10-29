<template>
  <div class="flex h-full min-h-0 flex-col">
    <div
      class="mb-0 flex items-center gap-1.5 truncate text-[12px] font-semibold text-[color:var(--crm-muted-fg,#5b6478)]"
    >
      <!-- Figma .grab: circles at y=6/12/18 (not Lucide 5/12/19) -->
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
      <span class="truncate">{{ title }}</span>
      <span
        v-if="subtitle"
        class="shrink-0 font-medium text-[color:var(--crm-muted-fg,#5b6478)]"
      >
        · {{ subtitle }}
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

    <!-- Funnel — Figma: label 62px muted, bar h=20 r=4, value 34px, gap 6/8 -->
    <div v-if="kind === 'funnel'" class="mt-2.5 flex min-h-0 flex-1 flex-col gap-1.5">
      <div
        v-for="(step, i) in funnelSteps"
        :key="i"
        class="flex items-center gap-2 text-[11.5px]"
      >
        <span
          class="w-[62px] shrink-0 truncate text-[color:var(--crm-muted-fg,#5b6478)]"
          >{{ step.label }}</span
        >
        <div class="flex min-w-0 flex-1 justify-center">
          <div
            class="h-5"
            :style="{
              width: `${step.width}%`,
              background: step.color,
              borderRadius: '4px',
            }"
          />
        </div>
        <span
          class="w-[34px] shrink-0 text-right font-semibold tabular-nums text-[color:var(--crm-fg,#0b1324)]"
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

    <!-- Table — Figma .tbl (td h=44, pad 0 10px) + .st + .av2.sm -->
    <table
      v-else-if="kind === 'table'"
      class="report-tbl mt-1.5 w-full border-collapse"
    >
      <tbody>
        <tr v-for="(row, i) in tableRows" :key="i">
          <td>
            <span class="font-semibold">{{
              row.name || row.label || row[tableCols[0]]
            }}</span>
          </td>
          <td>
            <span
              v-if="row.status || row.stage || row[tableCols[1]]"
              class="report-st"
            >
              <i
                :style="{
                  background:
                    stageColor(row.status || row.stage || row[tableCols[1]]) ||
                    'var(--crm-faint, #8a94a6)',
                }"
              />
              {{ row.status || row.stage || row[tableCols[1]] }}
            </span>
          </td>
          <td class="num r">
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
          </td>
          <td>
            <span
              v-if="row.owner || row.deal_owner || row.initials"
              class="report-av2"
              >{{ rowInitials(row) }}</span
            >
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Line chart — Figma SVG is fixed 520×110, grid at 27/55/82 -->
    <div v-else-if="kind === 'line'" class="mt-3 min-h-0 flex-1">
      <svg
        v-if="lineSeries.length"
        width="520"
        height="110"
        viewBox="0 0 520 110"
        class="block overflow-visible"
      >
        <line
          v-for="g in lineGridYs"
          :key="g"
          x1="0"
          :y1="g"
          x2="520"
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
          :stroke-dasharray="series.dashed ? '4 4' : undefined"
          :points="series.points"
        />
      </svg>
      <div
        v-else
        class="flex h-full items-center justify-center text-[12px] text-[color:var(--crm-muted-fg,#5b6478)]"
      >
        {{ __('No data for this period') }}
      </div>
    </div>

    <!-- Bar chart — Figma .hb (v3 padding 18px + crm padding-top 8px) -->
    <div v-else-if="kind === 'bar'" class="report-hb min-h-0 flex-1">
      <template v-if="bars.length">
        <div v-for="(bar, i) in bars" :key="i" class="report-hb__b">
          <span class="report-hb__num">{{ bar.display }}</span>
          <i
            :style="{
              height: bar.heightCss,
              background: bar.color,
              minHeight: bar.value ? '4px' : '0',
            }"
          />
          <span class="report-hb__label">{{ bar.short }}</span>
        </div>
      </template>
      <div
        v-else
        class="flex h-full w-full items-center justify-center text-[12px] text-[color:var(--crm-muted-fg,#5b6478)]"
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
  dragging: { type: Boolean, default: false },
  selected: { type: Boolean, default: false },
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
  // Figma capture uses absolute px heights (incl. short bars like 32px).
  const heights = rows.map((r) =>
    r.height != null ? Number(r.height) : null,
  )
  const usePxHeights = heights.some((h) => h != null && h > 100)
  return rows.slice(0, 8).map((r, i) => {
    const n = Number(r.value) || 0
    const display =
      r.display != null
        ? String(r.display)
        : n >= 1000
          ? formatKpiValue(n, 'currency').replace('₹', '')
          : // Figma bar labels use one decimal (18.0, 22.2, …)
            Number(n).toFixed(1)
    const rawH = heights[i]
    const heightCss =
      rawH != null && usePxHeights
        ? `${rawH}px`
        : `${rawH != null ? rawH : (n / max) * 70 + (n ? 10 : 0)}%`
    return {
      label: r.label,
      value: r.value,
      heightCss,
      short: String(r.label || ''),
      display,
      color: r.color || stageColor(r.label) || chartColor(i),
    }
  })
})

/** Figma p-17 gridline Y positions inside the 520×110 SVG. */
const lineGridYs = computed(() => props.data?.grid_ys || [27, 55, 82])

const lineSeries = computed(() => {
  const labels = props.data?.labels || []
  const series = props.data?.series || []
  if (!series.length) return []

  // Prefer exact Figma polyline points when provided by the fixture.
  // Respect explicit `dashed` — do NOT force si>0 (This year is solid).
  if (series.every((s) => s.points)) {
    return series.map((s) => {
      const dashed = Boolean(s.dashed)
      return {
        name: s.name,
        dashed,
        color: s.color || (dashed ? 'var(--crm-c6)' : 'var(--crm-c1)'),
        points: String(s.points),
      }
    })
  }

  const allVals = series
    .flatMap((s) => (s.data || []).map(Number))
    .filter(Number.isFinite)
  const max = Math.max(...allVals, 1)
  const min = Math.min(...allVals, 0)
  const span = Math.max(max - min, 1)
  const n = Math.max(
    labels.length,
    ...series.map((s) => (s.data || []).length),
    1,
  )
  const w = 520
  const h = 110

  return series.map((s, si) => {
    const data = s.data || []
    const pts = data.map((v, i) => {
      const x = n <= 1 ? w / 2 : (i / (n - 1)) * w
      const y = h - ((Number(v) - min) / span) * h
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    const dashed = Boolean(s.dashed)
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

<style scoped>
/*
 * Figma cascade: v3.css .hb { padding: 10px 18px } then crm.css
 * .hb { padding-top: 8px } → computed padding 8px 18px 10px.
 */
.report-hb {
  /* v3 .hb { padding:10px 18px; border-top } + crm { padding-top:8px } */
  display: flex;
  align-items: flex-end;
  gap: 10px;
  height: 100%;
  min-height: 0;
  padding: 8px 18px 10px;
  border-top: 1px solid var(--crm-border, #e1e7ec);
  overflow: hidden;
  box-sizing: border-box;
}
.report-hb__b {
  flex: 1 1 0%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  gap: 4px;
  height: 100%;
  min-width: 0;
  font-size: 10.5px;
  color: var(--crm-muted-fg, #5b6478);
}
.report-hb__b i {
  display: block;
  width: 100%;
  border-radius: 4px 4px 0 0;
  flex: none;
}
.report-hb__num {
  /* Inherited from .hb .b { font-size:10.5px } in Figma; weight/color via inline .num */
  font-size: 10.5px;
  font-weight: 600;
  color: var(--crm-fg, #0b1324);
  font-variant-numeric: tabular-nums;
  line-height: 15.225px;
}
.report-hb__label {
  width: 100%;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.report-tbl td {
  height: 44px;
  padding: 0 10px;
  border-bottom: 1px solid var(--crm-border, #e1e7ec);
  font-size: 12.5px;
  white-space: nowrap;
}
.report-tbl tr:last-child td {
  border-bottom: 0;
}
.report-tbl td.r {
  text-align: right;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.report-st {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 22px;
  padding: 0 8px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 600;
  white-space: nowrap;
  background: var(--crm-neutral-soft, #eef1f6);
  color: var(--crm-fg, #0b1324);
}
.report-st i {
  width: 7px;
  height: 7px;
  border-radius: 2px;
  display: block;
  background: var(--crm-faint, #8a94a6);
}
.report-av2 {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--crm-primary-soft, #e4f2f6);
  color: var(--crm-primary, #0a7393);
  font-size: 9px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
