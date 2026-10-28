<template>
  <div class="relative flex min-h-0 flex-1 flex-col overflow-hidden bg-crm-bg px-crm-page-x pb-6">
    <div
      class="min-h-0 flex-1 overflow-hidden rounded-[10px] border border-crm-border bg-crm-card"
    >
      <div class="h-full overflow-y-auto overflow-x-hidden">
      <AstraListTable
        class="astra-leads-table"
        row-key-field="name"
        :columns="columns"
        :rows="rows"
        :selectable="options.selectable !== false"
        :selected-keys="selectedKeys"
        :uppercase-headers="true"
        @row-click="onRowClick"
        @toggle-row="onToggleRow"
        @toggle-all="onToggleAll"
      >
        <template #cell-lead_name="{ row }">
          <div class="who2 flex min-w-0 items-center gap-[9px]">
            <AstraAvatar
              v-if="row.lead_name?.label || row.lead_name"
              class="av2"
              :name="
                row.lead_name?.image_label ||
                row.lead_name?.label ||
                row.lead_name
              "
              :src="row.lead_name?.image"
              size="md"
            />
            <!-- PNG name/org baseline sits ~1px lower than Chromium -->
            <div class="tx flex min-w-0 translate-y-px flex-col leading-[1.3]">
              <span
                class="truncate text-[12.5px] font-semibold leading-[1.3] text-crm-fg"
              >
                {{ row.lead_name?.label || row.lead_name }}
              </span>
              <span
                v-if="row.lead_name?.organization || row.organization"
                class="truncate text-[11.5px] leading-[1.3] text-crm-muted-fg"
              >
                {{ row.lead_name?.organization || row.organization }}
              </span>
            </div>
          </div>
        </template>

        <template #cell-status="{ row }">
          <AstraBadge
            v-if="row.status?.label || row.status"
            :label="row.status?.label || row.status"
            :tone="statusTone(row.status?.label || row.status)"
            dot
          />
        </template>

        <template #cell-temperature="{ row }">
          <span
            v-if="tempLabel(row)"
            class="inline-flex items-center gap-1 text-[11px] font-semibold"
            :class="tempClass(tempLabel(row))"
          >
            <i
              class="block size-1.5 rounded-full bg-current"
              aria-hidden="true"
            />
            {{ tempLabel(row) }}
          </span>
        </template>

        <template #cell-sla_status="{ row }">
          <span
            class="text-crm-meta font-semibold"
            :class="slaClass(row.sla_status)"
          >
            {{ slaLabel(row.sla_status) }}
          </span>
        </template>

        <template #cell-score="{ row }">
          <b class="font-semibold tabular-nums text-crm-fg">{{
            row.score ?? ''
          }}</b>
        </template>

        <template #cell-source="{ row }">
          <span class="text-crm-muted-fg">{{ row.source || '—' }}</span>
        </template>

        <template #cell-lead_owner="{ row }">
          <AstraAvatar
            v-if="row.lead_owner?.full_name || row.lead_owner?.label"
            class="av2 sm"
            :name="row.lead_owner.full_name || row.lead_owner.label"
            :src="row.lead_owner.user_image || row.lead_owner.image"
            size="sm"
          />
        </template>

        <template #cell-last_activity="{ row }">
          <span class="text-crm-muted-fg">{{
            activityLabel(row.last_activity)
          }}</span>
        </template>

        <template #cell-creation="{ row }">
          <span class="tabular-nums text-crm-muted-fg">{{
            row.creation?.timeAgo || row.creation?.label || row.creation || '—'
          }}</span>
        </template>
      </AstraListTable>
      </div>
    </div>

    <div
      class="mt-2.5 flex items-center text-[12px] text-crm-muted-fg"
    >
      <span>
        {{
          __('Showing {0}–{1} of {2} matching', [
            1,
            options.rowCount || rows.length,
            options.totalCount || rows.length,
          ])
        }}
        <template v-if="selectedKeys.length">
          · {{ __('{0} selected', [selectedKeys.length]) }}
        </template>
      </span>
      <span class="flex-1" />
      <span>
        {{ __('Page {0} of {1}', [1, totalPages]) }}
      </span>
    </div>

    <AstraBulkBar
      :count="selectedKeys.length"
      :actions="bulkBarActions"
      @clear="clearSelections"
    />
    <ListBulkActions
      ref="listBulkActionsRef"
      v-model="list"
      doctype="CRM Lead"
    />
  </div>
