<template>
  <div class="flex h-full min-h-0 flex-col">
    <div
      class="flex shrink-0 items-center justify-between gap-3 px-crm-page-x pb-2 pt-1"
    >
      <p
        class="m-0 text-crm-caps font-bold uppercase tracking-crm-caps text-crm-muted-fg"
      >
        {{ __('Deal stages') }}
        <span class="font-medium normal-case tracking-normal text-crm-faint">
          · {{ __('Open') }}
        </span>
      </p>
      <button
        v-if="showStagesLink"
        type="button"
        class="inline-flex h-crm-control-sm items-center gap-1.5 rounded-crm-control-sm px-2.5 text-crm-label font-medium text-crm-muted-fg shadow-[inset_0_0_0_1px_var(--crm-border-strong)] hover:text-crm-fg"
        @click="openStages"
      >
        <span class="lucide-settings size-3.5" aria-hidden="true" />
        {{ __('Stages') }}
      </button>
    </div>

    <div class="flex min-h-0 flex-1 gap-3 overflow-x-auto px-crm-page-x pb-6">
      <div class="flex h-full min-h-0 gap-3">
        <AstraKanbanColumn
          v-for="column in openColumns"
          :key="column.column.name"
          :title="column.column.name"
          :color="stageDot(column.column.name)"
          :count="column.column.count ?? column.data?.length ?? 0"
          :subtitle="columnSubtitle(column)"
          fill-height
        >
          <Draggable
            :list="column.data"
            group="deal-cards"
            item-key="name"
            class="flex min-h-[84px] flex-1 flex-col gap-2"
            :delay="isTouchScreenDevice() ? 200 : 0"
            :data-column="column.column.name"
            ghost-class="astra-kanban-ghost"
            @start="dragging = true"
            @end="(evt) => onCardMove(evt)"
          >
            <template #item="{ element: fields }">
              <div
                class="relative"
                :data-name="fields.name"
                @click="options.onClick?.(fields)"
              >
                <router-link
                  v-if="options.getRoute"
                  :to="options.getRoute(fields)"
                  class="absolute inset-0 z-[1] rounded-crm-card focus-visible:outline-none focus-visible:shadow-crm-focus"
                  :aria-label="cardTitle(fields)"
                />
                <AstraKanbanCard
                  class="relative z-0"
                  :title="cardTitle(fields)"
                  :value="cardValue(fields)"
                  :owner="cardOwner(fields)"
                  owner-right
                  :meta="cardMeta(fields)"
                  :date="cardDate(fields)"
                  :chips="cardChips(fields)"
                  :dragging="draggingName === fields.name"
                />
              </div>
            </template>
          </Draggable>
          <button
            v-if="column.column.count < column.column.all_count"
            type="button"
            class="mt-1 inline-flex h-crm-control-sm items-center justify-center rounded-crm-control-sm text-crm-label font-medium text-crm-muted-fg hover:bg-crm-card"
            @click="$emit('loadMore', column.column.name)"
          >
            {{ __('Load more') }}
          </button>
        </AstraKanbanColumn>
      </div>

      <section
        v-if="wonColumn || lostColumn"
        class="flex w-[200px] shrink-0 flex-col gap-3"
      >
        <p
          class="m-0 text-crm-caps font-bold uppercase tracking-crm-caps text-crm-muted-fg"
        >
          {{ __('Won / Lost') }}
        </p>
        <div
          v-if="wonColumn"
          class="flex min-h-[120px] flex-1 flex-col rounded-crm-panel border border-dashed border-crm-success bg-crm-success-soft/40 p-2"
          :data-column="wonColumn.column.name"
        >
          <div class="mb-2 flex items-center justify-between px-1">
            <span class="text-crm-label font-semibold text-crm-success">
              {{ __('Won') }}
            </span>
            <span class="text-crm-meta text-crm-muted-fg">
              {{ wonColumn.column.count ?? 0 }}
            </span>
          </div>
          <p class="mb-2 px-1 text-crm-meta text-crm-muted-fg">
            {{ columnSubtitle(wonColumn) }}
          </p>
          <Draggable
            :list="wonColumn.data"
            group="deal-cards"
            item-key="name"
            class="flex min-h-[84px] flex-1 flex-col gap-2"
            :delay="isTouchScreenDevice() ? 200 : 0"
            :data-column="wonColumn.column.name"
            ghost-class="astra-kanban-ghost"
            @end="(evt) => onCardMove(evt)"
          >
            <template #item="{ element: fields }">
              <div class="relative" :data-name="fields.name">
                <router-link
                  v-if="options.getRoute"
                  :to="options.getRoute(fields)"
                  class="absolute inset-0 z-[1] rounded-crm-card"
                  :aria-label="cardTitle(fields)"
                />
                <AstraKanbanCard
                  :title="cardTitle(fields)"
                  :value="cardValue(fields)"
                  :owner="cardOwner(fields)"
                  owner-right
                  :chips="cardChips(fields)"
                />
              </div>
            </template>
          </Draggable>
        </div>
        <div
          v-if="lostColumn"
          class="flex min-h-[120px] flex-1 flex-col rounded-crm-panel border border-dashed border-crm-danger bg-crm-danger-soft/40 p-2"
          :data-column="lostColumn.column.name"
        >
          <div class="mb-2 flex items-center justify-between px-1">
            <span class="text-crm-label font-semibold text-crm-danger">
              {{ __('Lost') }}
            </span>
            <span class="text-crm-meta text-crm-muted-fg">
              {{ lostColumn.column.count ?? 0 }}
            </span>
          </div>
          <p class="mb-2 px-1 text-crm-meta text-crm-muted-fg">
            {{ columnSubtitle(lostColumn) }}
          </p>
          <Draggable
            :list="lostColumn.data"
            group="deal-cards"
            item-key="name"
            class="flex min-h-[84px] flex-1 flex-col gap-2"
            :delay="isTouchScreenDevice() ? 200 : 0"
            :data-column="lostColumn.column.name"
            ghost-class="astra-kanban-ghost"
            @end="(evt) => onCardMove(evt)"
          >
            <template #item="{ element: fields }">
              <div class="relative" :data-name="fields.name">
                <router-link
                  v-if="options.getRoute"
                  :to="options.getRoute(fields)"
                  class="absolute inset-0 z-[1] rounded-crm-card"
                  :aria-label="cardTitle(fields)"
                />
                <AstraKanbanCard
                  :title="cardTitle(fields)"
                  :value="cardValue(fields)"
                  :owner="cardOwner(fields)"
                  owner-right
                  :chips="cardChips(fields)"
                />
              </div>
            </template>
          </Draggable>
        </div>
        <p class="m-0 text-crm-meta text-crm-faint">
          {{ __('Drop a card here to mark it won or lost.') }}
        </p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import Draggable from 'vuedraggable'
