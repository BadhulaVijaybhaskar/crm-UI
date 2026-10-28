<template>
  <div
    class="flex items-center justify-between gap-2 px-crm-page-x py-[10px]"
  >
    <div class="flex flex-wrap items-center gap-2">
      <slot name="filters">
        <button
          v-for="filter in filters"
          :key="filter.id || filter.label"
          type="button"
          class="inline-flex h-crm-control-sm items-center gap-1 rounded-crm-control-sm bg-crm-card pl-2.5 pr-2 text-crm-label shadow-[inset_0_0_0_1px_var(--crm-border-strong)]"
          :class="{
            'bg-crm-primary-soft shadow-[inset_0_0_0_1px_var(--crm-primary)]':
              filter.active,
          }"
          @click="$emit('remove-filter', filter)"
        >
          <span class="text-crm-muted-fg">{{ filter.key || filter.label }}</span>
          <span v-if="filter.value" class="font-semibold text-crm-fg">
            {{ filter.value }}
          </span>
          <span class="text-crm-faint" aria-hidden="true">×</span>
        </button>
        <button
          v-if="showAdd"
          type="button"
          class="inline-flex h-crm-control-sm items-center rounded-crm-control-sm px-2.5 text-crm-label font-medium text-crm-muted-fg shadow-[inset_0_0_0_1px_var(--crm-border-strong)]"
          @click="$emit('add-filter')"
        >
          + {{ addLabel }}
        </button>
      </slot>
    </div>
    <div v-if="$slots.actions || sortLabel" class="flex flex-wrap items-center gap-2">
      <button
        v-if="sortLabel"
        type="button"
        class="inline-flex h-crm-control-sm items-center gap-1.5 rounded-crm-control-sm px-2.5 text-crm-label font-medium text-crm-muted-fg"
        @click="$emit('sort')"
      >
        <svg
          class="size-3.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          aria-hidden="true"
        >
          <path d="M7 4v16M3 16l4 4 4-4M17 20V4M13 8l4-4 4 4" />
        </svg>
        {{ sortLabel }}
      </button>
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  filters: { type: Array, default: () => [] },
  sortLabel: { type: String, default: '' },
  addLabel: { type: String, default: 'Filter' },
  showAdd: { type: Boolean, default: true },
})

defineEmits(['add-filter', 'remove-filter', 'sort'])
</script>
