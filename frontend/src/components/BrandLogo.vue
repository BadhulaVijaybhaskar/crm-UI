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
    :src="ASTRA_LOGO"
    alt="Astra CRM"
    class="h-full w-auto max-w-full object-contain"
  />
</template>

<script setup>
import { ASTRA_LOGO } from '@/assets/brand'

const brand = defineModel({ type: Object, default: () => ({}) })
</script>
