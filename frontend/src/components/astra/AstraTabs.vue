<template>
  <div
    class="flex items-center gap-0.5 overflow-x-auto border-b border-crm-border bg-crm-card px-crm-page-x"
    role="tablist"
    @keydown="onKeydown"
  >
    <button
      v-for="(tab, index) in tabs"
      :key="tab.value"
      :ref="(el) => setTabRef(el, index)"
      type="button"
      role="tab"
      class="inline-flex h-10 items-center gap-1.5 whitespace-nowrap border-b-2 border-transparent px-2.5 text-crm-body font-medium text-crm-muted-fg"
      :class="{
        'border-crm-primary font-semibold text-crm-fg': tab.value === modelValue,
        'h-[38px]': size === 'list',
      }"
      :aria-selected="tab.value === modelValue"
      :tabindex="tab.value === modelValue ? 0 : -1"
      @click="$emit('update:modelValue', tab.value)"
    >
      <span>{{ tab.label }}</span>
      <span
        v-if="tab.count != null"
        class="rounded bg-crm-neutral-soft px-1 text-crm-micro font-semibold text-crm-muted-fg"
      >
        {{ tab.count }}
      </span>
    </button>
    <div v-if="$slots.trailing" class="ml-auto flex items-center gap-2">
      <slot name="trailing" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  tabs: { type: Array, default: () => [] },
  size: { type: String, default: 'record' },
})

const emit = defineEmits(['update:modelValue'])
const tabRefs = ref([])

function setTabRef(el, index) {
  tabRefs.value[index] = el
}

function onKeydown(event) {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
  const values = props.tabs.map((t) => t.value)
  const current = values.indexOf(props.modelValue)
  if (current < 0) return
  let next = current
  if (event.key === 'ArrowRight') next = (current + 1) % values.length
  if (event.key === 'ArrowLeft') next = (current - 1 + values.length) % values.length
  if (event.key === 'Home') next = 0
  if (event.key === 'End') next = values.length - 1
  event.preventDefault()
  emit('update:modelValue', values[next])
  tabRefs.value[next]?.focus?.()
}
</script>
