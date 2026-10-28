<template>
  <div class="flex flex-col gap-3">
    <Draggable
      :list="sections"
      item-key="name"
      handle=".section-drag-handle"
      class="flex flex-col gap-3"
    >
      <template #item="{ element: section }">
        <section
          class="overflow-hidden rounded-crm-panel border border-crm-border bg-crm-card"
        >
          <header
            class="flex items-center justify-between gap-2 border-b border-crm-border px-3.5 py-2.5"
          >
            <div
              class="flex min-w-0 items-center gap-2"
              @dblclick="section.editingLabel = true"
            >
              <DragVerticalIcon
                class="section-drag-handle size-3.5 shrink-0 cursor-grab text-crm-faint"
              />
              <input
                v-if="section.editingLabel"
                v-model="section.label"
                class="min-w-0 flex-1 border-0 bg-transparent text-[13px] font-semibold text-crm-fg outline-none"
                @click.stop
                @blur="section.editingLabel = false"
                @keydown.enter="section.editingLabel = false"
              />
              <span
                v-else
                class="truncate text-[13px] font-semibold text-crm-fg"
              >
                {{ section.label || __('Untitled') }}
              </span>
            </div>
            <div class="flex shrink-0 items-center gap-1">
              <Combobox
                :model-value="null"
                :options="fieldOptions"
                @update:selected-option="(field) => addField(section, field)"
              >
                <template #trigger="{ open, setOpen }">
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 px-1 text-crm-label font-semibold text-crm-primary"
                    @click="setOpen(!open)"
                  >
                    <Icon icon="plus" class="size-3.5" />
                    {{ __('Field') }}
                  </button>
                </template>
              </Combobox>
              <Dropdown
                v-if="menuFor(section).length"
                :options="menuFor(section)"
              >
                <template #default>
                  <button
                    type="button"
                    class="inline-flex size-7 items-center justify-center rounded-crm-chip text-crm-faint hover:bg-crm-muted"
                    :aria-label="__('Section actions')"
                  >
                    <Icon icon="more-horizontal" class="size-4" />
                  </button>
                </template>
              </Dropdown>
            </div>
          </header>
          <div class="grid grid-cols-2 gap-2 px-3.5 py-3">
            <Draggable
              v-for="column in section.columns || []"
              :key="column.name"
              :list="column.fields"
              group="fields"
              item-key="fieldname"
              handle=".field-drag-handle"
              class="min-h-[34px]"
              :class="fieldsClass(section)"
            >
              <template #item="{ element: field }">
                <div
                  class="group flex h-[34px] min-w-0 items-center gap-2 rounded-[7px] bg-crm-card px-2.5 text-left"
                  :class="
                    selected === field
                      ? 'border border-crm-primary shadow-[0_0_0_3px_var(--crm-primary-soft)]'
                      : 'border border-crm-border'
                  "
                  role="button"
                  tabindex="0"
                  @click="selected = field"
                  @keydown.enter="selected = field"
                >
                  <DragVerticalIcon
                    class="field-drag-handle size-3.5 shrink-0 cursor-grab text-crm-faint"
                  />
                  <span
                    class="min-w-0 flex-1 truncate text-crm-label font-semibold text-crm-fg"
                  >
                    {{ field.label || field.fieldname }}
                    <span v-if="field.reqd" class="text-crm-danger">*</span>
                  </span>
                  <span class="shrink-0 text-[11.5px] text-crm-faint">
                    {{ field.fieldtype }}
                  </span>
                  <button
                    type="button"
                    class="inline-flex size-4 items-center justify-center text-crm-faint opacity-0 hover:text-crm-fg group-hover:opacity-100"
                    :aria-label="__('Remove field')"
                    @click.stop="removeField(column, field)"
                  >
                    <Icon icon="x" class="size-3" />
                  </button>
                </div>
              </template>
            </Draggable>
          </div>
        </section>
      </template>
    </Draggable>
    <button
      type="button"
      class="flex h-11 items-center justify-center gap-1.5 rounded-crm-control border border-dashed border-crm-border-strong text-crm-label font-semibold text-crm-primary hover:bg-crm-primary-soft"
      @click="addSection"
    >
      <Icon icon="plus" class="size-4" />
      {{ __('Add section') }}
    </button>
  </div>
