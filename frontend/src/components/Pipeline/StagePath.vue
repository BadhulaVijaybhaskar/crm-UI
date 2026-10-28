<template>
  <div v-if="stages.length" class="flex flex-col gap-2">
    <p
      v-if="summary"
      class="m-0 text-right text-crm-meta font-semibold text-crm-primary"
    >
      {{ summary }}
    </p>
    <div class="flex gap-1.5">
      <section
        v-for="group in groups"
        :key="group.key"
        class="min-w-0 rounded-crm-rail border bg-crm-card px-2.5 pb-2.5 pt-2"
        :class="
          group.current
            ? 'border-crm-primary shadow-[inset_0_0_0_1px_var(--crm-primary)]'
            : 'border-crm-border'
        "
        :style="{ flex: `${Math.max(group.items.length, 1)} 1 0` }"
      >
        <header
          v-if="groups.length > 1"
          class="mb-2 flex items-center justify-between gap-2 text-crm-caps font-bold uppercase tracking-crm-caps"
          :class="group.current ? 'text-crm-primary' : 'text-crm-muted-fg'"
        >
          <span>{{ group.label }}</span>
          <span class="text-crm-label font-normal normal-case tracking-normal text-crm-fg">
            {{ group.items.length }}
          </span>
        </header>
        <div class="flex gap-1.5">
          <button
            v-for="item in group.items"
            :key="item.stage.name"
            type="button"
            class="min-w-0 flex-1 text-left"
            :aria-current="item.state === 'todo' ? undefined : 'step'"
            @click="emit('select', item.stage.name)"
          >
            <span class="block" :class="barClass[item.state]" />
            <span
              class="mt-1 block truncate text-crm-meta font-semibold"
              :class="titleClass[item.state]"
            >
              {{ item.stage.label || item.stage.name }}
            </span>
            <span
              v-if="item.date"
              class="mt-0.5 block truncate text-crm-micro text-crm-muted-fg"
            >
              {{ item.date }}
            </span>
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatDate } from '@/utils'
import { isCloseStage, stageState } from '@/components/Pipeline/stageRail'

const props = defineProps({
  stages: { type: Array, default: () => [] },
  current: { type: String, default: '' },
  dates: { type: Object, default: () => ({}) },
  summary: { type: String, default: '' },
})

const emit = defineEmits(['select'])

const barClass = {
  done: 'h-1.5 rounded-[3px] bg-crm-primary',
  current: 'h-1.5 rounded-[3px] bg-crm-primary shadow-[0_0_0_2px_var(--crm-primary-soft)]',
  won: 'h-1.5 rounded-[3px] bg-crm-success',
  lost: 'h-1.5 rounded-[3px] border border-crm-danger bg-crm-danger-soft',
  todo: 'h-1.5 rounded-[3px] bg-crm-neutral-soft',
}

const titleClass = {
  done: 'text-crm-fg',
  current: 'text-crm-fg',
  won: 'text-crm-success',
  lost: 'text-crm-danger',
  todo: 'font-medium text-crm-muted-fg',
}

const currentIndex = computed(() =>
  props.stages.findIndex((stage) => stage.name === props.current),
)

const groups = computed(() => {
  const indexed = props.stages.map((stage, index) => ({
    stage,
    index,
    state: stageState(stage, index, currentIndex.value),
    date: props.dates?.[stage.name]
      ? formatDate(props.dates[stage.name], 'D MMM')
      : '',
  }))
  const path = indexed.filter((item) => !isCloseStage(item.stage))
  const close = indexed.filter((item) => isCloseStage(item.stage))
  const next = []
  if (path.length) next.push({ key: 'path', label: __('Stages'), items: path })
  if (close.length) next.push({ key: 'close', label: __('Close'), items: close })
  return next.map((group) => ({
    ...group,
    current: group.items.some((item) => item.state !== 'todo' && item.state !== 'done'),
  }))
})
</script>
