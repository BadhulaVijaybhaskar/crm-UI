<template>
  <div
    v-if="count > 0"
    class="pointer-events-none fixed bottom-[22px] left-crm-nav right-0 z-40 flex justify-center px-4"
    role="toolbar"
    :aria-label="__('Bulk actions')"
  >
    <div
      class="pointer-events-auto inline-flex h-[42px] translate-x-px items-center gap-2 rounded-crm-rail bg-crm-bulk-bg px-3 text-crm-label text-crm-bulk-fg shadow-crm-bulk"
    >
      <!-- crm.css .bulk .bb is font-weight 600; PNG tints count with primary -->
      <span
        class="inline-flex h-7 items-center gap-1.5 rounded-crm-chip px-2.5 font-semibold text-crm-primary"
      >
        {{ __('{0} selected', [count]) }}
      </span>
      <template v-for="action in actions" :key="action.label">
        <button
          type="button"
          class="inline-flex h-7 items-center gap-1.5 rounded-crm-chip border-l border-[rgba(127,140,150,0.35)] px-2.5 font-semibold text-crm-bulk-fg hover:bg-white/10"
          @click="action.onClick?.()"
        >
          <svg
            v-if="action.icon === 'assign'"
            class="size-3.5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <circle cx="12" cy="8" r="4" />
            <path d="M4 21a8 8 0 0 1 16 0" />
          </svg>
          <svg
            v-else-if="action.icon === 'status'"
            class="size-3.5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path
              d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z"
            />
            <circle cx="7.5" cy="7.5" r="1.2" />
          </svg>
          <svg
            v-else-if="action.icon === 'temperature'"
            class="size-3.5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path
              d="M4 22V4s1-1 4-1 5 2 8 2 4-1 4-1v11s-1 1-4 1-5-2-8-2-4 1-4 1"
            />
          </svg>
          {{ action.label }}
        </button>
      </template>
      <button
        type="button"
        class="inline-flex h-7 items-center gap-1.5 rounded-crm-chip border-l border-[rgba(127,140,150,0.35)] px-2.5 font-medium text-crm-bulk-fg opacity-55 hover:bg-white/10"
        @click="$emit('clear')"
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
          <path d="M18 6 6 18M6 6l12 12" />
        </svg>
        {{ __('Clear') }}
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  count: { type: Number, default: 0 },
  actions: { type: Array, default: () => [] },
})

defineEmits(['clear'])
</script>