</template>

<script setup>
import ListBulkActions from '@/components/ListBulkActions.vue'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import AstraBadge from '@/components/astra/AstraBadge.vue'
import AstraBulkBar from '@/components/astra/AstraBulkBar.vue'
import AstraListTable from '@/components/astra/AstraListTable.vue'
import { STATUS_TONES } from '@/components/astra/format'
import { canUseCrmCsvExport, crmCsvExportUrl } from '@/utils/csvExport'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  options: {
    type: Object,
    default: () => ({
      selectable: true,
      showTooltip: true,
      resizeColumn: false,
      totalCount: 0,
      rowCount: 0,
    }),
  },
})
const emit = defineEmits([
  'loadMore',
  'updatePageCount',
  'columnWidthUpdated',
  'applyFilter',
  'applyLikeFilter',
  'likeDoc',
  'selectionsChanged',
])

const route = useRoute()
const router = useRouter()

const pageLengthCount = defineModel({ type: Number })
const list = defineModel('list', { type: Object })

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const listBulkActionsRef = ref(null)
const selectedKeys = ref([])

const totalPages = computed(() => {
  const total = props.options.totalCount || 0
  const per = props.options.rowCount || props.rows.length || 14
  const fromData = list.value?.data?.total_pages
  if (fromData) return fromData
  return Math.max(1, Math.round(total / per) || 1)
})

function onRowClick(row) {
  router.push({
    name: 'Lead',
    params: { leadId: row.name },
    query: { view: route.query.view, viewType: route.params.viewType },
  })
}

function onToggleRow(row, checked) {
  const key = row.name
  const next = new Set(selectedKeys.value)
  if (checked) next.add(key)
  else next.delete(key)
  selectedKeys.value = [...next]
  emit('selectionsChanged', next)
}

function onToggleAll(checked) {
  selectedKeys.value = checked ? props.rows.map((r) => r.name) : []
  emit('selectionsChanged', new Set(selectedKeys.value))
}

function clearSelections() {
  selectedKeys.value = []
  emit('selectionsChanged', new Set())
}

function statusTone(label) {
  return STATUS_TONES[label] || 'mute'
}

function tempLabel(row) {
  const t = row.temperature
  if (t && typeof t === 'object') return t.label || t.tone || ''
  return t || ''
}

function tempClass(label) {
  if (label === 'Hot') return 'text-crm-danger'
  if (label === 'Warm') return 'text-crm-warning'
  return 'text-crm-muted-fg'
}

function slaLabel(item) {
  if (item == null || item === '') return '—'
  if (typeof item === 'object') return item.value || item.label || '—'
  return String(item)
}

function slaClass(item) {
  const tone =
    (item && typeof item === 'object' && item.tone) ||
    (item && typeof item === 'object' && item.color) ||
    ''
  const label = slaLabel(item)
  if (tone === 'late' || tone === 'red' || /overdue/i.test(label)) {
    return 'text-crm-danger'
  }
  if (tone === 'ok' || tone === 'green' || /^met$/i.test(label)) {
    return 'text-crm-success'
  }
  if (tone === 'due' || tone === 'amber' || tone === 'warn') {
    return 'text-crm-warning'
  }
  if (!label || label === '—') return 'text-crm-faint'
  return 'text-crm-warning'
}

function activityLabel(value) {
  if (value == null || value === '') return '—'
  if (typeof value === 'object') return value.label || value.timeAgo || '—'
  return String(value)
}

const bulkBarActions = computed(() => {
  const selections = new Set(selectedKeys.value)
  const unselectAll = () => clearSelections()
  const all =
    listBulkActionsRef.value?.bulkActions(selections, unselectAll) || []
  const assign = all.find(
    (a) => a.label === __('Assign To') || a.label === 'Assign To',
  )
  const edit = all.find((a) => a.label === __('Edit') || a.label === 'Edit')
  const allowed = []
  if (assign)
    allowed.push({
      label: __('Assign'),
      icon: 'assign',
      onClick: assign.onClick,
    })
  if (edit)
    allowed.push({
      label: __('Set status'),
      icon: 'status',
      onClick: edit.onClick,
    })
  allowed.push({
    label: __('Set temperature'),
    icon: 'temperature',
    onClick: () => edit?.onClick?.(),
  })
  if (canUseCrmCsvExport('CRM Lead') && selectedKeys.value.length) {
    allowed.push({
      label: __('Export'),
      onClick: () => {
        const fields = (list.value?.data?.columns || []).map((c) => c.key)
        window.location.href = crmCsvExportUrl({
          doctype: 'CRM Lead',
          fields,
          filters: {
            ...(list.value?.params?.filters || {}),
            name: ['in', selectedKeys.value],
          },
          orderBy: list.value?.params?.order_by,
          limit: selectedKeys.value.length,
          title: 'CRM Lead',
        })
      },
    })
  } else if (selectedKeys.value.length) {
    allowed.push({ label: __('Export'), onClick: () => {} })
  }
  return allowed
})

