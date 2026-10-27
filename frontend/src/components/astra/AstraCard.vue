<template>
  <section class="astra-card" :class="{ 'astra-card--flush': flush }" v-bind="$attrs">
    <header
      v-if="title || $slots.title || $slots.actions"
      class="mb-3 flex items-start justify-between gap-3"
    >
      <div class="min-w-0">
        <slot name="title">
          <h3 v-if="title" class="astra-card__title">{{ title }}</h3>
        </slot>
        <p v-if="subtitle" class="astra-muted mt-0.5 text-xs">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="shrink-0">
        <slot name="actions" />
      </div>
    </header>
    <slot />
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  flush: { type: Boolean, default: false },
})
</script>
