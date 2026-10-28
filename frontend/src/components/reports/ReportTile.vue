<template>
  <div
    class="report-tile group relative flex h-full w-full flex-col overflow-hidden rounded-[10px] border bg-[color:var(--crm-card,#fff)] p-3 text-[color:var(--crm-fg,#0f172a)]"
    :class="[
      editing
        ? 'border-[color:var(--crm-border-strong,#94a3b8)]'
        : 'border-[color:var(--crm-border,#e2e8f0)]',
      selected ? 'shadow-[0_0_0_2px_var(--crm-primary,#0a7393)]' : '',
    ]"
    @click="$emit('select')"
  >
    <div
      v-if="editing"
      class="absolute left-2 top-2 z-10 cursor-grab text-[color:var(--crm-faint,#94a3b8)] opacity-70"
      aria-hidden="true"
    >
      <span class="lucide-grip-vertical size-3.5" />
    </div>

    <div
      v-if="editing"
      class="absolute right-2 top-2 z-10 flex items-center gap-0.5 rounded-md bg-[color:var(--crm-card,#fff)] opacity-0 shadow-sm ring-1 ring-[color:var(--crm-border,#e2e8f0)] group-hover:opacity-100"
    >
      <button
        type="button"
        class="rounded px-2 py-1 text-[11px] hover:bg-[color:var(--crm-muted,#f1f5f9)]"
        @click.stop="$emit('edit')"
      >
        {{ __('Edit') }}
      </button>
      <button
        type="button"
        class="rounded px-2 py-1 text-[11px] hover:bg-[color:var(--crm-muted,#f1f5f9)]"
        @click.stop="$emit('duplicate')"
      >
        {{ __('Duplicate') }}
      </button>
      <button
        type="button"
        class="rounded px-2 py-1 text-[11px] text-[color:var(--crm-danger,#dc2626)] hover:bg-[color:var(--crm-danger-soft,#fee2e2)]"
        @click.stop="$emit('remove')"
      >
        {{ __('Delete') }}
      </button>
      <span
        class="px-1.5 text-[10px] text-[color:var(--crm-muted-fg,#64748b)]"
      >
        {{ sizeLabel }}
      </span>
    </div>

    <div class="min-h-0 flex-1" :class="editing ? 'pointer-events-none' : ''">
      <ReportKpiTile
        v-if="tile.type === 'kpi'"
        :title="tile.title"
        :data="tile.data"
      />
      <ReportChartTile
        v-else
        :title="tile.title"
        :tile-type="tile.type"
        :data="tile.data"
      />
    </div>

    <div
      v-if="editing"
      class="pointer-events-none absolute bottom-[3px] right-[3px] size-3 rounded-br-[3px] border-b-2 border-r-2 border-[color:var(--crm-primary,#0a7393)]"
      aria-hidden="true"
    />
  </div>
</template>

<script setup>
import ReportChartTile from './ReportChartTile.vue'
import ReportKpiTile from './ReportKpiTile.vue'
import { computed } from 'vue'

const props = defineProps({
  tile: { type: Object, required: true },
  editing: { type: Boolean, default: false },
  selected: { type: Boolean, default: false },
})

defineEmits(['select', 'edit', 'duplicate', 'remove'])

const sizeLabel = computed(() => {
  const l = props.tile.layout || {}
  return `${l.w || 0} × ${l.h || 0}`
})
</script>
