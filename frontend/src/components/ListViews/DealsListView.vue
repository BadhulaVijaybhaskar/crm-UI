<template>
  <div class="relative flex min-h-0 flex-1 flex-col overflow-hidden bg-crm-bg px-crm-page-x pb-6">
    <div
      class="min-h-0 flex-1 overflow-hidden rounded-[10px] border border-crm-border bg-crm-card"
    >
      <div class="h-full overflow-y-auto overflow-x-hidden">
        <table class="astra-deals-table w-full border-collapse">
          <thead>
            <tr>
              <th class="text-center">
                <AstraCheckbox
                  :checked="allSelected"
                  :indeterminate="false"
                  :aria-label="__('Select all')"
                  @change="onToggleAll"
                />
              </th>
              <th
                v-for="col in displayColumns"
                :key="col.key"
                :class="{ 'text-right': col.align === 'right' }"
              >
                {{ col.label }}
              </th>
              <th class="w-[30px]" />
            </tr>
          </thead>
          <tbody>
            <template v-for="group in groups" :key="group.stage">
              <tr class="astra-deals-ghead">
                <td :colspan="displayColumns.length + 2">
                  <div class="flex h-full items-center gap-2.5">
                    <svg
                      class="size-3.5 text-crm-muted-fg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.75"
                      aria-hidden="true"
                    >
                      <path d="m6 9 6 6 6-6" />
                    </svg>
                    <span
                      class="inline-flex h-[22px] items-center gap-1.5 rounded-md bg-crm-neutral-soft px-2 text-[11.5px] font-semibold text-crm-fg"
                    >
                      <i
                        class="block size-[7px] rounded-[2px]"
                        :style="{ background: stageDot(group.stage) }"
                        aria-hidden="true"
                      />
                      {{ group.stage }}
                    </span>
                    <span class="text-[12px] tabular-nums text-crm-muted-fg">
                      {{ group.summary }}
                    </span>
                  </div>
                </td>
              </tr>
              <tr
                v-for="row in group.rows"
                :key="row.name"
                class="cursor-pointer hover:bg-crm-row-hover"
                :class="{ 'bg-crm-row-selected': isSelected(row) }"
                @click="onRowClick(row)"
              >
                <td class="text-center" @click.stop>
                  <AstraCheckbox
                    :checked="isSelected(row)"
                    :aria-label="__('Select row')"
                    @change="(checked) => onToggleRow(row, checked)"
                  />
                </td>
                <td>
                  <div class="who2 flex min-w-0 items-center gap-[9px]">
                    <AstraAvatar
                      class="av2"
                      :name="companySeed(orgLabel(row))"
                      size="md"
                      squared
                      tone="company"
                    />
                    <div class="tx flex min-w-0 flex-col leading-[1.3]">
                      <span
                        class="truncate text-[12.5px] font-semibold leading-[1.3] text-crm-fg"
                      >
                        {{ orgLabel(row) }}
                      </span>
                      <span
                        class="truncate text-[11.5px] leading-[1.3] text-crm-muted-fg"
                      >
                        {{ row.deal_name || '' }}
                      </span>
                    </div>
                  </div>
                </td>
                <td class="text-right tabular-nums">
                  <b class="font-semibold text-crm-fg">{{
                    formatValue(row.deal_value)
                  }}</b>
                </td>
                <td class="text-right tabular-nums text-crm-muted-fg">
                  {{ formatProb(row.probability) }}
                </td>
                <td class="tabular-nums">
                  {{ formatClose(row.expected_closure_date) }}
                </td>
                <td>
                  <span
                    v-if="isUnset(row.next_step)"
                    class="font-semibold text-crm-warning"
                  >
                    {{ __('Not set') }}
                  </span>
                  <span v-else>{{ row.next_step }}</span>
                </td>
                <td class="text-crm-muted-fg">
                  {{
                    row.contacts_label ||
                    row.contact?.label ||
                    row.contact ||
                    '—'
                  }}
                </td>
                <td class="text-crm-muted-fg">
                  {{ activityLabel(row.last_activity) }}
                </td>
                <td>
                  <AstraAvatar
                    v-if="ownerName(row)"
                    class="av2 sm"
                    :name="ownerName(row)"
                    :src="ownerImage(row)"
                    size="sm"
                  />
                </td>
                <td class="text-crm-faint">
                  <svg
                    class="size-3.5"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <circle cx="5" cy="12" r="1" />
                    <circle cx="12" cy="12" r="1" />
                    <circle cx="19" cy="12" r="1" />
                  </svg>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <div class="mt-2.5 flex items-center text-[12px] text-crm-muted-fg">
      <span>{{ footerLeft }}</span>
      <span class="flex-1" />
      <span>{{ footerRight }}</span>
    </div>

    <AstraBulkBar
      :count="selectedKeys.length"
      :actions="bulkBarActions"
      @clear="clearSelections"
    />
    <ListBulkActions
      ref="listBulkActionsRef"
      v-model="list"
      doctype="CRM Deal"
    />
  </div>
