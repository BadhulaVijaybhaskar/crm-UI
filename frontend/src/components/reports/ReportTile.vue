<template>
  <div
    class="report-tile group relative flex h-full w-full flex-col rounded-[10px] border bg-[color:var(--crm-card,#fff)] px-3.5 py-3 text-[color:var(--crm-fg,#0b1324)]"
    :class="[
      editing
        ? 'overflow-visible border-[color:var(--crm-border-strong,#d0d9e0)]'
        : 'overflow-hidden border-[color:var(--crm-border,#e1e7ec)]',
      selected ? 'shadow-[0_0_0_2px_var(--crm-primary,#0a7393)]' : '',
    ]"
    @click="$emit('select')"
  >
    <div
      v-if="editing && selected"
      class="absolute -top-3.5 right-2.5 z-[2] flex items-center gap-0.5 rounded-[7px] border border-[color:var(--crm-border,#e1e7ec)] bg-[color:var(--crm-card,#fff)] p-0.5 text-[12px] shadow-[0_4px_12px_rgba(4,20,27,0.12)]"
    >
      <button
        type="button"
        class="inline-flex h-7 items-center rounded-[5px] px-2 font-medium hover:bg-[color:var(--crm-muted,#f6f8fa)]"
        @click.stop="$emit('edit')"
      >
        {{ __('Edit') }}
      </button>
      <button
        type="button"
        class="inline-flex h-7 items-center rounded-[5px] px-2 font-medium hover:bg-[color:var(--crm-muted,#f6f8fa)]"
        @click.stop="$emit('duplicate')"
      >
        {{ __('Duplicate') }}
      </button>
      <button
        type="button"
        class="inline-flex h-7 items-center rounded-[5px] px-2 font-medium hover:bg-[color:var(--crm-muted,#f6f8fa)]"
        @click.stop="$emit('remove')"
      >
        {{ __('Delete') }}
      </button>
      <b
        class="inline-flex h-7 items-center px-2 font-medium text-[color:var(--crm-muted-fg,#5b6478)]"
      >
        {{ sizeLabel }}
      </b>
    </div>

    <div class="min-h-0 flex-1" :class="editing ? 'pointer-events-none' : ''">
      <ReportKpiTile
        v-if="tile.type === 'kpi'"
        :title="tile.title"
        :data="tile.data"
        :editing="editing"
      />
      <ReportChartTile
        v-else
        :title="tile.title"
        :subtitle="tileSubtitle"
        :tile-type="tile.type"
        :data="tile.data"
        :editing="editing"
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
})

defineEmits(['select', 'edit', 'duplicate', 'remove'])

const sizeLabel = computed(() => {
  const l = props.tile.layout || {}
  return `${l.w || 0} × ${l.h || 0}`
})

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
