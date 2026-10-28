<template>
  <RecordsListChrome
    :title="__('Deals')"
    :description="__('Your deals · drag a card to change its stage.')"
    :create-label="__('+ New deal')"
    :view-tabs="viewTabs"
    :active-view="activeView"
    :show-save-view="true"
    :show-view-switch="true"
    :view-type="viewType === 'kanban' ? 'kanban' : 'list'"
    :filter-chips="filterChips"
    :show-filter-bar="filterChips.length > 0"
    @create="showDealModal = true"
    @select-view="selectView"
    @save-view="saveView"
    @set-view-type="setViewType"
    @remove-filter="removeFilterChip"
  >
    <template #actions>
      <CustomActions
        v-if="dealsListView?.customListActions"
        :actions="dealsListView.customListActions"
      />
      <AstraButton
        variant="primary"
        :label="__('+ New deal')"
        @click="showDealModal = true"
      />
    </template>
    <div
      class="astra-records-vc flex flex-wrap items-center justify-between gap-2 border-b border-crm-border bg-crm-card px-crm-page-x py-2.5"
    >
      <ViewControls
        ref="viewControls"
        v-model="deals"
        v-model:loadMore="loadMore"
        v-model:resizeColumn="triggerResize"
        v-model:updatedPageCount="updatedPageCount"
        doctype="CRM Deal"
        :options="{
          allowedViews: ['list', 'group_by', 'kanban'],
          groupSummary: true,
          groupByExclude: ['naming_series', 'docstatus'],
        }"
      />
      <div
        v-if="viewType !== 'kanban'"
        class="flex shrink-0 items-center gap-2"
      >
        <AstraButton
          variant="secondary"
          size="sm"
          :label="__('Import')"
          @click="
            router.push({
              name: 'NewDataImport',
              params: { doctype: 'CRM Deal' },
            })
          "
        />
        <AstraButton
          v-if="canExportDeals"
          variant="secondary"
          size="sm"
          :label="__('Export')"
          @click="exportDealsCsv"
        />
      </div>
    </div>
    <AstraDealsBoard
      v-if="route.params.viewType == 'kanban'"
      v-model="deals"
      class="min-h-0 flex-1"
      :rows-by-name="rowsByName"
      :show-stages-link="showStagesLink"
      :options="{
        getRoute: (row) => getRoute(row.name),
        onNewClick: (column) => onNewClick(column),
      }"
      @update="(data) => viewControls.updateKanbanSettings(data)"
      @loadMore="(columnName) => viewControls.loadMoreKanban(columnName)"
    />
    <GroupSummaryTable
      v-else-if="viewControls?.groupSummary"
      doctype="CRM Deal"
      :settings="viewControls.groupSummary"
      :filters="viewControls.currentFilters"
      @update:settings="(s) => viewControls.updateGroupSummary(s)"
    />
    <DealsListView
      v-else-if="deals.data && rows.length"
      ref="dealsListView"
      v-model="deals.data.page_length_count"
      v-model:list="deals"
      :rows="rows"
      :columns="columns"
      :options="{
        showTooltip: false,
        resizeColumn: true,
        rowCount: deals.data.row_count,
        totalCount: deals.data.total_count,
      }"
      @loadMore="() => loadMore++"
      @columnWidthUpdated="() => triggerResize++"
      @updatePageCount="(count) => (updatedPageCount = count)"
      @applyFilter="(data) => viewControls.applyFilter(data)"
      @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
      @likeDoc="(data) => viewControls.likeDoc(data)"
      @selectionsChanged="
        (selections) => viewControls.updateSelections(selections)
      "
    />
    <EmptyState
      v-else-if="deals.data && !rows.length"
      name="Deals"
      :icon="DealsIcon"
      :title="__('No deals yet')"
      :description="
        __(
          'A deal is a sale you are working on. Create one, or convert a lead into a deal once it looks promising.',
        )
      "
      :filtered="!!Object.keys(deals.params?.filters || {}).length"
      importDoctype="CRM Deal"
      @create="showDealModal = true"
    />
    <DealModal
      v-if="showDealModal"
      v-model="showDealModal"
      :defaults="defaults"
    />
  </RecordsListChrome>
