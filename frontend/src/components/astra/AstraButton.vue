<template>
  <button
    type="button"
    class="inline-flex items-center justify-center gap-1.5 font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-55"
    :class="[variantClass, sizeClass, { 'w-full': block }]"
    :disabled="disabled || loading"
    v-bind="$attrs"
  >
    <span
      v-if="loading"
      class="size-3.5 animate-spin rounded-full border-2 border-current border-r-transparent"
      aria-hidden="true"
    />
    <slot name="prefix" />
    <span v-if="!iconOnly"><slot>{{ label }}</slot></span>
    <slot name="suffix" />
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, default: '' },
  variant: { type: String, default: 'secondary' },
  size: { type: String, default: 'md' },
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  block: { type: Boolean, default: false },
  iconOnly: { type: Boolean, default: false },
})

const sizeClass = computed(() => {
  if (props.size === 'sm') {
    return props.iconOnly
      ? 'size-crm-control-sm rounded-crm-control-sm text-crm-label'
      : 'h-crm-control-sm rounded-crm-control-sm px-[10px] text-crm-label'
  }
  return props.iconOnly
    ? 'size-crm-control rounded-crm-control text-crm-body'
    : 'h-crm-control rounded-crm-control px-[13px] text-crm-body'
})

const variantClass = computed(() => {
  const map = {
    primary: 'bg-crm-primary text-crm-primary-fg hover:bg-crm-primary-hover',
    secondary:
      'bg-crm-card text-crm-fg shadow-[inset_0_0_0_1px_var(--crm-border-strong)] hover:bg-crm-muted',
    ghost: 'bg-transparent text-crm-muted-fg hover:bg-crm-muted hover:text-crm-fg',
    positive: 'bg-crm-success text-white hover:brightness-105',
    negative: 'bg-crm-danger text-white hover:brightness-105',
  }
  return map[props.variant] || map.secondary
})
</script>
