<template>
  <label class="flex min-w-0 flex-col gap-[5px]" :class="{ 'opacity-60': disabled }">
    <span v-if="label" class="text-xs font-semibold text-crm-fg">{{ label }}</span>
    <span
      class="flex h-crm-input items-center gap-2 rounded-crm-control-sm bg-crm-card px-2.5 shadow-[inset_0_0_0_1px_var(--crm-border-strong)] focus-within:shadow-crm-input-focus focus-within:shadow-[inset_0_0_0_1px_var(--crm-primary),var(--crm-input-focus)]"
      :class="{ 'shadow-[inset_0_0_0_1px_var(--crm-danger)]': invalid }"
    >
      <span v-if="$slots.prefix" class="inline-flex text-crm-faint">
        <slot name="prefix" />
      </span>
      <input
        class="min-w-0 flex-1 border-0 bg-transparent text-crm-label text-crm-fg outline-none placeholder:text-crm-faint"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :aria-invalid="invalid || undefined"
        v-bind="$attrs"
        @input="$emit('update:modelValue', $event.target.value)"
      />
      <span v-if="$slots.suffix" class="inline-flex text-crm-faint">
        <slot name="suffix" />
      </span>
    </span>
    <span v-if="hint" class="text-crm-micro text-crm-faint">{{ hint }}</span>
  </label>
</template>

<script setup>
defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  hint: { type: String, default: '' },
  type: { type: String, default: 'text' },
  disabled: { type: Boolean, default: false },
  invalid: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])
</script>
