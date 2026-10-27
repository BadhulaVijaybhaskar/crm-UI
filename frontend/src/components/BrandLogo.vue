<template>
  <div v-if="brand?.logo" class="flex h-full items-center">
    <img
      :src="brand.logo"
      :alt="brand.name || 'Astra CRM'"
      class="h-full w-auto max-w-full object-contain"
    />
  </div>
  <img
    v-else
    src="/assets/crm/images/astra-crm-logo.png"
    alt="Astra CRM"
    class="h-full w-auto max-w-full object-contain"
  />
</template>

<script setup>
const brand = defineModel({ type: Object, default: () => ({}) })
</script>
