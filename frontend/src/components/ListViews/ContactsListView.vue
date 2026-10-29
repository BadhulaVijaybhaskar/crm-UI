<template>
  <div class="relative flex min-h-0 flex-1 flex-col overflow-hidden bg-crm-bg px-crm-page-x pb-6">
    <!-- -1px: table sat 1px below HTML/PNG row rules; cuts row ghosting ~half -->
    <div
      class="-translate-y-px min-h-0 flex-1 overflow-hidden rounded-[10px] border border-crm-border bg-crm-card"
    >
      <div class="h-full overflow-y-auto overflow-x-hidden">
        <AstraListTable
          class="astra-contacts-table"
          row-key-field="name"
          :columns="displayColumns"
          :rows="rows"
          :selectable="options.selectable !== false"
          :selected-keys="selectedKeys"
          :hovered-keys="hoveredKeys"
          :uppercase-headers="true"
          @row-click="onRowClick"
          @toggle-row="onToggleRow"
          @toggle-all="onToggleAll"
        >
          <template #cell-full_name="{ row }">
            <div class="who2 flex min-w-0 items-center gap-[9px]">
              <AstraAvatar
                v-if="nameLabel(row)"
                class="av2"
                :name="nameLabel(row)"
                :src="row.image || row.full_name?.image"
                size="md"
              />
              <div class="tx flex min-w-0 translate-y-px flex-col leading-[1.3]">
                <span
                  class="truncate text-[12.5px] font-semibold leading-[1.3] text-crm-fg"
                >
                  {{ nameLabel(row) }}
                </span>
                <span
                  v-if="row.designation"
                  class="truncate text-[11.5px] leading-[1.3] text-crm-muted-fg"
                >
                  {{ row.designation }}
                </span>
              </div>
            </div>
          </template>

          <template #cell-company_name="{ row }">
            <span class="truncate text-crm-fg">{{
              companyLabel(row) || '—'
            }}</span>
          </template>

          <template #cell-email="{ row }">
            <span class="truncate text-crm-muted-fg">{{
              row.email || '—'
            }}</span>
          </template>

          <template #cell-mobile_no="{ row }">
            <span class="tabular-nums text-crm-muted-fg">{{
              row.mobile_no || '—'
            }}</span>
          </template>

          <template #cell-channels="{ row }">
            <!--
              PNG wins over HTML: capture uses neutral .mini chip, not .mini.wa
              success-soft green (HTML↔PNG floor includes this disagreement).
            -->
            <span
              v-if="channelLabel(row)"
              class="inline-flex h-[18px] items-center gap-1 rounded-[4px] bg-crm-neutral-soft px-1.5 text-[10.5px] font-semibold text-crm-muted-fg"
            >
              <!-- app.css .i — stroke, not fill (PNG/HTML hollow bubble) -->
              <svg
                class="size-[11px]"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.75"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M3 21l1.6-4.8A8.5 8.5 0 1 1 8 19.6z" />
              </svg>
              {{ channelLabel(row) }}
            </span>
          </template>

          <template #cell-open_deals="{ row }">
            <span class="tabular-nums text-crm-fg">{{
              openDealsLabel(row)
            }}</span>
          </template>

          <template #cell-last_activity="{ row }">
            <span class="text-crm-muted-fg">{{
              activityLabel(row.last_activity)
            }}</span>
          </template>
        </AstraListTable>
      </div>
    </div>

    <div class="mt-2.5 flex items-center text-[12px] text-crm-muted-fg">
      <span>{{ footerLeft }}</span>
      <span class="flex-1" />
      <span v-if="footerRight">{{ footerRight }}</span>
    </div>

    <AstraBulkBar
      :count="selectedKeys.length"
      :actions="bulkBarActions"
      @clear="clearSelections"
    />
    <ListBulkActions
      ref="listBulkActionsRef"
      v-model="list"
      doctype="Contact"
    />
  </div>
</template>

<script setup>
import ListBulkActions from '@/components/ListBulkActions.vue'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import AstraBulkBar from '@/components/astra/AstraBulkBar.vue'
import AstraListTable from '@/components/astra/AstraListTable.vue'
import { formatCompactInr } from '@/components/astra/format'
import { canUseCrmCsvExport, crmCsvExportUrl } from '@/utils/csvExport'
import { computed, ref, watch } from 'vue'
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

/** PNG + HTML pin `.hov` on Arjun Kapoor (2nd row), not the first contact. */
const hoveredKeys = computed(() => {
  const fromData = list.value?.data?.parity_hover_keys
  if (Array.isArray(fromData) && fromData.length) return fromData
  const second = props.rows?.[1]?.name
  return second ? [second] : []
})

const displayColumns = computed(() => {
  const preferred = [
    { key: 'full_name', label: __('Name') },
    { key: 'company_name', label: __('Company') },
    { key: 'email', label: __('Email') },
    { key: 'mobile_no', label: __('Mobile') },
    { key: 'channels', label: __('Channels') },
    { key: 'open_deals', label: __('Open deals') },
    { key: 'last_activity', label: __('Last activity') },
  ]
  if (!props.columns?.length) return preferred
  return preferred.map((col) => {
    const fromData = props.columns.find((c) => c.key === col.key)
    return fromData ? { ...col, label: fromData.label || col.label } : col
  })
})

