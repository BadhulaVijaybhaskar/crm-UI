<template>
  <div class="grid grid-cols-2 gap-3">
    <FormControl
      :model-value="model.doctype || model.source_doctype"
      type="select"
      :label="__('Module')"
      :options="moduleOptions"
      @update:model-value="set('doctype', $event)"
    />
    <FormControl
      :model-value="model.aggregation || 'count'"
      type="select"
      :label="__('Aggregate')"
      :options="aggOptions"
      @update:model-value="set('aggregation', $event)"
    />
    <FormControl
      v-if="(model.aggregation || 'count') !== 'count'"
      :model-value="model.field || model.aggregate_field"
      type="select"
      :label="__('Field')"
      :options="numericOptions"
      @update:model-value="set('field', $event)"
    />
    <FormControl
      :model-value="model.date_field || 'creation'"
      type="select"
      :label="__('Date field')"
      :options="dateOptions"
      @update:model-value="set('date_field', $event)"
    />
  </div>
</template>

<script setup>
import { FormControl } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  meta: { type: Object, default: () => ({}) },
})

const model = defineModel({ type: Object, required: true })

const moduleOptions = computed(() =>
  (props.meta.modules || []).map((m) => ({ label: m.label, value: m.value })),
)

const fields = computed(() => {
  const dt = model.value.doctype || model.value.source_doctype
  return props.meta.fields_by_doctype?.[dt] || {}
})

const numericOptions = computed(() => fields.value.numeric || [])
const dateOptions = computed(() => fields.value.dates || [])
const aggOptions = computed(
  () =>
    fields.value.aggregations || [
      { label: 'Count', value: 'count' },
      { label: 'Sum', value: 'sum' },
      { label: 'Avg', value: 'avg' },
      { label: 'Min', value: 'min' },
      { label: 'Max', value: 'max' },
    ],
)

function set(key, value) {
  model.value[key] = value
}
</script>
