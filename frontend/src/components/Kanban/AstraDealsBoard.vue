<template>
  <div class="relative flex h-full min-h-0 flex-col">
    <div
      class="-translate-y-[3px] flex shrink-0 items-end gap-3 px-crm-page-x pb-2 pt-1"
    >
      <p
        class="m-0 min-w-0 flex-1 border-t-2 border-crm-border-strong pt-1.5 text-[10.5px] font-bold uppercase tracking-[0.06em] text-crm-muted-fg"
        :style="{ maxWidth: '1008px' }"
      >
        {{ __('Deal stages · open · set by your admin in Settings → Pipeline stages') }}
      </p>
      <p
        v-if="wonColumn || lostColumn"
        class="m-0 w-[126px] shrink-0 border-t-2 border-crm-success pt-1.5 text-[10.5px] font-bold uppercase tracking-[0.06em] text-crm-success"
      >
        {{ __('Won / Lost') }}
      </p>
    </div>

    <div
      class="-translate-y-[3px] flex min-h-0 flex-1 gap-3 overflow-x-auto px-crm-page-x pb-6"
    >
      <div class="flex h-full min-h-0 gap-3">
        <AstraKanbanColumn
          v-for="column in openColumns"
          :key="column.column.name"
          :title="column.column.name"
          :color="stageDot(column.column.name)"
          :count="column.column.count ?? column.data?.length ?? 0"
          :subtitle="columnValueLabel(column)"
          :subtitle-right="columnProbLabel(column)"
          :width="192"
          fill-height
        >
          <!-- Parity mid-drag: flat list with ghost between cards (no Draggable wrap) -->
          <div
            v-if="parityDrag"
            class="flex min-h-[84px] flex-1 flex-col gap-2"
            :data-column="column.column.name"
          >
            <template
              v-for="(fields, index) in column.data || []"
              :key="fields.name"
            >
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
                  :owner="cardContact(fields)"
                  :avatar-name="cardOwner(fields)"
                  :date="cardDate(fields)"
                  :chips="cardChips(fields)"
                  :faded="parityDrag.name === fields.name"
                />
              </div>
              <div
                v-if="parityGhostAfter(column, index)"
                class="astra-kanban-ghost min-h-[84px]"
                aria-hidden="true"
              />
            </template>
          </div>
          <Draggable
            v-else
            :list="column.data"
            group="deal-cards"
            item-key="name"
            class="flex min-h-[84px] flex-1 flex-col gap-2"
            :delay="isTouchScreenDevice() ? 200 : 0"
            :data-column="column.column.name"
            ghost-class="astra-kanban-ghost"
            @start="(evt) => onDragStart(evt)"
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
                  :owner="cardContact(fields)"
                  :avatar-name="cardOwner(fields)"
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

      <!-- Closed · period — Figma summary column (not live Won/Lost card lists) -->
      <section
        v-if="wonColumn || lostColumn"
        class="flex w-[126px] shrink-0 flex-col overflow-hidden rounded-crm-panel border border-dashed border-crm-border bg-transparent"
      >
        <header class="shrink-0 px-3 pb-2 pt-2.5">
          <div class="text-[12px] font-semibold text-crm-fg">
            {{ closedHeading }}
          </div>
        </header>
        <div class="flex flex-col gap-2.5 p-2">
          <div
            v-if="wonColumn"
            class="flex flex-col gap-[3px] rounded-crm-card border border-crm-border bg-crm-card p-[10px_11px]"
            :data-column="wonColumn.column.name"
          >
            <span
              class="inline-flex h-[22px] w-fit items-center gap-1.5 rounded-md bg-crm-success-soft px-2 text-[11.5px] font-semibold text-crm-success"
            >
              <span
                class="size-[7px] rounded-[2px] bg-crm-success"
                aria-hidden="true"
              />
              {{ __('Won') }}
            </span>
            <div class="mt-1 text-[13px] font-bold tabular-nums text-crm-fg">
              {{ wonColumn.column.count ?? wonColumn.column.all_count ?? 0 }}
            </div>
            <div class="text-[11.5px] tabular-nums text-crm-muted-fg">
              {{ columnValueLabel(wonColumn) }}
            </div>
            <Draggable
              :list="wonColumn.data"
              group="deal-cards"
              item-key="name"
              class="hidden"
              :data-column="wonColumn.column.name"
              @end="(evt) => onCardMove(evt)"
            >
              <template #item="{ element: fields }">
                <div :data-name="fields.name" />
              </template>
            </Draggable>
          </div>
          <div
            v-if="lostColumn"
            class="flex flex-col gap-[3px] rounded-crm-card border border-crm-border bg-crm-card p-[10px_11px]"
            :data-column="lostColumn.column.name"
          >
            <span
              class="inline-flex h-[22px] w-fit items-center gap-1.5 rounded-md bg-crm-danger-soft px-2 text-[11.5px] font-semibold text-crm-danger"
            >
              <span
                class="size-[7px] rounded-[2px] bg-crm-danger"
                aria-hidden="true"
              />
              {{ __('Lost') }}
            </span>
            <div class="mt-1 text-[13px] font-bold tabular-nums text-crm-fg">
              {{ lostColumn.column.count ?? lostColumn.column.all_count ?? 0 }}
            </div>
            <div class="text-[11.5px] tabular-nums text-crm-muted-fg">
              {{ columnValueLabel(lostColumn) }}
            </div>
            <Draggable
              :list="lostColumn.data"
              group="deal-cards"
              item-key="name"
              class="hidden"
              :data-column="lostColumn.column.name"
              @end="(evt) => onCardMove(evt)"
            >
              <template #item="{ element: fields }">
                <div :data-name="fields.name" />
              </template>
            </Draggable>
          </div>
          <p class="m-0 text-[11px] leading-[1.4] text-crm-faint">
            {{ __('Drop a card here to mark it won or lost') }}
          </p>
        </div>
      </section>
    </div>

    <!-- Drag preview — fixed + rotate on same box as HTML .dc.drag -->
    <div
      v-if="parityDragCard"
      class="pointer-events-none fixed z-[40] rotate-[-1.5deg]"
      :style="{
        left: `${parityDrag.left || 0}px`,
        top: `${parityDrag.top || 0}px`,
        width: `${parityDrag.width || 178}px`,
      }"
    >
      <AstraKanbanCard
        :title="cardTitle(parityDragCard)"
        :value="cardValue(parityDragCard)"
        :owner="cardContact(parityDragCard)"
        :avatar-name="cardOwner(parityDragCard)"
        dragging
        :moving-label="parityDrag.label"
        preview
      />
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
  formatCompactInr,
  formatInrAmount,
  stageToken,
} from '@/components/astra/format'
import { dealCardChips, stageColourVar } from '@/components/astra/dealChips'
import { isTouchScreenDevice } from '@/utils'
import { statusesStore } from '@/stores/statuses'
import { usersStore } from '@/stores/users'

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

