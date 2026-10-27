<template>
  <div class="astra-empty" role="status">
    <p class="astra-empty__title">{{ title }}</p>
    <p v-if="body" class="astra-empty__body">{{ body }}</p>
    <div v-if="$slots.default" class="mt-2">
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
