<template>
  <div
    class="flex items-center justify-between gap-2 px-crm-page-x py-[10px]"
  >
    <div class="flex translate-x-px flex-nowrap items-center gap-2">
      <slot name="filters">
        <button
          v-for="filter in filters"
          :key="filter.id || filter.label"
          type="button"
          class="inline-flex h-crm-control-sm items-center gap-1.5 rounded-crm-control-sm bg-crm-card pl-2.5 pr-2 text-crm-label shadow-[inset_0_0_0_1px_var(--crm-border-strong)]"
          :class="{
            'bg-crm-primary-soft shadow-[inset_0_0_0_1px_var(--crm-primary)]':
              filter.active,
          }"
          @click="$emit('remove-filter', filter)"
        >
          <span class="leading-none text-crm-muted-fg">{{
            filter.key || filter.label
          }}</span>
          <span
            v-if="filter.value"
            class="leading-none font-semibold text-crm-primary"
          >
            {{ filter.value }}
          </span>
          <!-- PNG paints the dismiss X in primary on .on chips (HTML faint disagrees). -->
          <svg
            class="size-3.5"
            :class="filter.active ? 'text-crm-primary' : 'text-crm-faint'"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            aria-hidden="true"
          >
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>
        <button
          v-if="showAdd"
          type="button"
          class="inline-flex h-crm-control-sm items-center gap-1.5 rounded-crm-control-sm bg-crm-card pl-2.5 pr-2 text-crm-label text-crm-fg shadow-[inset_0_0_0_1px_var(--crm-border-strong)]"
          @click="$emit('add-filter')"
        >
          <svg
            class="size-3.5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            aria-hidden="true"
          >
            <path d="M12 5v14M5 12h14" />
          </svg>
          {{ addLabel }}
        </button>
      </slot>
    </div>
    <!-- app.css .btn gap:7px; font-weight:600. −2.5 (10px) — −3 overshot actions. -->
    <div
      v-if="$slots.actions || sortLabel"
      class="-translate-x-2.5 flex flex-nowrap items-center gap-[7px]"
    >
      <button
        v-if="sortLabel"
        type="button"
        class="inline-flex h-crm-control-sm items-center gap-[7px] rounded-crm-control-sm px-2.5 text-crm-label font-semibold text-crm-muted-fg"
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
