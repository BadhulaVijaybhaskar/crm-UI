<template>
  <div
    class="report-tile group relative flex h-full w-full flex-col rounded-[10px] border bg-[color:var(--crm-card,#fff)] px-3.5 py-3 text-[color:var(--crm-fg,#0b1324)]"
    :class="[
      editing && !dragging
        ? 'overflow-visible border-[color:var(--crm-border-strong,#d0d9e0)]'
        : editing && dragging
          ? 'report-tile--dragging overflow-visible border-[color:var(--crm-border,#e1e7ec)]'
          : 'overflow-hidden border-[color:var(--crm-border,#e1e7ec)]',
      selected && !dragging
        ? 'shadow-[0_0_0_2px_var(--crm-primary,#0a7393)]'
        : '',
    ]"
    @click="$emit('select')"
  >
    <div
      v-if="editing && selected"
      class="absolute right-2 top-1.5 z-[2] flex items-center gap-0.5 rounded-lg border border-[color:var(--crm-border,#e1e7ec)] bg-[color:var(--crm-card,#fff)] p-[3px] text-[12.5px] shadow-[0_6px_16px_rgba(4,20,27,0.12)]"
    >
      <button
        type="button"
        class="inline-flex h-7 items-center gap-[7px] rounded-[7px] border border-transparent bg-transparent px-2.5 font-semibold text-[color:var(--crm-muted-fg,#5b6478)] hover:bg-[color:var(--crm-muted,#f6f8fa)] hover:text-[color:var(--crm-fg,#0b1324)]"
        @click.stop="$emit('edit')"
      >
        <!-- Figma Settings path (p-17 .btn.sm.ghost) -->
        <svg
          class="size-3.5 shrink-0"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="3" />
          <path
            d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"
          />
        </svg>
        {{ __('Edit') }}
      </button>
      <button
        type="button"
        class="inline-flex h-7 w-[34px] items-center justify-center rounded-[7px] border border-transparent bg-transparent text-[color:var(--crm-muted-fg,#5b6478)] hover:bg-[color:var(--crm-muted,#f6f8fa)]"
        :title="__('Duplicate')"
        @click.stop="$emit('duplicate')"
      >
        <svg
          class="size-3.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <rect x="9" y="9" width="12" height="12" rx="2" />
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
        </svg>
      </button>
      <button
        type="button"
        class="inline-flex h-7 w-[34px] items-center justify-center rounded-[7px] border border-transparent bg-transparent text-[color:var(--crm-muted-fg,#5b6478)] hover:bg-[color:var(--crm-muted,#f6f8fa)]"
        :title="__('Delete')"
        @click.stop="$emit('remove')"
      >
        <svg
          class="size-3.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" />
        </svg>
      </button>
      <span
        class="inline-flex h-7 items-center px-1.5 text-[11px] text-[color:var(--crm-faint,#8a94a6)]"
      >
        {{ sizeLabel }}
      </span>
    </div>

    <!-- Figma .tile.sel: 6 corner/edge handles (8×8, -5px inset); no .hdl -->
    <template v-if="editing && selected && !dragging">
      <span
        v-for="(pos, i) in selectHandles"
        :key="'h' + i"
        class="pointer-events-none absolute z-[1] box-border size-2 rounded-[2px] border-2 border-[color:var(--crm-primary,#0a7393)] bg-[color:var(--crm-card,#fff)]"
        :style="pos"
        aria-hidden="true"
      />
    </template>

    <!-- Figma .tile .hdl — unselected edit tiles only (sel uses handles above) -->
    <span
      v-if="editing && !dragging && !selected"
      class="report-tile-hdl pointer-events-none absolute z-[1]"
      aria-hidden="true"
    />

    <div class="min-h-0 flex-1" :class="editing ? 'pointer-events-none' : ''">
      <ReportKpiTile
        v-if="tile.type === 'kpi'"
        :title="tile.title"
        :data="tile.data"
        :editing="editing"
        :dragging="dragging"
        :selected="selected"
      />
      <ReportChartTile
        v-else
        :title="tile.title"
        :subtitle="tileSubtitle"
        :tile-type="tile.type"
        :data="tile.data"
        :editing="editing"
        :dragging="dragging"
        :selected="selected"
      />
    </div>
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
  /** Mid-drag ghost — Figma omits the ⋯ menu on the floating card. */
  dragging: { type: Boolean, default: false },
})

defineEmits(['select', 'edit', 'duplicate', 'remove'])

const sizeLabel = computed(() => {
  const l = props.tile.layout || {}
  return `${l.w || 0} × ${l.h || 0}`
})

const selectHandles = [
  { top: '-5px', left: '-5px' },
  { top: '-5px', right: '-5px' },
  { bottom: '-5px', left: '-5px' },
  { bottom: '-5px', right: '-5px' },
  { top: 'calc(50% - 4px)', right: '-5px' },
  { bottom: '-5px', left: 'calc(50% - 4px)' },
]

const tileSubtitle = computed(() => {
  const fromData = props.tile.data?.subtitle || props.tile.config?.subtitle
  if (fromData) return String(fromData).replace(/^·\s*/, '')
  const cfg = props.tile.config || {}
  if (props.tile.type === 'bar' || props.tile.type === 'line') {
    if (cfg.aggregation === 'sum') return __('sum of deal value, ₹ L')
    if (cfg.aggregation === 'count') return __('count')
    return cfg.aggregation || ''
  }
  if (props.tile.type === 'funnel') return __('this quarter')
  return ''
})
</script>

<style scoped>
/* crm.css .tile .hdl */
.report-tile-hdl {
  right: 3px;
  bottom: 3px;
  width: 12px;
  height: 12px;
  border-right: 2px solid var(--crm-primary, #0a7393);
  border-bottom: 2px solid var(--crm-primary, #0a7393);
  border-radius: 0 0 3px 0;
}
/* Figma .tile.drag — shadow + primary ring on the same element as the border */
.report-tile--dragging {
  box-shadow:
    0 14px 30px rgba(4, 20, 27, 0.2),
    0 0 0 2px var(--crm-primary, #0a7393);
}
/* Figma svg.i uses stroke-width 1.75 — menu/grab icons only, not chart SVGs */
.report-tile :deep(.size-3\.5) {
  stroke-width: 1.75;
}
</style>
