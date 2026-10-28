<template>
  <div
    class="report-grid min-h-0 flex-1 overflow-y-auto p-3"
    :class="editing ? 'report-grid--editing' : ''"
  >
    <GridLayout
      v-if="items.length > 0"
      class="h-fit w-full"
      :class="editing ? 'mb-40 !select-none' : ''"
      :col-num="12"
      :cols="{ lg: 12, md: 12, sm: 12, xs: 1, xxs: 1 }"
      :row-height="92"
      :margin="[12, 12]"
      :is-draggable="editing"
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
        :min-h="tile.layout.minH || 2"
      >
        <div v-if="layoutReady" class="h-full w-full">
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
        class="flex size-11 items-center justify-center rounded-[10px] bg-[color:var(--crm-muted,#f1f5f9)] text-[color:var(--crm-muted-fg,#64748b)]"
      >
        <span class="lucide-layout-dashboard size-5" />
      </div>
      <div class="text-[15px] font-semibold text-[color:var(--crm-fg,#0f172a)]">
        {{ __('No tiles yet') }}
      </div>
      <p class="max-w-[420px] text-[13px] text-[color:var(--crm-muted-fg,#64748b)]">
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
import { Button } from 'frappe-ui'
import { GridItem, GridLayout } from 'grid-layout-plus'
import { ref } from 'vue'

defineProps({
  editing: { type: Boolean, default: false },
  selectedId: { type: String, default: null },
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
      var(--crm-border, #e2e8f0) 1px,
      transparent 1px
    ),
    linear-gradient(
      to bottom,
      var(--crm-border, #e2e8f0) 1px,
      transparent 1px
    );
  background-size: calc((100% - 24px) / 12) 104px;
  background-position: 12px 12px;
  outline: 1px dashed var(--crm-border-strong, #94a3b8);
  outline-offset: 6px;
  border-radius: 10px;
}

.vgl-layout {
  --vgl-placeholder-bg: var(--crm-primary-soft, #e6f4f8);
  --vgl-placeholder-opacity: 100%;
  --vgl-placeholder-z-index: 2;
  --vgl-item-dragging-z-index: 3;
  --vgl-item-resizing-z-index: 3;
  --vgl-resizer-size: 12px;
}

:deep(.vgl-item--placeholder) {
  background-color: var(--crm-primary-soft, #e6f4f8);
  border: 2px dashed var(--crm-primary, #0a7393);
  border-radius: 10px;
  opacity: 1;
}

:deep(.vgl-item--dragging) {
  transform: rotate(-0.6deg);
  box-shadow: var(
    --crm-shadow-tile-drag,
    0 14px 30px rgba(4, 20, 27, 0.2),
    0 0 0 2px var(--crm-primary, #0a7393)
  );
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
}
</style>
