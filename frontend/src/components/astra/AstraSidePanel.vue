<template>
  <aside
    class="shrink-0 overflow-y-auto bg-crm-card"
    :class="
      stacked
        ? 'w-full border-t border-crm-border xl:w-crm-side xl:border-l xl:border-t-0'
        : 'w-crm-side border-l border-crm-border'
    "
  >
    <slot />
  </aside>
</template>

<script setup>
defineProps({
  stacked: { type: Boolean, default: false },
})
</script>