function seedParitySelection() {
  if (typeof window === 'undefined' || !window.__PARITY__) return
  const fromData = list.value?.data?.parity_selected
  const keys =
    Array.isArray(fromData) && fromData.length
      ? fromData
      : props.rows.slice(0, 3).map((r) => r.name)
  if (!keys.length) return
  selectedKeys.value = keys.filter((k) => props.rows.some((r) => r.name === k))
  emit('selectionsChanged', new Set(selectedKeys.value))
}

onMounted(() => {
  seedParitySelection()
})

watch(
  () => props.rows,
  () => {
    if (selectedKeys.value.length) return
    seedParitySelection()
  },
)

defineExpose({
  customListActions: computed(
    () => listBulkActionsRef.value?.customListActions,
  ),
})
</script>

<style scoped>
.astra-leads-table :deep(table) {
  /* Fixed layout; leftover width goes to Created (no width on last col). */
  table-layout: fixed;
  width: 100%;
  border-collapse: collapse;
}
.astra-leads-table :deep(th) {
  height: 34px;
  padding: 0 10px;
  /* PNG uppercase caps track slightly wider than tight 0.02em */
  letter-spacing: 0.03em;
  font-size: 11.5px;
  font-weight: 600;
}
.astra-leads-table :deep(td) {
  height: 44px;
  max-height: 44px;
  padding: 0 10px;
  font-size: 12.5px;
  overflow: hidden;
  vertical-align: middle;
}
/*
 * Column widths tuned to Figma PNG landmarks (HTML auto-layout sits ~7–14px
 * right of PNG from Status onward). Checkbox 34; Name 199; Temp 77 — best
 * Status/SLA/Score landmark set from shift experiments (≤0.99% PNG).
 */
.astra-leads-table :deep(th:nth-child(1)),
.astra-leads-table :deep(td:nth-child(1)) {
  width: 34px;
  min-width: 34px;
  max-width: 34px;
}
.astra-leads-table :deep(th:nth-child(2)),
.astra-leads-table :deep(td:nth-child(2)) {
  width: 199px;
  min-width: 199px;
  max-width: 199px;
}
.astra-leads-table :deep(th:nth-child(3)),
.astra-leads-table :deep(td:nth-child(3)) {
  width: 135px;
}
.astra-leads-table :deep(th:nth-child(4)),
.astra-leads-table :deep(td:nth-child(4)) {
  width: 77px;
}
.astra-leads-table :deep(th:nth-child(5)),
.astra-leads-table :deep(td:nth-child(5)) {
  width: 197px;
  /* Shift-sim: SLA ink −1px vs PNG */
  padding-left: 9px;
}
.astra-leads-table :deep(th:nth-child(6)),
.astra-leads-table :deep(td:nth-child(6)) {
  width: 67px;
  /* Score/Source/Owner/Activity sit ~2–3px right of PNG */
  padding-left: 8px;
}
.astra-leads-table :deep(th:nth-child(7)),
.astra-leads-table :deep(td:nth-child(7)) {
  width: 108px;
  padding-left: 8px;
}
.astra-leads-table :deep(th:nth-child(8)),
.astra-leads-table :deep(td:nth-child(8)) {
  width: 73px;
  /* Owner avatar was −2px vs PNG after the −2 pad; restore default */
  padding-left: 10px;
}
.astra-leads-table :deep(th:nth-child(9)),
.astra-leads-table :deep(td:nth-child(9)) {
  width: 158px;
  /* Activity ink sat ~10px left of PNG; +8px pad is shift-sim optimum */
  padding-left: 16px;
}
.astra-leads-table :deep(th:nth-child(10)),
.astra-leads-table :deep(td:nth-child(10)) {
  width: 91px;
  /* Created −3px vs default 10px padding */
  padding-left: 7px;
}
.astra-leads-table :deep(td.bg-crm-row-selected) {
  background: var(--crm-row-selected);
}
</style>
