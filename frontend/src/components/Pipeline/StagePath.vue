<template>
  <div v-if="stages.length" class="flex gap-1.5">
    <section
      v-for="group in groups"
      :key="group.key"
      class="min-w-0 rounded-[9px] border px-2.5 pb-2.5 pt-2"
      :class="
        group.dashed
          ? 'border-dashed border-crm-border'
          : group.current
            ? 'border-crm-primary shadow-[inset_0_0_0_1px_var(--crm-primary)]'
            : 'border-crm-border'
      "
      :style="{ flex: `${group.flex} 1 0` }"
    >
      <header
        class="mb-1.5 flex items-center justify-between gap-2 text-[10.5px] font-bold uppercase tracking-[0.06em] text-crm-muted-fg"
      >
        <span :class="group.current ? 'text-crm-primary' : ''">{{
          group.label
        }}</span>
        <span
          v-if="group.badge"
          class="text-crm-label font-semibold normal-case tracking-normal text-crm-primary"
        >
          {{ group.badge }}
        </span>
      </header>
      <div class="flex gap-1">
        <button
          v-for="item in group.items"
          :key="item.stage.name"
          type="button"
          class="min-w-0 flex-1 text-left"
          :aria-current="item.state === 'todo' ? undefined : 'step'"
          @click="emit('select', item.stage.name)"
        >
          <span class="block h-1.5 rounded-[3px]" :class="barClass[item.state]" />
          <span
            class="mt-1 block truncate text-[11.5px] font-semibold"
            :class="titleClass[item.state]"
          >
            {{ item.stage.label || item.stage.name }}
          </span>
          <span
            v-if="item.date"
            class="mt-0.5 block truncate text-[11px] text-crm-muted-fg"
          >
            {{ item.date }}
          </span>
        </button>
      </div>
    </section>
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
  /** Optional copy overrides per status name (e.g. "since 24 Oct"). */
  dateLabels: { type: Object, default: () => ({}) },
  /** Optional caption under a status (e.g. Converted → "creates a deal"). */
  captions: { type: Object, default: () => ({}) },
  /** Optional group plan; defaults match Figma lead / deal rails. */
  groupPlan: { type: Array, default: null },
  summary: { type: String, default: '' },
})

const emit = defineEmits(['select'])

const barClass = {
  done: 'bg-crm-primary',
  current: 'bg-crm-primary shadow-[0_0_0_2px_var(--crm-primary-soft)]',
  won: 'bg-crm-success',
  lost: 'bg-crm-border-strong',
  todo: 'bg-crm-neutral-soft',
}

const titleClass = {
  done: 'text-crm-fg',
  current: 'text-crm-fg',
  won: 'text-crm-success',
  lost: 'font-medium text-crm-muted-fg',
  todo: 'font-medium text-crm-muted-fg',
}

const LEAD_PLAN = [
  {
    key: 'lead',
    label: __('1 · Lead'),
    names: ['New', 'Contacted', 'Nurture'],
    flex: 3,
    inProgress: true,
  },
  {
    key: 'qualified',
    label: __('2 · Qualified'),
    names: ['Qualified'],
    flex: 1.1,
  },
  {
    key: 'deal',
    label: __('3 · Deal'),
    names: ['Converted'],
    flex: 1.1,
  },
  {
    key: 'close',
    label: __('Close out'),
    names: ['Unqualified', 'Junk'],
    flex: 1.5,
    dashed: true,
  },
]

const DEAL_PLAN = [
  {
    key: 'path',
    label: __('Stages'),
    names: null,
    flex: 4,
  },
  {
    key: 'close',
    label: __('Close'),
    names: null,
    closeOnly: true,
    flex: 1.5,
    dashed: true,
  },
]

const currentIndex = computed(() =>
  props.stages.findIndex((stage) => stage.name === props.current),
)

function dateFor(stageName, state) {
  if (props.dateLabels?.[stageName]) return props.dateLabels[stageName]
  if (props.captions?.[stageName] && state === 'todo') {
    return props.captions[stageName]
  }
  if (props.dates?.[stageName]) {
    const formatted = formatDate(props.dates[stageName], 'D MMM')
    if (state === 'current') return __('since {0}', [formatted])
    return formatted
  }
  if (props.captions?.[stageName]) return props.captions[stageName]
  if (state === 'todo' || state === 'lost') return '—'
  return ''
}

function buildPlan() {
  if (props.groupPlan?.length) return props.groupPlan
  const names = props.stages.map((s) => s.name)
  const looksLikeLead = ['New', 'Contacted', 'Nurture', 'Qualified'].some((n) =>
    names.includes(n),
  )
  return looksLikeLead ? LEAD_PLAN : DEAL_PLAN
}

const groups = computed(() => {
  const indexed = props.stages.map((stage, index) => ({
    stage,
    index,
    state: stageState(stage, index, currentIndex.value),
  }))
  const byName = Object.fromEntries(
    indexed.map((item) => [item.stage.name, item]),
  )
  const plan = buildPlan()
  return plan
    .map((spec) => {
      let items
      if (spec.closeOnly) {
        items = indexed.filter((item) => isCloseStage(item.stage))
      } else if (Array.isArray(spec.names)) {
        items = spec.names
          .map((name) => byName[name])
          .filter(Boolean)
      } else {
        items = indexed.filter((item) => !isCloseStage(item.stage))
      }
      items = items.map((item) => ({
        ...item,
        date: dateFor(item.stage.name, item.state),
      }))
      const current = items.some(
        (item) => item.state === 'current' || item.state === 'won',
      )
      return {
        key: spec.key,
        label: spec.label,
        flex: spec.flex || Math.max(items.length, 1),
        dashed: !!spec.dashed,
        current,
        badge:
          spec.inProgress && current ? __('In progress') : spec.badge || '',
        items,
      }
    })
    .filter((group) => group.items.length)
})
</script>
