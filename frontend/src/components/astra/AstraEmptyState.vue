<template>
  <div class="flex flex-col items-center justify-center gap-2 px-6 py-12 text-center" role="status">
    <div
      v-if="$slots.icon"
      class="mb-1 grid size-11 place-items-center rounded-crm-panel bg-crm-neutral-soft text-crm-faint"
    >
      <slot name="icon" />
    </div>
    <p class="m-0 text-crm-dialog font-semibold text-crm-fg">{{ title }}</p>
    <p v-if="body" class="m-0 max-w-[420px] text-crm-body text-crm-muted-fg">
      {{ body }}
    </p>
    <div v-if="$slots.default" class="mt-3">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  body: { type: String, default: '' },
})
</script>
