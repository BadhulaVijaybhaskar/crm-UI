<template>
  <span
    class="inline-flex shrink-0 items-center justify-center overflow-hidden font-semibold"
    :class="[
      sizeClass,
      !src && !navFoot && !squared && 'text-crm-primary',
    ]"
    :style="src ? undefined : chipStyle"
    :aria-hidden="ariaLabel ? undefined : true"
    :aria-label="ariaLabel || undefined"
    role="img"
  >
    <img v-if="src" :src="src" alt="" class="size-full object-cover" />
    <template v-else>{{ letters }}</template>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { avatarTone, initialsFrom } from '@/components/astra/format'

const props = defineProps({
  name: { type: String, default: '' },
  seed: { type: String, default: '' },
  src: { type: String, default: '' },
  size: { type: String, default: 'md' },
  squared: { type: Boolean, default: false },
  /** `primary` matches crm.css .av2; `auto` hashes seed across palette. */
  tone: { type: String, default: 'primary' },
  /** app.css .nav .foot .av — ink chip on dark nav */
  navFoot: { type: Boolean, default: false },
  ariaLabel: { type: String, default: '' },
})

const letters = computed(() => initialsFrom(props.name || props.seed))
/** crm.css .av2 always uses primary; hashed tones are opt-in via `tone="auto"`. */
const tone = computed(() => {
  if (props.tone === 'auto') return avatarTone(props.seed || props.name)
  return 'var(--crm-primary)'
})
const soft = computed(() =>
  props.squared ? 'var(--crm-neutral-soft)' : 'var(--crm-primary-soft)',
)

const chipStyle = computed(() => {
  if (props.navFoot) {
    // Exact capture values from app.css .nav .foot .av
    return { backgroundColor: '#16264A', color: '#C9D3E6' }
  }
  if (props.squared) {
    return { backgroundColor: soft.value, color: 'var(--crm-muted-fg)' }
  }
  return { backgroundColor: soft.value, color: tone.value }
})

const sizeClass = computed(() => {
  const radius = props.squared ? 'rounded-crm-panel' : 'rounded-full'
  if (props.size === 'xs') return `${radius} size-5 text-[9px]`
  if (props.size === 'sm') return `${radius} size-[20px] text-[9px]`
  // crm.css / app.css .nav .foot .av — 30×30, font 11px / 600
  if (props.size === 'foot') return `${radius} size-[30px] text-[11px] font-semibold`
  if (props.size === 'lg') return `${radius} size-[42px] text-[15px]`
  if (props.size === 'xl') return `${radius} size-14 text-base`
  // crm.css .av2 — 26×26, 10.5px; 600 matches available Inter cut / Figma AA better than 700
  return `${radius} size-[26px] text-[10.5px] font-semibold`
})
</script>