import AstraKanbanCard from '@/components/astra/AstraKanbanCard.vue'
import AstraKanbanColumn from '@/components/astra/AstraKanbanColumn.vue'
import {
  STAGE_COLOURS,
  stageToken,
} from '@/components/astra/format'
import { dealCardChips, stageColourVar } from '@/components/astra/dealChips'
import { isTouchScreenDevice } from '@/utils'
import { formatCompactNumber } from '@/utils/numberFormat'
import { statusesStore } from '@/stores/statuses'
import { usersStore } from '@/stores/users'
import { showSettings, activeSettingsPage } from '@/composables/settings'

const props = defineProps({
  options: {
    type: Object,
    default: () => ({
      getRoute: null,
      onClick: null,
      onNewClick: null,
    }),
  },
  /** Parsed rows keyed by deal name (from Deals.vue parseRows). */
  rowsByName: { type: Object, default: () => ({}) },
  showStagesLink: { type: Boolean, default: false },
})

const emit = defineEmits(['update', 'loadMore'])
const kanban = defineModel({ type: Object })

const { getDealStatus, dealStatuses } = statusesStore()
const { getUser } = usersStore()

const dragging = ref(false)
const draggingName = ref('')

const allColumns = computed(() => {
  if (!kanban.value?.data?.data || kanban.value.data.view_type != 'kanban') {
    return []
  }
  return (kanban.value.data.data || []).filter((col) => {
    if (!col.column?.delete && !Array.isArray(col.data)) {
      col.data = []
    }
    return !col.column?.delete
  })
})

function statusType(name) {
  return getDealStatus(name)?.type || ''
}

