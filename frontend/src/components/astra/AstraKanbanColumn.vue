<template>
  <section
    class="flex w-crm-kanban-col shrink-0 flex-col overflow-hidden rounded-crm-panel border border-crm-border bg-crm-muted"
  >
    <header class="border-b border-crm-border px-3 pb-2 pt-2.5">
      <div class="flex items-center justify-between gap-2">
        <slot name="title">
          <AstraBadge v-if="title" :label="title" :tone="tone" />
        </slot>
        <span class="text-xs text-crm-muted-fg">{{ count }}</span>
      </div>
      <p v-if="subtitle" class="mt-1 text-crm-meta text-crm-muted-fg">
        {{ subtitle }}
      </p>
    </header>
    <div class="flex flex-1 flex-col gap-2 overflow-y-auto p-2">
      <slot />
    </div>
  </section>
</template>

<script setup>
import AstraBadge from '@/components/astra/AstraBadge.vue'

defineProps({
  title: { type: String, default: '' },
  tone: { type: String, default: 'mute' },
  count: { type: [Number, String], default: 0 },
  subtitle: { type: String, default: '' },
})
</script>
