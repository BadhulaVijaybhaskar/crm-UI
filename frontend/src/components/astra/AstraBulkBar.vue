<template>
  <div
    v-if="count > 0"
    class="pointer-events-none fixed inset-x-0 bottom-[22px] z-40 flex justify-center px-4"
    role="toolbar"
    :aria-label="__('Bulk actions')"
  >
    <div
      class="pointer-events-auto inline-flex h-[42px] items-center gap-0 rounded-crm-rail bg-crm-bulk-bg px-3 text-crm-label text-crm-bulk-fg shadow-crm-bulk"
    >
      <span class="pr-3 font-semibold">
        {{ __('{0} selected', [count]) }}
      </span>
      <template v-for="(action, index) in actions" :key="action.label">
        <span
          v-if="index"
          class="mx-0.5 h-4 w-px bg-crm-bulk-fg/20"
          aria-hidden="true"
        />
        <button
          type="button"
          class="inline-flex h-7 items-center rounded-crm-control-sm px-2.5 font-semibold text-crm-bulk-fg hover:bg-white/10"
          @click="action.onClick?.()"
        >
          {{ action.label }}
        </button>
      </template>
      <span class="mx-0.5 h-4 w-px bg-crm-bulk-fg/20" aria-hidden="true" />
      <button
        type="button"
        class="inline-flex h-7 items-center rounded-crm-control-sm px-2.5 font-semibold text-crm-bulk-fg hover:bg-white/10"
        @click="$emit('clear')"
      >
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
