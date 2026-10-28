<template>
  <span
    class="inline-flex shrink-0 items-center justify-center overflow-hidden font-bold text-crm-primary"
    :class="sizeClass"
    :style="src ? undefined : { backgroundColor: soft, color: tone }"
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
  ariaLabel: { type: String, default: '' },
})

const letters = computed(() => initialsFrom(props.name || props.seed))
const tone = computed(() => avatarTone(props.seed || props.name))
const soft = computed(() => 'var(--crm-primary-soft)')

const sizeClass = computed(() => {
  const radius = props.squared ? 'rounded-crm-panel' : 'rounded-full'
  if (props.size === 'xs') return `${radius} size-5 text-[9px]`
  if (props.size === 'sm') return `${radius} size-[20px] text-[9px]`
  if (props.size === 'lg') return `${radius} size-[42px] text-[15px]`
  if (props.size === 'xl') return `${radius} size-14 text-base`
  return `${radius} size-[26px] text-[10.5px]`
})
</script>
