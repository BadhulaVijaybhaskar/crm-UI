<template>
  <input
    type="checkbox"
    class="astra-checkbox size-4 shrink-0 rounded-crm-mini border border-crm-border-strong bg-crm-card accent-crm-primary focus-visible:outline-none focus-visible:shadow-crm-focus"
    :checked="checked"
    :indeterminate.prop="indeterminate"
    :disabled="disabled"
    :aria-label="ariaLabel || undefined"
    @change="$emit('change', $event.target.checked, $event)"
    @click.stop
  />
</template>

<script setup>
defineProps({
  checked: { type: Boolean, default: false },
  indeterminate: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  ariaLabel: { type: String, default: '' },
})

defineEmits(['change'])
</script>
