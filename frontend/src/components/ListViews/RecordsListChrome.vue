<template>
  <div class="flex min-h-0 flex-1 flex-col bg-crm-bg">
    <AstraPageHeader :title="title" :description="description">
      <template #actions>
        <slot name="actions">
          <AstraButton
            v-if="createLabel"
            variant="primary"
            :label="createLabel"
            @click="$emit('create')"
          >
            <template #prefix>
              <span class="lucide-plus size-3.5" aria-hidden="true" />
            </template>
          </AstraButton>
        </slot>
      </template>
    </AstraPageHeader>

    <div
      v-if="viewTabs.length || showViewSwitch"
      class="flex items-center gap-2 border-b border-crm-border bg-crm-card px-crm-page-x"
    >
      <div class="min-w-0 flex-1 overflow-x-auto">
        <div class="flex items-center gap-0.5" role="tablist">
          <button
            v-for="tab in viewTabs"
            :key="tab.value"
            type="button"
            role="tab"
            class="inline-flex h-[38px] items-center gap-1.5 whitespace-nowrap border-b-2 border-transparent px-2.5 text-crm-body font-medium text-crm-muted-fg"
            :class="{
              'border-crm-primary font-semibold text-crm-fg':
                tab.value === activeView,
            }"
            :aria-selected="tab.value === activeView"
            @click="$emit('select-view', tab)"
          >
            <span>{{ tab.label }}</span>
            <span
              v-if="tab.count != null"
              class="text-crm-micro font-semibold text-crm-faint"
            >
              {{ tab.count }}
            </span>
          </button>
          <button
            v-if="showSaveView"
            type="button"
            class="inline-flex h-[38px] items-center gap-1 px-2.5 text-crm-body font-semibold text-crm-primary"
            @click="$emit('save-view')"
          >
            <span class="lucide-plus size-3.5" aria-hidden="true" />
            {{ __('Save view') }}
          </button>
        </div>
      </div>
      <div
        v-if="showViewSwitch"
        class="flex shrink-0 items-center gap-0.5 rounded-crm-control bg-crm-muted p-[3px] shadow-[inset_0_0_0_1px_var(--crm-border)]"
        role="group"
        :aria-label="__('View type')"
      >
        <button
          type="button"
          class="inline-flex h-[26px] items-center rounded-crm-chip px-2.5 text-crm-label font-medium"
          :class="
            viewType === 'list'
              ? 'bg-crm-card font-semibold text-crm-fg shadow-[inset_0_0_0_1px_var(--crm-border)]'
              : 'text-crm-muted-fg'
          "
          @click="$emit('set-view-type', 'list')"
        >
          {{ __('List') }}
        </button>
        <button
          type="button"
          class="inline-flex h-[26px] items-center rounded-crm-chip px-2.5 text-crm-label font-medium"
          :class="
            viewType === 'kanban'
              ? 'bg-crm-card font-semibold text-crm-fg shadow-[inset_0_0_0_1px_var(--crm-border)]'
              : 'text-crm-muted-fg'
          "
          @click="$emit('set-view-type', 'kanban')"
        >
          {{ __('Board') }}
        </button>
      </div>
    </div>

    <AstraFilterBar
      v-if="showFilterBar"
      :filters="filterChips"
      :sort-label="sortLabel"
      :show-add="showAddFilter"
      :add-label="__('Filter')"
      @add-filter="$emit('add-filter')"
      @remove-filter="(f) => $emit('remove-filter', f)"
      @sort="$emit('sort')"
    >
      <template v-if="$slots.filters" #filters>
        <slot name="filters" />
      </template>
      <template #actions>
        <slot name="toolbar" />
        <slot name="board-toolbar" />
      </template>
    </AstraFilterBar>

    <div class="relative flex min-h-0 flex-1 flex-col overflow-hidden">
      <slot />
    </div>
  </div>
</template>

<script setup>
import AstraButton from '@/components/astra/AstraButton.vue'
import AstraFilterBar from '@/components/astra/AstraFilterBar.vue'
import AstraPageHeader from '@/components/astra/AstraPageHeader.vue'

defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  createLabel: { type: String, default: '' },
  viewTabs: { type: Array, default: () => [] },
  activeView: { type: [String, Number], default: '' },
  showSaveView: { type: Boolean, default: false },
  showViewSwitch: { type: Boolean, default: false },
  viewType: { type: String, default: 'list' },
  filterChips: { type: Array, default: () => [] },
  showFilterBar: { type: Boolean, default: true },
  showAddFilter: { type: Boolean, default: true },
  sortLabel: { type: String, default: '' },
})

defineEmits([
  'create',
  'select-view',
  'save-view',
  'set-view-type',
  'remove-filter',
  'add-filter',
  'sort',
])
</script>