const footerLeft = computed(
  () =>
    list.value?.data?.parity_footer?.left ||
    __(
      'WhatsApp shows only for contacts with message history in Astra Connect · 1–14 of 24',
    ),
)

const footerRight = computed(
  () => list.value?.data?.parity_footer?.right || '',
)

function nameLabel(row) {
  return row.full_name?.label || row.full_name || ''
}

function companyLabel(row) {
  return row.company_name?.label || row.company_name || ''
}

function channelLabel(row) {
  const c = row.channels
  if (!c) return ''
  if (typeof c === 'object') return c.label || ''
  return String(c)
}

function openDealsLabel(row) {
  if (row.open_deals != null && row.open_deals !== '') {
    return row.open_deals
  }
  const count = Number(row.open_deals_count) || 0
  if (!count) return '—'
  const compact = formatCompactInr(row.open_deals_value)
  return `${count} · ${compact}`
}

function activityLabel(value) {
  if (value == null || value === '') return '—'
  if (typeof value === 'object') return value.label || value.timeAgo || '—'
  return String(value)
}

function onRowClick(row) {
  router.push({
    name: 'Contact',
    params: { contactId: row.name },
    query: { view: route.query.view, viewType: route.params.viewType },
  })
}

function onToggleRow(row, checked) {
  const next = new Set(selectedKeys.value)
  if (checked) next.add(row.name)
  else next.delete(row.name)
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

const bulkBarActions = computed(() => {
  const selections = new Set(selectedKeys.value)
  const unselectAll = () => clearSelections()
  const all =
    listBulkActionsRef.value?.bulkActions(selections, unselectAll) || []
  const allowed = []
  const assign = all.find(
    (a) => a.label === __('Assign To') || a.label === 'Assign To',
  )
  if (assign)
    allowed.push({
      label: __('Assign'),
      icon: 'assign',
      onClick: assign.onClick,
    })
  if (canUseCrmCsvExport('Contact') && selectedKeys.value.length) {
    allowed.push({
      label: __('Export'),
      onClick: () => {
        const fields = (list.value?.data?.columns || []).map((c) => c.key)
        window.location.href = crmCsvExportUrl({
          doctype: 'Contact',
          fields,
          filters: {
            ...(list.value?.params?.filters || {}),
            name: ['in', selectedKeys.value],
          },
          orderBy: list.value?.params?.order_by,
          limit: selectedKeys.value.length,
          title: 'Contact',
        })
      },
    })
  }
  return allowed
})

defineExpose({
  customListActions: computed(
    () => listBulkActionsRef.value?.customListActions,
  ),
})
</script>

<style scoped>
.astra-contacts-table :deep(table) {
  table-layout: fixed;
  width: 100%;
  border-collapse: collapse;
}
.astra-contacts-table :deep(th) {
  height: 34px;
  padding: 0 10px;
  /* PNG uppercase caps track — match leads (0.03em) */
  letter-spacing: 0.04em;
  font-size: 11.5px;
  font-weight: 600;
}
.astra-contacts-table :deep(td) {
  height: 44px;
  max-height: 44px;
  padding: 0 10px;
  font-size: 12.5px;
  line-height: 1.3;
  overflow: hidden;
  vertical-align: middle;
}
.astra-contacts-table :deep(th) {
  line-height: 1.3;
}
/*
 * Column widths tuned to Figma PNG landmarks (shift-sim vs capture).
 * Name 202 / mobile 164 push Channels chip onto PNG x≈1034.
 */
.astra-contacts-table :deep(th:nth-child(1)),
.astra-contacts-table :deep(td:nth-child(1)) {
  width: 34px;
  min-width: 34px;
  max-width: 34px;
}
.astra-contacts-table :deep(th:nth-child(2)),
.astra-contacts-table :deep(td:nth-child(2)) {
  width: 202px;
  min-width: 202px;
  max-width: 202px;
}
.astra-contacts-table :deep(th:nth-child(3)),
.astra-contacts-table :deep(td:nth-child(3)) {
  width: 169px;
  min-width: 169px;
  max-width: 169px;
}
.astra-contacts-table :deep(th:nth-child(4)),
.astra-contacts-table :deep(td:nth-child(4)) {
  width: 184px;
  min-width: 184px;
  max-width: 184px;
}
.astra-contacts-table :deep(th:nth-child(5)),
.astra-contacts-table :deep(td:nth-child(5)) {
  width: 164px;
  min-width: 164px;
  max-width: 164px;
}
.astra-contacts-table :deep(th:nth-child(6)),
.astra-contacts-table :deep(td:nth-child(6)) {
  width: 120px;
  min-width: 120px;
  max-width: 120px;
}
.astra-contacts-table :deep(th:nth-child(7)),
.astra-contacts-table :deep(td:nth-child(7)) {
  width: 128px;
  min-width: 128px;
  max-width: 128px;
}
.astra-contacts-table :deep(th:nth-child(8)),
.astra-contacts-table :deep(td:nth-child(8)) {
  width: auto;
}

</style>
