<template>
  <button
    type="button"
    role="checkbox"
    class="astra-checkbox inline-flex size-[15px] shrink-0 items-center justify-center rounded-crm-mini border-[1.5px] border-crm-border-strong bg-crm-card focus-visible:outline-none focus-visible:shadow-crm-focus"
    :class="{
      'border-crm-primary bg-crm-primary text-crm-primary-fg': checked || indeterminate,
      'opacity-55': disabled,
    }"
    :aria-checked="indeterminate ? 'mixed' : checked ? 'true' : 'false'"
    :aria-label="ariaLabel || undefined"
    :disabled="disabled"
    @click.stop="onToggle"
  >
    <svg
      v-if="indeterminate"
      class="size-2.5"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="3.5"
      stroke-linecap="round"
      aria-hidden="true"
    >
      <path d="M5 12h14" />
    </svg>
    <svg
      v-else-if="checked"
      class="size-2.5"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="3.5"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <path d="M20 6 9 17l-5-5" />
    </svg>
  </button>
</template>

<script setup>
const props = defineProps({
  checked: { type: Boolean, default: false },
  indeterminate: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  ariaLabel: { type: String, default: '' },
})

const emit = defineEmits(['change'])

function onToggle() {
  if (props.disabled) return
  emit('change', !props.checked)
}
</script>
