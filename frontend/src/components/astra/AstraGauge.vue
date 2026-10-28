<template>
  <div class="flex flex-col items-center justify-center gap-2 py-1">
    <svg
      viewBox="0 0 120 72"
      class="h-24 w-40"
      role="img"
      :aria-label="ariaLabel"
    >
      <path
        d="M10 62 A50 50 0 0 1 110 62"
        fill="none"
        stroke="var(--astra-border)"
        stroke-width="10"
        stroke-linecap="round"
      />
      <path
        d="M10 62 A50 50 0 0 1 110 62"
        fill="none"
        stroke="var(--astra-primary)"
        stroke-width="10"
        stroke-linecap="round"
        :stroke-dasharray="track"
        :stroke-dashoffset="offset"
      />
      <text
        x="60"
        y="54"
        text-anchor="middle"
        class="fill-[var(--astra-text)] text-[1.35rem] font-bold"
        style="font-variant-numeric: tabular-nums"
      >
        {{ displayPercent }}
      </text>
    </svg>
    <p v-if="caption" class="astra-muted text-center text-xs">{{ caption }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** 0–100 progress. Caller must only pass when a real target exists. */
  percent: { type: Number, required: true },
  caption: { type: String, default: '' },
  ariaLabel: { type: String, default: 'Target progress' },
})

const clamped = computed(() =>
  Math.max(0, Math.min(100, Number(props.percent) || 0)),
)
const displayPercent = computed(() => `${Math.round(clamped.value)}%`)
const track = 157 // approx arc length for r=50 semicircle
const offset = computed(() => track - (track * clamped.value) / 100)
</script>
