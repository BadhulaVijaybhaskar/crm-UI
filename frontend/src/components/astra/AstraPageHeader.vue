<template>
  <header class="flex items-center justify-between gap-3 px-crm-page-x pb-3.5 pt-[18px]">
    <div class="min-w-0">
      <p
        v-if="eyebrow"
        class="mb-1 text-crm-caps font-bold uppercase tracking-crm-caps text-crm-faint"
      >
        {{ eyebrow }}
      </p>
      <h1
        class="m-0 text-crm-page font-semibold leading-[1.45] tracking-crm-tight text-crm-fg"
      >
        {{ title }}
      </h1>
      <p
        v-if="description"
        class="mt-0 text-crm-body leading-[1.45] text-crm-muted-fg"
      >
        {{ description }}
      </p>
    </div>
    <div
      v-if="$slots.actions || $slots.default"
      class="flex flex-wrap items-center justify-end gap-3"
    >
      <slot name="actions" />
      <slot />
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  eyebrow: { type: String, default: '' },
})
</script>