</template>

<script setup>
import GroupSummaryTable from '@/components/GroupSummaryTable.vue'
import CustomActions from '@/components/CustomActions.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import RecordsListChrome from '@/components/ListViews/RecordsListChrome.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import AstraDealsBoard from '@/components/Kanban/AstraDealsBoard.vue'
import DealModal from '@/components/Modals/DealModal.vue'
import ViewControls from '@/components/ViewControls.vue'
import AstraButton from '@/components/astra/AstraButton.vue'
import { useRecordsViews } from '@/composables/useRecordsViews'
import { canUseCrmCsvExport, crmCsvExportUrl } from '@/utils/csvExport'
import { getMeta } from '@/stores/meta'
import { usersStore } from '@/stores/users'
import { organizationsStore } from '@/stores/organizations'
import { statusesStore } from '@/stores/statuses'
import { formatDate, timeAgo, website, formatTime } from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { useBroadcast } from '@/composables/useBroadcast'
import { useRoute, useRouter } from 'vue-router'
import { ref, reactive, computed, h } from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Deal')
const { getUser, isManager, isAdmin } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()
const { on } = useBroadcast()

const route = useRoute()
const router = useRouter()

/** Stages settings lives on another branch; hide the gear until registered. */
const showStagesLink = computed(() => {
  if (!(isManager() || isAdmin())) return false
  return Boolean(
    router.hasRoute?.('Stages') ||
      router.getRoutes?.().some(
        (r) =>
          r.name === 'Stages' ||
          r.path?.includes?.('/settings/stages') ||
          r.meta?.settingsPage === 'Stages',
      ),
  )
})

function getRoute(name) {
  return {
    name: 'Deal',
    params: { dealId: name },
    query: { view: route.query.view, viewType: route.params.viewType },
  }
}

const dealsListView = ref(null)
const showDealModal = ref(false)

on('trigger_deal_create', (data) => {
  showDealModal.value = Boolean(data)
})

const defaults = reactive({})

// deals data is loaded in the ViewControls component
const deals = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const {
  viewType,
  activeView,
  viewTabs,
  selectView,
  setViewType,
  saveView,
  filterChipsFromList,
  removeFilterChip,
} = useRecordsViews({
  doctype: 'CRM Deal',
  list: deals,
  viewControls,
  defaultFilters: () => ({}),
  allLabel: __('All open deals'),
})

const filterChips = computed(() => filterChipsFromList())
const canExportDeals = computed(() => canUseCrmCsvExport('CRM Deal'))

function exportDealsCsv() {
  const fields = (deals.value?.data?.columns || []).map((c) => c.key)
  window.location.href = crmCsvExportUrl({
    doctype: 'CRM Deal',
    fields,
    filters: deals.value?.params?.filters || {},
    orderBy: deals.value?.params?.order_by,
    limit: deals.value?.data?.total_count || 100,
    title: 'CRM Deal',
  })
}

// Rows
const rows = computed(() => {
  if (!deals.value?.data?.data) return []
  if (deals.value.data.view_type === 'group_by') {
    if (!deals.value?.data.group_by_field?.fieldname) return []
    return getGroupedByRows(
      deals.value?.data.data,
      deals.value?.data.group_by_field,
      deals.value.data.columns,
    )
  } else if (deals.value.data.view_type === 'kanban') {
    return getKanbanRows(deals.value.data.data, deals.value.data.fields)
  } else {
    return parseRows(deals.value?.data.data, deals.value.data.columns)
  }
})

const rowsByName = computed(() => {
  const map = {}
  for (const row of rows.value || []) {
    if (row?.name) map[row.name] = row
  }
  return map
})

const columns = computed(() => {
  let _columns = deals.value?.data?.columns || []

  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})

