<template>
  <div class="relative flex min-h-0 flex-1 flex-col overflow-hidden bg-crm-bg px-crm-page-x pb-6 pt-2.5">
    <div
      class="min-h-0 flex-1 overflow-hidden rounded-[10px] border border-crm-border bg-crm-card"
    >
      <div class="h-full overflow-auto">
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
          <div class="flex min-w-0 items-center gap-[9px]">
            <AstraAvatar
              v-if="row.lead_name?.label || row.lead_name"
              :name="
                row.lead_name?.image_label ||
                row.lead_name?.label ||
                row.lead_name
              "
              :src="row.lead_name?.image"
              size="md"
            />
            <div class="flex min-w-0 flex-col leading-[1.3]">
              <span class="truncate text-crm-label font-semibold text-crm-fg">
                {{ row.lead_name?.label || row.lead_name }}
              </span>
              <span
                v-if="row.lead_name?.organization || row.organization"
                class="truncate text-crm-meta text-crm-muted-fg"
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
  if (assign) allowed.push({ label: __('Assign'), onClick: assign.onClick })
  if (edit) allowed.push({ label: __('Set status'), onClick: edit.onClick })
  allowed.push({
    label: __('Set temperature'),
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
  border-collapse: collapse;
}
.astra-leads-table :deep(th) {
  height: 34px;
  padding: 0 10px;
  letter-spacing: 0.06em;
  font-size: 11px;
}
.astra-leads-table :deep(td) {
  height: 44px;
  max-height: 44px;
  padding: 0 10px;
  font-size: 12.5px;
  overflow: hidden;
  vertical-align: middle;
}
.astra-leads-table :deep(tr.bg-crm-row-selected),
.astra-leads-table :deep(tr[class*='bg-crm-row-selected']) {
  background: var(--crm-row-selected);
}
</style>
