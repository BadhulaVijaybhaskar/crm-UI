<template>
  <div
    class="w-full overflow-x-hidden overflow-y-visible bg-crm-card"
    :class="{ 'min-h-64': !rows.length }"
  >
    <div v-if="!rows.length">
      <slot name="empty">
        <AstraEmptyState :title="emptyTitle" :body="emptyBody" />
      </slot>
    </div>
    <table v-else class="w-full border-collapse">
      <thead>
        <tr>
          <th
            v-if="selectable"
            class="h-crm-th w-[34px] border-b border-crm-border bg-crm-muted px-2.5 text-center"
          >
            <AstraCheckbox
              :checked="allSelected"
              :indeterminate="false"
              :aria-label="__('Select all')"
              @change="(checked) => $emit('toggle-all', checked)"
            />
          </th>
          <th
            v-for="col in columns"
            :key="col.key"
            class="h-crm-th border-b border-crm-border bg-crm-muted px-2.5 text-left text-crm-micro font-semibold text-crm-muted-fg"
            :class="[
              uppercaseHeaders ? 'uppercase tracking-[0.03em]' : 'normal-case',
              { 'text-right': col.align === 'right' },
            ]"
            :style="col.width ? { width: col.width } : undefined"
          >
            {{ col.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in rows"
          :key="rowKey(row)"
          class="cursor-pointer border-b border-crm-border hover:bg-crm-row-hover"
          :class="{
            'bg-crm-row-selected': isSelected(row),
            'bg-crm-row-hover': isHovered(row) && !isSelected(row),
          }"
          @click="$emit('row-click', row)"
        >
          <td
            v-if="selectable"
            class="h-crm-td w-[34px] px-2.5 text-center"
            :class="{
              'bg-crm-row-selected': isSelected(row),
              'bg-crm-row-hover': isHovered(row) && !isSelected(row),
            }"
            @click.stop
          >
            <AstraCheckbox
              :checked="isSelected(row)"
              :aria-label="__('Select row')"
              @change="(checked) => $emit('toggle-row', row, checked)"
            />
          </td>
          <td
            v-for="col in columns"
            :key="col.key"
            class="h-crm-td whitespace-nowrap px-2.5 text-crm-label text-crm-fg"
            :class="{
              'text-right': col.align === 'right',
              'bg-crm-row-selected': isSelected(row),
              'bg-crm-row-hover': isHovered(row) && !isSelected(row),
            }"
          >
            <slot :name="`cell-${col.key}`" :row="row" :column="col">
              {{ row[col.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AstraCheckbox from '@/components/astra/AstraCheckbox.vue'
import AstraEmptyState from '@/components/astra/AstraEmptyState.vue'

const props = defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  rowKeyField: { type: String, default: 'id' },
  selectable: { type: Boolean, default: false },
  selectedKeys: { type: Array, default: () => [] },
  /** Keys shown with row-hover (PNG parity snapshots often pin one .hov row). */
  hoveredKeys: { type: Array, default: () => [] },
  emptyTitle: { type: String, default: 'No records' },
  emptyBody: {
    type: String,
    default: 'Try adjusting filters or create a new record.',
  },
  /** Spec table headers are sentence case; set true for uppercase 11px caps. */
  uppercaseHeaders: { type: Boolean, default: true },
})

defineEmits(['row-click', 'toggle-row', 'toggle-all'])

function rowKey(row) {
  return row?.[props.rowKeyField] ?? row?.name ?? row?.id
}

function isSelected(row) {
  return props.selectedKeys.includes(rowKey(row))
}

function isHovered(row) {
  return props.hoveredKeys.includes(rowKey(row))
}

const allSelected = computed(
  () =>
    props.rows.length > 0 &&
    props.rows.every((row) => props.selectedKeys.includes(rowKey(row))),
)
</script>
