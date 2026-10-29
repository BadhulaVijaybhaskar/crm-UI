<template>
  <div
    class="report-grid min-h-0 flex-1 overflow-y-auto pb-6 pt-1"
    :class="editing ? 'report-grid--editing mx-crm-page-x' : 'px-crm-page-x'"
  >
    <GridLayout
      v-if="items.length > 0"
      class="report-grid-layout h-fit w-full"
      :class="editing ? 'mb-40 !select-none' : ''"
      :col-num="12"
      :cols="{ lg: 12, md: 12, sm: 12, xs: 1, xxs: 1 }"
      :row-height="92"
      :margin="[12, 12]"
      :is-draggable="editing && !draggingId"
      :is-resizable="editing"
      responsive
      :layout="items.map((item) => item.layout)"
      @update:layout="onLayout"
      @layout-ready="layoutReady = true"
    >
      <GridItem
        v-for="(tile, index) in items"
        :key="tile.layout.i"
        :i="tile.layout.i"
        :x="tile.layout.x"
        :y="tile.layout.y"
        :w="tile.layout.w"
        :h="tile.layout.h"
        :min-w="tile.layout.minW || 2"
        :min-h="tile.layout.minH || 1"
        :class="{
          'vgl-item--parity-dragging': draggingId && draggingId === tile.id,
        }"
      >
        <div
          v-if="draggingId && draggingId === tile.id"
          class="report-tile-drop-slot"
          aria-hidden="true"
        />
        <div
          v-if="layoutReady"
          class="h-full w-full"
          :class="{
            'report-tile-drag-ghost': draggingId && draggingId === tile.id,
          }"
        >
          <ReportTile
            :tile="tile"
            :editing="editing"
            :selected="selectedId === tile.id"
            @select="$emit('select', tile)"
            @edit="$emit('edit', tile)"
            @duplicate="$emit('duplicate', tile)"
            @remove="items.splice(index, 1)"
          />
        </div>
      </GridItem>
    </GridLayout>

    <div
      v-else
      class="flex flex-col items-center justify-center gap-3 px-6 py-20 text-center"
    >
      <div
        class="flex size-11 items-center justify-center rounded-[10px] bg-[color:var(--crm-muted,#f6f8fa)] text-[color:var(--crm-muted-fg,#5b6478)]"
      >
        <LucideLayoutDashboard class="size-5" />
      </div>
      <div class="text-[15px] font-semibold text-[color:var(--crm-fg,#0b1324)]">
        {{ __('No tiles yet') }}
      </div>
      <p class="max-w-[420px] text-[13px] text-[color:var(--crm-muted-fg,#5b6478)]">
        {{ __('Add a KPI or chart tile to start building this dashboard.') }}
      </p>
      <Button
        v-if="editing"
        variant="solid"
        :label="__('Add tile')"
        @click="$emit('add')"
      />
    </div>
  </div>
</template>

<script setup>
import ReportTile from './ReportTile.vue'
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import { Button } from 'frappe-ui'
import { GridItem, GridLayout } from 'grid-layout-plus'
import { ref } from 'vue'

defineProps({
  editing: { type: Boolean, default: false },
  selectedId: { type: String, default: null },
  draggingId: { type: String, default: null },
})

defineEmits(['select', 'edit', 'duplicate', 'add'])

const items = defineModel({ type: Array, default: () => [] })
const layoutReady = ref(false)

function onLayout(newLayout) {
  items.value.forEach((item, idx) => {
    item.layout = newLayout[idx]
  })
}
</script>

<style scoped>
.report-grid--editing {
  background-image:
    linear-gradient(
      to right,
      var(--crm-border, #e1e7ec) 1px,
      transparent 1px
    ),
    linear-gradient(
      to bottom,
      var(--crm-border, #e1e7ec) 1px,
      transparent 1px
    );
  background-size: calc((100% + 12px) / 12) 104px;
  outline: 1px dashed var(--crm-border-strong, #d0d9e0);
  outline-offset: 6px;
  border-radius: 4px;
}

.vgl-layout {
  --vgl-placeholder-bg: var(--crm-primary-soft, #e4f2f6);
  --vgl-placeholder-opacity: 100%;
  --vgl-placeholder-z-index: 2;
  --vgl-item-dragging-z-index: 3;
  --vgl-item-resizing-z-index: 3;
  --vgl-resizer-size: 12px;
}

/*
 * grid-layout-plus insets the first/last track by margin[0]/margin[1].
 * CSS-grid refs use gap only (no outer inset). Pull the layout out by
 * one margin so tile left edges match the Figma PNG / HTML dgrid.
 */
.report-grid-layout {
  margin-left: -12px;
  margin-right: -12px;
  width: calc(100% + 24px);
}

.report-grid--editing :deep(.vgl-item) {
  overflow: visible;
}

:deep(.vgl-item--placeholder) {
  background-color: var(--crm-primary-soft, #e4f2f6);
  border: 2px dashed var(--crm-primary, #0a7393);
  border-radius: 10px;
  opacity: 1;
}

:deep(.vgl-item--placeholder)::after {
  content: 'Drop here';
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--crm-primary, #0a7393);
  font-size: 12px;
  font-weight: 600;
  pointer-events: none;
}

:deep(.vgl-item--dragging),
:deep(.vgl-item--parity-dragging) {
  z-index: 3;
}

.report-tile-drop-slot {
  /* Figma 17: soft dashed home-slot behind the tipped mid-drag card */
  position: absolute;
  inset: 0;
  z-index: 1;
  border: 2px dashed var(--crm-primary, #0a7393);
  border-radius: 10px;
  background: var(--crm-primary-soft, #e4f2f6);
  pointer-events: none;
}

:deep(.vgl-item--dragging) .report-tile-drag-ghost,
.report-tile-drag-ghost {
  /*
   * Figma 17 mid-drag: card fills the slot then shifts down-right so the
   * soft dashed home-slot shows along the top/left and the card overhangs.
   */
  position: absolute;
  inset: 0;
  z-index: 2;
  width: auto;
  height: auto;
  transform: translate(10px, 22px) rotate(-0.6deg);
  box-shadow: var(
    --crm-shadow-tile-drag,
    0 14px 30px rgba(4, 20, 27, 0.2),
    0 0 0 2px var(--crm-primary, #0a7393)
  );
  border-radius: 10px;
  background: var(--crm-card, #fff);
}

:deep(.vgl-item__resizer) {
  right: 3px;
  bottom: 3px;
  width: 12px;
  height: 12px;
  border-right: 2px solid var(--crm-primary, #0a7393);
  border-bottom: 2px solid var(--crm-primary, #0a7393);
  border-radius: 0 0 3px 0;
  box-sizing: border-box;
  background: transparent;
}
</style>