function getGroupedByRows(listRows, groupByField, columns) {
  let groupedRows = []

  groupByField.options?.forEach((option) => {
    let filteredRows

    if (!option) {
      filteredRows = listRows.filter((row) => !row[groupByField.fieldname])
    } else {
      filteredRows = listRows.filter(
        (row) => row[groupByField.fieldname] == option,
      )
    }

    let groupDetail = {
      label: groupByField.label,
      group: option || __(' '),
      collapsed: false,
      rows: parseRows(filteredRows, columns),
    }
    if (groupByField.fieldname == 'status') {
      groupDetail.icon = () =>
        h(IndicatorIcon, {
          class: getDealStatus(option)?.color,
        })
    }
    groupedRows.push(groupDetail)
  })

  return groupedRows || listRows
}

function getKanbanRows(data, columns) {
  let _rows = []
  data.forEach((column) => {
    column.data?.forEach((row) => {
      _rows.push(row)
    })
  })
  return parseRows(_rows, columns)
}

function parseRows(rows, columns = []) {
  let view_type = deals.value.data.view_type
  let key = view_type === 'kanban' ? 'fieldname' : 'key'
  let type = view_type === 'kanban' ? 'fieldtype' : 'type'

  return rows.map((deal) => {
    let _rows = { name: deal.name }
    deals.value.data.rows.forEach((row) => {
      _rows[row] = deal[row]

      let fieldType = columns?.find((col) => (col[key] || col.value) == row)?.[
        type
      ]

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(deal[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, deal)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, deal)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, deal)
      }

      if (row == 'organization') {
        _rows[row] = {
          label: deal.organization,
          logo: getOrganization(deal.organization)?.organization_logo,
        }
      } else if (row === 'website') {
        _rows[row] = { label: website(deal.website), url: deal.website }
      } else if (row == 'status') {
        _rows[row] = {
          label: deal.status,
          color: getDealStatus(deal.status)?.color,
        }
      } else if (row == 'sla_status') {
        let value = deal.sla_status
        let tooltipText = value
        let color =
          deal.sla_status == 'Failed'
            ? 'red'
            : deal.sla_status == 'Fulfilled'
              ? 'green'
              : 'amber'
        if (value == 'First Response Due' || value == 'Rolling Response Due') {
          value = __(timeAgo(deal.response_by))
          tooltipText = formatDate(deal.response_by)
          if (new Date(deal.response_by) < new Date()) {
            color = 'red'
          }
        }
        _rows[row] = {
          label: tooltipText,
          value: value,
          color: color,
        }
      } else if (row == 'deal_owner') {
        _rows[row] = {
          label: deal.deal_owner && getUser(deal.deal_owner).full_name,
          ...(deal.deal_owner && getUser(deal.deal_owner)),
        }
      } else if (row == '_assign') {
        let assignees = JSON.parse(deal._assign || '[]')
        _rows[row] = assignees.map((user) => ({
          name: user,
          image: getUser(user).user_image,
          label: getUser(user).full_name,
        }))
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = timestampCell(deal[row])
      } else if (
        ['first_response_time', 'first_responded_on', 'response_by'].includes(
          row,
        )
      ) {
        let field = row == 'response_by' ? 'response_by' : 'first_responded_on'
        _rows[row] = {
          label: deal[field] ? formatDate(deal[field]) : '',
          timeAgo: deal[row]
            ? row == 'first_response_time'
              ? formatTime(deal[row])
              : __(timeAgo(deal[row]))
            : '',
        }
      }
    })
    _rows['_email_count'] = deal._email_count
    _rows['_note_count'] = deal._note_count
    _rows['_task_count'] = deal._task_count
    _rows['_comment_count'] = deal._comment_count
    return _rows
  })
}

function onNewClick(column) {
  let column_field = deals.value.params.column_field

  if (column_field) {
    defaults[column_field] = column.column.name
  }

  showDealModal.value = true
}
</script>
