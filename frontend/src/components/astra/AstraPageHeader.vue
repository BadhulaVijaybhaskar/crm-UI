<template>
  <header class="flex items-center justify-between gap-3 px-crm-page-x pb-3.5 pt-[18px]">
    <!-- PNG title block sits ~1px left of default packing -->
    <div class="min-w-0 -translate-x-px">
      <p
        v-if="eyebrow"
        class="mb-1 text-crm-caps font-bold uppercase tracking-crm-caps text-crm-faint"
      >
        {{ eyebrow }}
      </p>
      <h1
        class="m-0 text-[20px] font-semibold leading-[29px] tracking-crm-tight text-crm-fg"
      >
        {{ title }}
      </h1>
      <p
        v-if="description"
        class="m-0 -translate-y-px text-[13px] leading-[18.85px] text-crm-muted-fg"
      >
        {{ description }}
      </p>
    </div>
    <div v-if="$slots.actions || $slots.default" class="flex flex-wrap items-center justify-end gap-2">
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
