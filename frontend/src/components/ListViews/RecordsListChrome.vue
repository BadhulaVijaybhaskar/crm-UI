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
      class="flex items-center gap-2 border-b border-crm-border px-crm-page-x"
    >
      <div class="min-w-0 flex-1 overflow-x-auto">
        <div class="flex items-center gap-0.5" role="tablist">
          <button
            v-for="tab in viewTabs"
            :key="tab.value"
            type="button"
            role="tab"
            class="-mb-px inline-flex h-[38px] items-center gap-1.5 whitespace-nowrap border-b-2 px-2.5 text-crm-body font-medium"
            :class="
              tab.value === activeView
                ? 'border-crm-primary font-semibold text-crm-fg'
                : 'border-transparent text-crm-muted-fg'
            "
            :aria-selected="tab.value === activeView"
            @click="$emit('select-view', tab)"
          >
            <span>{{ tab.label }}</span>
            <span
              v-if="tab.count != null"
              class="text-[11px] font-semibold text-crm-faint"
            >
              {{ tab.count }}
            </span>
          </button>
          <button
            v-if="showSaveView"
            type="button"
            class="-mb-px ml-[7px] inline-flex h-[38px] -translate-y-px items-center gap-1.5 px-2.5 text-crm-body font-semibold text-crm-primary"
            @click="$emit('save-view')"
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
            {{ __('Save view') }}
          </button>
        </div>
      </div>
      <div
        v-if="showViewSwitch"
        class="-translate-x-px flex shrink-0 items-center gap-0.5 rounded-crm-control bg-crm-muted p-[3px] shadow-[inset_0_0_0_1px_var(--crm-border)]"
        role="group"
        :aria-label="__('View type')"
      >
        <!--
          crm.css .views span { height:38px } cascades onto .seg spans in the
          HTML capture, so List/Board render at 38px and the tabs row is 46px.
          Match that signed-off height (app.css .seg span 26px is overridden).
        -->
        <button
          type="button"
          class="inline-flex h-[38px] items-center gap-1.5 rounded-crm-chip px-2.5 text-crm-label font-medium"
          :class="
            viewType === 'kanban'
              ? 'bg-crm-card font-semibold text-crm-fg shadow-[inset_0_0_0_1px_var(--crm-border)]'
              : 'text-crm-muted-fg'
          "
          @click="$emit('set-view-type', 'kanban')"
        >
          <svg
            class="size-3.5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            aria-hidden="true"
          >
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <path d="M8 7v7M12 7v4M16 7v9" />
          </svg>
          {{ __('Board') }}
        </button>
        <button
          type="button"
          class="inline-flex h-[38px] items-center gap-1.5 rounded-crm-chip px-2.5 text-crm-label font-medium"
          :class="
            viewType === 'list'
              ? 'bg-crm-card font-semibold text-crm-fg shadow-[inset_0_0_0_1px_var(--crm-border)]'
              : 'text-crm-muted-fg'
          "
          @click="$emit('set-view-type', 'list')"
        >
          <svg
            class="size-3.5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            aria-hidden="true"
          >
            <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
          </svg>
          {{ __('List') }}
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
