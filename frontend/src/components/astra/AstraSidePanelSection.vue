<template>
  <section class="border-b border-crm-border last:border-b-0">
    <header class="flex items-center justify-between gap-2 px-4 pb-1 pt-3">
      <h3 class="m-0 text-xs font-bold text-crm-fg">{{ title }}</h3>
      <div v-if="$slots.action" class="shrink-0">
        <slot name="action" />
      </div>
    </header>
    <dl v-if="entries.length" class="grid grid-cols-[118px_1fr] gap-x-2.5 gap-y-2 px-4 pb-3.5 pt-2">
      <template v-for="entry in entries" :key="entry.label">
        <dt class="text-crm-label text-crm-muted-fg">{{ entry.label }}</dt>
        <dd class="m-0 truncate text-crm-label font-medium text-crm-fg">
          <slot :name="`value-${entry.key || entry.label}`" :entry="entry">
            {{ entry.value }}
          </slot>
        </dd>
      </template>
    </dl>
    <div v-else class="px-4 pb-3.5">
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  entries: { type: Array, default: () => [] },
})
</script>
