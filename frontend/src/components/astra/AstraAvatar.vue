<template>
  <span
    class="inline-flex shrink-0 items-center justify-center rounded-full font-semibold text-white"
    :class="sizeClass"
    :style="{ backgroundColor: tone }"
    :aria-hidden="ariaLabel ? undefined : true"
    :aria-label="ariaLabel || undefined"
    role="img"
  >
    {{ letters }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { avatarTone, initialsFrom } from '@/components/astra/format'

const props = defineProps({
  name: { type: String, default: '' },
  seed: { type: String, default: '' },
  size: { type: String, default: 'md' },
  ariaLabel: { type: String, default: '' },
})

const letters = computed(() => initialsFrom(props.name || props.seed))
const tone = computed(() => avatarTone(props.seed || props.name))
const sizeClass = computed(() => {
  if (props.size === 'lg') return 'size-14 text-lg'
  if (props.size === 'sm') return 'size-8 text-xs'
  return 'size-9 text-xs'
})
</script>
