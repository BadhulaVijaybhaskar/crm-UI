<template>
  <span
    class="inline-flex h-crm-chip items-center gap-1.5 whitespace-nowrap rounded-crm-chip px-2 text-crm-meta font-semibold"
    :class="toneClass"
  >
    <span
      v-if="dot"
      class="size-1.5 shrink-0 rounded-full bg-current"
      aria-hidden="true"
    />
    <slot>{{ label }}</slot>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, default: '' },
  tone: { type: String, default: 'mute' },
  dot: { type: Boolean, default: false },
})

const toneClass = computed(() => {
  const map = {
    ok: 'bg-crm-success-soft text-crm-success',
    warn: 'bg-crm-warning-soft text-crm-warning',
    bad: 'bg-crm-danger-soft text-crm-danger',
    info: 'bg-crm-primary-soft text-crm-primary',
    blue: 'bg-crm-blue-soft text-crm-blue',
    teal: 'bg-crm-teal-soft text-crm-teal',
    mute: 'bg-crm-neutral-soft text-crm-muted-fg',
    primary: 'bg-crm-primary-soft text-crm-primary',
    success: 'bg-crm-success-soft text-crm-success',
    warning: 'bg-crm-warning-soft text-crm-warning',
    danger: 'bg-crm-danger-soft text-crm-danger',
    off: 'bg-transparent text-crm-faint shadow-[inset_0_0_0_1px_var(--crm-border-strong)] [border-style:dashed]',
  }
  return map[props.tone] || map.mute
})
</script>