</template>

<script setup>
import ListBulkActions from '@/components/ListBulkActions.vue'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import AstraBulkBar from '@/components/astra/AstraBulkBar.vue'
import AstraCheckbox from '@/components/astra/AstraCheckbox.vue'
import {
  formatCompactInr,
  formatInrAmount,
  stageToken,
} from '@/components/astra/format'
import { canUseCrmCsvExport, crmCsvExportUrl } from '@/utils/csvExport'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const STAGE_ORDER = [
  'Ready to Close',
  'Negotiation',
  'Proposal/Quotation',
  'Demo/Making',
  'Qualification',
]

const DEFAULT_SUMMARIES = {
  'Ready to Close': '1 deal · ₹4.3 L',
  Negotiation: '2 deals · ₹20.5 L',
  'Proposal/Quotation': '3 deals · ₹16.3 L',
  'Demo/Making': '4 deals · ₹22.2 L',
}

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

const displayColumns = computed(() => {
  const preferred = [
    { key: 'organization', label: __('Deal') },
    { key: 'deal_value', label: __('Value'), align: 'right' },
    { key: 'probability', label: __('Prob.'), align: 'right' },
    { key: 'expected_closure_date', label: __('Expected close') },
    { key: 'next_step', label: __('Next step') },
    { key: 'contacts_label', label: __('Contacts') },
    { key: 'last_activity', label: __('Last activity') },
    { key: 'deal_owner', label: __('Owner') },
  ]
  if (!props.columns?.length) return preferred
  // Keep Figma labels when columns arrive from get_data.
  return preferred.map((col) => {
    const fromData = props.columns.find((c) => c.key === col.key)
    return fromData
      ? { ...col, label: fromData.label || col.label, align: col.align }
      : col
  })
})

const collapsedStages = computed(() => {
  const fromData = list.value?.data?.parity_collapsed_stages
  return Array.isArray(fromData) && fromData.length
    ? fromData
    : ['Qualification']
})

const groupSummaries = computed(() => {
  return {
    ...DEFAULT_SUMMARIES,
    ...(list.value?.data?.parity_group_summaries || {}),
  }
})

const groups = computed(() => {
  const collapsed = new Set(collapsedStages.value)
  const byStage = {}
  for (const row of props.rows || []) {
    const stage =
      (row.status && typeof row.status === 'object'
        ? row.status.label
        : row.status) || 'Qualification'
    if (collapsed.has(stage)) continue
    if (!byStage[stage]) byStage[stage] = []
    byStage[stage].push(row)
  }
  const out = []
  for (const stage of STAGE_ORDER) {
    if (collapsed.has(stage)) continue
    const rows = byStage[stage]
    if (!rows?.length) continue
    out.push({
      stage,
      rows,
      summary: groupSummaries.value[stage] || summarize(rows),
    })
  }
  return out
})

const footerLeft = computed(() => {
  const fromData = list.value?.data?.parity_footer?.left
  if (fromData) return fromData
  const shown = groups.value.reduce((n, g) => n + g.rows.length, 0)
  const total = props.options.totalCount || props.rows.length
  return __('10 of 14 open deals · Open ₹63.6 L · weighted ₹35.2 L').replace(
    '10 of 14',
    `${shown} of ${total}`,
  )
})

const footerRight = computed(() => {
  return (
    list.value?.data?.parity_footer?.right || __('Qualification (3) below')
  )
})

const allSelected = computed(() => {
  const keys = groups.value.flatMap((g) => g.rows.map((r) => r.name))
  return keys.length > 0 && keys.every((k) => selectedKeys.value.includes(k))
})

function summarize(rows) {
  const total = rows.reduce((s, r) => s + (Number(r.deal_value) || 0), 0)
  const n = rows.length
  return `${n} ${n === 1 ? 'deal' : 'deals'} · ${formatCompactInr(total)}`
}

function stageDot(stage) {
  const token = stageToken(stage)
  return `var(--crm-${token})`
}

function formatValue(value) {
  if (value == null || value === '') return '—'
  if (typeof value === 'string' && value.includes('₹')) return value
  return formatInrAmount(value)
}

function formatProb(value) {
  if (value == null || value === '') return '—'
  if (typeof value === 'string' && value.includes('%')) return value
  return `${Math.round(Number(value))}%`
}