const openColumns = computed(() =>
  allColumns.value.filter((col) => {
    const type = statusType(col.column.name)
    return type !== 'Won' && type !== 'Lost'
  }),
)

const wonColumn = computed(
  () =>
    allColumns.value.find((col) => statusType(col.column.name) === 'Won') ||
    null,
)

const lostColumn = computed(
  () =>
    allColumns.value.find((col) => statusType(col.column.name) === 'Lost') ||
    null,
)

function stageDot(name) {
  return stageColourVar(stageToken(name) || STAGE_COLOURS[name] || 'c6')
}

function columnSubtitle(column) {
  const rows = column.data || []
  let total = 0
  let weight = 0
  for (const raw of rows) {
    const row = props.rowsByName[raw.name] || raw
    const value = Number(
      raw.expected_deal_value ??
        raw.deal_value ??
        row.expected_deal_value?.label ??
        row.expected_deal_value ??
        0,
    )
    const probability = Number(
      raw.probability ?? row.probability?.label ?? row.probability ?? 0,
    )
    if (Number.isFinite(value)) total += value
    if (Number.isFinite(value) && Number.isFinite(probability)) {
      weight += (value * probability) / 100
    }
  }
  const prob =
    dealStatuses.data?.find?.((s) => s.name === column.column.name)
      ?.probability ?? column.column.probability
  const parts = []
  if (total) parts.push(`₹${formatCompactNumber(total)}`)
  if (prob != null && prob !== '') parts.push(`${prob}%`)
  else if (weight && total) parts.push(`${Math.round((weight / total) * 100)}%`)
  return parts.join(' · ')
}

function rowOf(fields) {
  return props.rowsByName[fields.name] || fields
}

function cardTitle(fields) {
  const row = rowOf(fields)
  return (
    row.organization?.label ||
    fields.organization ||
    row.lead_name?.label ||
    fields.name ||
    __('Untitled')
  )
}

function cardValue(fields) {
  const row = rowOf(fields)
  const formatted =
    row.expected_deal_value?.label ||
    row.deal_value?.label ||
    row.expected_deal_value ||
    row.deal_value
  if (formatted && typeof formatted === 'string' && formatted.includes('₹')) {
    return formatted
  }
  const raw = fields.expected_deal_value ?? fields.deal_value
  if (raw == null || raw === '') return ''
  const n = Number(raw)
  if (!Number.isFinite(n)) return String(raw)
  return `₹${formatCompactNumber(n)}`
}

function cardOwner(fields) {
  const row = rowOf(fields)
  return (
    row.deal_owner?.full_name ||
    row.deal_owner?.label ||
    (fields.deal_owner && getUser(fields.deal_owner)?.full_name) ||
    ''
  )
}

function cardMeta(fields) {
  const row = rowOf(fields)
  return row.lead_name?.label || fields.lead_name || ''
}

function cardDate(fields) {
  const row = rowOf(fields)
  return (
    row.expected_closure_date?.label ||
    row.expected_closure_date ||
    fields.expected_closure_date ||
    ''
  )
}

function cardChips(fields) {
  return dealCardChips({ ...fields, ...rowOf(fields) })
}

function serializeColumns() {
  return allColumns.value.map((col) => {
    const column = { ...col.column, order: (col.data || []).map((d) => d.name) }
    if (column.page_length) delete column.page_length
    return column
  })
}

function onCardMove(d) {
  dragging.value = false
  draggingName.value = ''
  const toColumn = d?.to?.dataset?.column
  const fromColumn = d?.from?.dataset?.column
  const itemName = d?.item?.dataset?.name
  const payload = { kanban_columns: serializeColumns() }
  if (toColumn && fromColumn && toColumn !== fromColumn) {
    payload.item = itemName
    payload.to = toColumn
    payload.from = fromColumn
    payload.fromIndex = d?.oldIndex
  }
  emit('update', payload)
}

function openStages() {
  showSettings.value = true
  activeSettingsPage.value = 'Stages'
}
</script>

<style scoped>
:deep(.astra-kanban-ghost) {
  min-height: 84px;
  border-radius: 8px;
  border: 1.5px dashed var(--crm-primary);
  background: var(--crm-primary-soft);
}
</style>
