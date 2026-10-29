<template>
  <span
    class="inline-flex shrink-0 items-center justify-center overflow-hidden"
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
  if (props.tone === 'company' || (props.squared && props.tone !== 'primary')) {
    // crm.css .av2.co — neutral chip + muted initials (list company cells)
    return {
      backgroundColor: 'var(--crm-neutral-soft)',
      color: 'var(--crm-muted-fg)',
    }
  }
  if (props.squared) {
    // Figma .bigav — primary-soft chip + primary initials (not muted ink)
    return {
      backgroundColor: 'var(--crm-primary-soft)',
      color: 'var(--crm-primary)',
    }
  }
  return { backgroundColor: soft.value, color: tone.value }
})

const sizeClass = computed(() => {
  // List .av2.co is 6px; record .bigav is 10px
  const radius =
    props.tone === 'company'
      ? 'rounded-[6px]'
      : props.squared
        ? 'rounded-[10px]'
        : 'rounded-full'
  if (props.size === 'xs') return `${radius} size-5 text-[9px] font-semibold`
  // PNG av2 initials ink is lighter than Inter 700 in Chromium — match PNG
  // (approved) with 600; HTML .av2 {700} disagrees with the capture.
  if (props.size === 'sm')
    return `${radius} size-[20px] text-[9px] font-semibold`
  // crm.css / app.css .nav .foot .av — 30×30, font 11px / 600
  if (props.size === 'foot')
    return `${radius} size-[30px] text-[11px] font-semibold`
  if (props.size === 'lg')
    return `${radius} size-[42px] text-[15px] font-semibold`
  if (props.size === 'xl') return `${radius} size-14 text-base font-semibold`
  // .av2 26×26 / 10.5px — PNG-approved weight 600 (not HTML 700)
  return `${radius} size-[26px] text-[10.5px] font-semibold`
})
</script>