</template>

<script setup>
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import Icon from '@/components/Icon.vue'
import { getRandom } from '@/utils'
import { Combobox, Dropdown } from 'frappe-ui'
import Draggable from 'vuedraggable'
import { watch } from 'vue'

const props = defineProps({
  fieldOptions: { type: Array, default: () => [] },
  sectionOptions: { type: Function, default: null },
})

const sections = defineModel({ type: Array, default: () => [] })
const selected = defineModel('selected', { type: Object, default: null })

watch(
  sections,
  () => {
    if (fieldExists(selected.value)) return
    // Figma 23 selects Expected close when present.
    selected.value =
      findField('expected_closure_date') ||
      findField('Expected close') ||
      firstField()
  },
  { deep: true, immediate: true },
)

function findField(needle) {
  const want = String(needle).toLowerCase()
  for (const section of sections.value || []) {
    for (const column of section.columns || []) {
      for (const field of column.fields || []) {
        if (
          String(field.fieldname || '').toLowerCase() === want ||
          String(field.label || '').toLowerCase() === want
        ) {
          return field
        }
      }
    }
  }
  return null
}

function fieldsClass(section) {
  if ((section.columns || []).length <= 1) {
    return 'col-span-2 grid grid-cols-1 gap-2 sm:grid-cols-2'
  }
  return 'flex min-w-0 flex-col gap-2'
}

function menuFor(section) {
  if (props.sectionOptions) return props.sectionOptions(section) || []
  return [
    {
      label: __('Rename'),
      icon: 'lucide-edit',
      onClick: () => {
        section.editingLabel = true
      },
    },
    {
      label: __('Remove section'),
      icon: 'lucide-trash-2',
      onClick: () => {
        const index = sections.value.indexOf(section)
        if (index >= 0) sections.value.splice(index, 1)
      },
    },
  ]
}

function addField(section, field) {
  if (!field) return
  if (!section.columns?.length) {
    section.columns = [{ name: 'column_' + getRandom(), fields: [] }]
  }
  const used = (section.columns || []).some((column) =>
    (column.fields || []).some((row) => row.fieldname === field.fieldname),
  )
  if (used) return
  let target = section.columns[0]
  for (const column of section.columns) {
    if ((column.fields?.length || 0) < (target.fields?.length || 0)) {
      target = column
    }
  }
  target.fields.push(field)
  selected.value = field
}

function removeField(column, field) {
  const index = column.fields.indexOf(field)
  if (index >= 0) column.fields.splice(index, 1)
  if (selected.value === field) selected.value = firstField()
}

function addSection() {
  sections.value.push({
    label: __('New section'),
    name: 'section_' + getRandom(),
    opened: true,
    columns: [
      { name: 'column_' + getRandom(), fields: [] },
      { name: 'column_' + getRandom(), fields: [] },
    ],
  })
}

function firstField() {
  for (const section of sections.value || []) {
    for (const column of section.columns || []) {
      if (column.fields?.length) return column.fields[0]
    }
  }
  return null
}

function fieldExists(field) {
  if (!field) return false
  for (const section of sections.value || []) {
    for (const column of section.columns || []) {
      if ((column.fields || []).includes(field)) return true
    }
  }
  return false
}

function removeSelected() {
  const field = selected.value
  if (!field) return
  for (const section of sections.value || []) {
    for (const column of section.columns || []) {
      if ((column.fields || []).includes(field)) {
        removeField(column, field)
        return
      }
    }
  }
}

defineExpose({ removeSelected })
</script>
