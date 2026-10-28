<template>
  <section
    class="flex w-crm-kanban-col shrink-0 flex-col overflow-hidden rounded-crm-panel border border-crm-border bg-crm-muted"
    :class="{ 'h-full min-h-0': fillHeight }"
  >
    <header class="shrink-0 border-b border-crm-border px-3 pb-2 pt-2.5">
      <div class="flex items-center justify-between gap-2">
        <slot name="title">
          <div v-if="title" class="flex min-w-0 items-center gap-2">
            <span
              v-if="color"
              class="size-2 shrink-0 rounded-full"
              :style="{ backgroundColor: color }"
              aria-hidden="true"
            />
            <span class="truncate text-crm-label font-semibold text-crm-fg">
              {{ title }}
            </span>
          </div>
          <AstraBadge v-else-if="badgeTitle" :label="badgeTitle" :tone="tone" />
        </slot>
        <span class="shrink-0 text-xs text-crm-muted-fg">{{ count }}</span>
      </div>
      <p v-if="subtitle" class="mt-1 text-crm-meta text-crm-muted-fg">
        {{ subtitle }}
      </p>
    </header>
    <div class="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto p-2">
      <slot />
    </div>
  </section>
</template>

<script setup>
import AstraBadge from '@/components/astra/AstraBadge.vue'

defineProps({
  title: { type: String, default: '' },
  /** Legacy filled-pill title; prefer `title` + `color` for stage headers. */
  badgeTitle: { type: String, default: '' },
  tone: { type: String, default: 'mute' },
  /** CSS colour for the stage dot (e.g. var(--crm-c6)). */
  color: { type: String, default: '' },
  count: { type: [Number, String], default: 0 },
  subtitle: { type: String, default: '' },
  fillHeight: { type: Boolean, default: false },
})
</script>