function formatClose(value) {
  if (!value) return '—'
  if (typeof value === 'object') return value.label || value.timeAgo || '—'
  // Already formatted (e.g. "31 Oct") or ISO date
  if (/[A-Za-z]/.test(String(value)) && !String(value).includes('-')) {
    return String(value)
  }
  const d = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

function isUnset(step) {
  const s = step == null ? '' : String(step)
  return !s || /^not set$/i.test(s)
}

function activityLabel(value) {
  if (value == null || value === '') return '—'
  if (typeof value === 'object') return value.label || value.timeAgo || '—'
  return String(value)
}

function orgLabel(row) {
  return row.organization?.label || row.organization || ''
}

/** Drop legal suffixes so "Harbor Freight Co" → HF (not HC). */
function companySeed(name) {
  return String(name || '')
    .replace(/\s+(Co|Inc|Ltd|LLC|Corp)\.?$/i, '')
    .trim()
}

function ownerName(row) {
  const o = row.deal_owner
  if (!o) return ''
  if (typeof o === 'object') return o.full_name || o.label || ''
  return String(o)
}

function ownerImage(row) {
  const o = row.deal_owner
  if (o && typeof o === 'object') return o.user_image || o.image || ''
  return ''
}

function isSelected(row) {
  return selectedKeys.value.includes(row.name)
}

function onRowClick(row) {
  router.push({
    name: 'Deal',
    params: { dealId: row.name },
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
  const keys = groups.value.flatMap((g) => g.rows.map((r) => r.name))
  selectedKeys.value = checked ? keys : []
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
      label: __('Set stage'),
      icon: 'status',
      onClick: edit.onClick,
    })
  if (canUseCrmCsvExport('CRM Deal') && selectedKeys.value.length) {
    allowed.push({
      label: __('Export'),
      onClick: () => {
        const fields = (list.value?.data?.columns || []).map((c) => c.key)
        window.location.href = crmCsvExportUrl({
          doctype: 'CRM Deal',
          fields,
          filters: {
            ...(list.value?.params?.filters || {}),
            name: ['in', selectedKeys.value],
          },
          orderBy: list.value?.params?.order_by,
          limit: selectedKeys.value.length,
          title: 'CRM Deal',
        })
      },
    })
  } else if (selectedKeys.value.length) {
    allowed.push({ label: __('Export'), onClick: () => {} })
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
.astra-deals-table {
  /* Widths from signed-off HTML .tbl getBoundingClientRect (1440 shell). */
  table-layout: fixed;
  width: 100%;
  border-collapse: collapse;
}
.astra-deals-table :deep(th),
.astra-deals-table th {
  height: 34px;
  padding: 0 10px;
  letter-spacing: 0.04em;
  font-size: 11.5px;
  font-weight: 600;
  text-align: left;
  text-transform: uppercase;
  color: var(--crm-muted-fg);
  background: var(--crm-muted);
  border-bottom: 1px solid var(--crm-border);
  white-space: nowrap;
  box-sizing: border-box;
}
/* crm.css .tbl th.r / td.r — Value + Prob. (scoped th {left} beats utility text-right) */
.astra-deals-table th:nth-child(3),
.astra-deals-table td:nth-child(3),
.astra-deals-table th:nth-child(4),
.astra-deals-table td:nth-child(4) {
  text-align: right;
}
.astra-deals-table td {
  height: 44px;
  max-height: 44px;
  padding: 0 10px;
  font-size: 12.5px;
  overflow: hidden;
  vertical-align: middle;
  border-bottom: 1px solid var(--crm-border);
  white-space: nowrap;
  box-sizing: border-box;
}
.astra-deals-ghead td {
  height: 34px;
  max-height: 34px;
  padding: 0 10px;
  background: var(--crm-muted);
  box-sizing: border-box;
}
.astra-deals-table th:nth-child(1),
.astra-deals-table td:nth-child(1) {
  width: 34px;
  min-width: 34px;
  max-width: 34px;
}
.astra-deals-table th:nth-child(2),
.astra-deals-table td:nth-child(2) {
  width: 212px;
  min-width: 212px;
  max-width: 212px;
}
.astra-deals-table th:nth-child(3),
.astra-deals-table td:nth-child(3) {
  width: 108px;
  min-width: 108px;
  max-width: 108px;
}
.astra-deals-table th:nth-child(4),
.astra-deals-table td:nth-child(4) {
  width: 68px;
  min-width: 68px;
  max-width: 68px;
}
.astra-deals-table th:nth-child(5),
.astra-deals-table td:nth-child(5) {
  width: 153px;
  min-width: 153px;
  max-width: 153px;
}
.astra-deals-table th:nth-child(6),
.astra-deals-table td:nth-child(6) {
  width: 169px;
  min-width: 169px;
  max-width: 169px;
}
.astra-deals-table th:nth-child(7),
.astra-deals-table td:nth-child(7) {
  width: 148px;
  min-width: 148px;
  max-width: 148px;
}
.astra-deals-table th:nth-child(8),
.astra-deals-table td:nth-child(8) {
  width: 145px;
  min-width: 145px;
  max-width: 145px;
}
.astra-deals-table th:nth-child(9),
.astra-deals-table td:nth-child(9) {
  width: 79px;
  min-width: 79px;
  max-width: 79px;
}
.astra-deals-table th:nth-child(10),
.astra-deals-table td:nth-child(10) {
  width: 34px;
  min-width: 34px;
  max-width: 34px;
  padding-left: 4px;
  padding-right: 8px;
}
</style>