const closedHeading = computed(() => {
  const period = wonColumn.value?.column?.period || lostColumn.value?.column?.period
  return period ? `${__('Closed')} · ${period}` : __('Closed')
})

const parityDrag = computed(() => kanban.value?.data?.parity_drag || null)

const parityDragCard = computed(() => {
  const drag = parityDrag.value
  if (!drag?.name) return null
  for (const col of allColumns.value) {
    const hit = (col.data || []).find((d) => d.name === drag.name)
    if (hit) return hit
  }
  return props.rowsByName[drag.name] || null
})

/** Insert empty drop ghost after this index in the target column (Figma: after first). */
function parityGhostAfter(column, index) {
  const drag = parityDrag.value
  if (!drag || drag.to !== column.column.name) return false
  if (column.data?.some((d) => d.name === drag.name)) return false
  const after = drag.insert_after ?? 0
  return index === after
}

function stageDot(name) {
  return stageColourVar(stageToken(name) || STAGE_COLOURS[name] || 'c6')
}

function columnTotal(column) {
  if (column.column?.total != null && Number.isFinite(Number(column.column.total))) {
    return Number(column.column.total)
  }
  const rows = column.data || []
  let total = 0
  for (const raw of rows) {
    const row = props.rowsByName[raw.name] || raw
    const value = Number(
      raw.expected_deal_value ??
        raw.deal_value ??
        row.expected_deal_value?.label ??
        row.expected_deal_value ??
        0,
    )
    if (Number.isFinite(value)) total += value
  }
  return total
}

function columnValueLabel(column) {
  const total = columnTotal(column)
  return total ? formatCompactInr(total) : ''
}

function columnProbLabel(column) {
  const prob =
    dealStatuses.data?.find?.((s) => s.name === column.column.name)
      ?.probability ?? column.column.probability
  if (prob == null || prob === '') return ''
  return `${prob}%`
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
    (typeof row.expected_deal_value === 'string' &&
    row.expected_deal_value.includes('₹')
      ? row.expected_deal_value
      : null) ||
    (typeof row.deal_value === 'string' && row.deal_value.includes('₹')
      ? row.deal_value
      : null)
  if (formatted) return formatted
  const raw = fields.expected_deal_value ?? fields.deal_value
  if (raw == null || raw === '') return ''
  const n = Number(raw)
  if (!Number.isFinite(n)) return String(raw)
  return formatInrAmount(n)
}

function cardContact(fields) {
  const row = rowOf(fields)
  return (
    row.contact?.label ||
    fields.contact ||
    row.lead_name?.label ||
    fields.lead_name ||
    ''
  )
}

function cardOwner(fields) {
  const row = rowOf(fields)
  return (
    row.deal_owner?.full_name ||
    row.deal_owner?.label ||
    (fields.deal_owner && getUser(fields.deal_owner)?.full_name) ||
    fields.deal_owner ||
    ''
  )
}

function formatShortDate(value) {
  if (!value) return ''
  if (typeof value === 'string' && /^[0-9]{2} [A-Za-z]{3}$/.test(value.trim())) {
    return value.trim()
  }
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  const months = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec',
  ]
  const dd = String(d.getDate()).padStart(2, '0')
  return `${dd} ${months[d.getMonth()]}`
}

function cardDate(fields) {
  const row = rowOf(fields)
  const raw =
    row.expected_closure_date?.label ||
    row.expected_closure_date ||
    fields.expected_closure_date ||
    ''
  return formatShortDate(raw)
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

function onDragStart(d) {
  dragging.value = true
  draggingName.value = d?.item?.dataset?.name || ''
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
</script>

<style scoped>
:deep(.astra-kanban-ghost) {
  height: 84px;
  min-height: 84px;
  border-radius: 8px;
  border: 1.5px dashed var(--crm-primary);
  background: var(--crm-primary-soft);
  box-sizing: border-box;
}
</style>
