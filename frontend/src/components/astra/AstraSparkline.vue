<template>
  <svg
    v-if="points.length > 1"
    :viewBox="`0 0 ${width} ${height}`"
    class="h-8 w-full"
    preserveAspectRatio="none"
    aria-hidden="true"
  >
    <defs>
      <linearGradient :id="gradId" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="var(--astra-teal)" stop-opacity="0.28" />
        <stop offset="100%" stop-color="var(--astra-teal)" stop-opacity="0" />
      </linearGradient>
    </defs>
    <path :d="areaPath" :fill="`url(#${gradId})`" />
    <path
      :d="linePath"
      fill="none"
      stroke="var(--astra-teal)"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** Real numeric series only — empty array hides the chart. */
  values: { type: Array, default: () => [] },
  width: { type: Number, default: 120 },
  height: { type: Number, default: 36 },
})

const gradId = `astra-spark-${Math.random().toString(36).slice(2, 9)}`

const points = computed(() =>
  (props.values || []).map(Number).filter((n) => Number.isFinite(n)),
)

const coords = computed(() => {
  const vals = points.value
  if (vals.length < 2) return []
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const span = max - min || 1
  return vals.map((v, i) => {
    const x = (i / (vals.length - 1)) * props.width
    const y = props.height - ((v - min) / span) * (props.height - 4) - 2
    return [x, y]
  })
})

const linePath = computed(() =>
  coords.value.map((p, i) => `${i ? 'L' : 'M'}${p[0]},${p[1]}`).join(' '),
)

const areaPath = computed(() => {
  if (!coords.value.length) return ''
  const first = coords.value[0]
  const last = coords.value[coords.value.length - 1]
  return `${linePath.value} L${last[0]},${props.height} L${first[0]},${props.height} Z`
})
</script>
