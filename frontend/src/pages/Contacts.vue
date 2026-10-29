<template>
  <RecordsListChrome
    :title="__('Contacts')"
    :description="__('People at your customers and prospects')"
    :create-label="__('+ New contact')"
    :view-tabs="viewTabs"
    :active-view="activeView"
    :show-save-view="true"
    :show-view-switch="false"
    view-type="list"
    :filter-chips="displayFilterChips"
    :show-filter-bar="true"
    :show-add-filter="true"
    :sort-label="__('Last activity')"
    @create="showContactModal = true"
    @select-view="selectView"
    @save-view="saveView"
    @remove-filter="removeFilterChip"
    @add-filter="openFilters"
    @sort="noop"
  >
    <template #actions>
      <CustomActions
        v-if="contactsListView?.customListActions"
        :actions="contactsListView.customListActions"
      />
      <AstraButton
        variant="primary"
        size="sm"
        :label="__('New contact')"
        @click="showContactModal = true"
      >
        <template #prefix>
          <svg
            class="size-3.5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            aria-hidden="true"
          >
            <path d="M12 5v14M5 12h14" />
          </svg>
        </template>
      </AstraButton>
    </template>
    <template #toolbar>
      <button
        type="button"
        class="inline-flex h-crm-control-sm items-center gap-[7px] rounded-crm-control-sm px-2.5 text-crm-label font-semibold text-crm-muted-fg"
      >
        <svg
          class="size-3.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          aria-hidden="true"
        >
          <rect x="3" y="4" width="18" height="16" rx="2" />
          <path d="M9 4v16M15 4v16" />
        </svg>
        {{ __('Columns') }}
      </button>
      <button
        type="button"
        class="inline-flex h-crm-control-sm items-center gap-[7px] rounded-crm-control-sm px-2.5 text-crm-label font-semibold text-crm-muted-fg"
        @click="showCrmCsvImport = true"
      >
        <svg
          class="size-3.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          aria-hidden="true"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <path d="m17 8-5-5-5 5" />
          <path d="M12 3v12" />
        </svg>
        {{ __('Import') }}
      </button>
      <button
        v-if="canExportContacts"
        type="button"
        class="inline-flex h-crm-control-sm items-center rounded-crm-control-sm px-2.5 text-crm-label font-semibold text-crm-muted-fg"
        @click="exportContactsCsv"
      >
        {{ __('Export') }}
      </button>
    </template>
    <!-- ViewControls stays mounted for data loading; chrome is the Astra filter bar. -->
    <div class="sr-only" aria-hidden="true">
      <ViewControls
        ref="viewControls"
        v-model="contacts"
        v-model:loadMore="loadMore"
        v-model:resizeColumn="triggerResize"
        v-model:updatedPageCount="updatedPageCount"
        doctype="Contact"
        :options="{
          hideColumnsButton: true,
        }"
      />
    </div>
    <ContactsListView
      v-if="contacts.data && rows.length"
      ref="contactsListView"
      v-model="contacts.data.page_length_count"
      v-model:list="contacts"
      :rows="rows"
      :columns="columns"
      :options="{
        showTooltip: false,
        resizeColumn: true,
        rowCount: contacts.data.row_count,
        totalCount: contacts.data.total_count,
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
      v-else-if="contacts.data && !rows.length"
      name="Contacts"
      :icon="ContactsIcon"
      :title="__('No contacts yet')"
      :description="
        __(
          'Contacts are the people you talk to at your leads and customers. They are added when you convert a lead, or you can add them here.',
        )
      "
      :filtered="!!Object.keys(contacts.params?.filters || {}).length"
      importDoctype="Contact"
      @create="showContactModal = true"
    />
    <CrmCsvImportModal
      v-if="showCrmCsvImport"
      v-model="showCrmCsvImport"
      doctype="Contact"
    />
    <ContactModal
      v-if="showContactModal"
      v-model="showContactModal"
      :contact="{}"
    />
  </RecordsListChrome>
</template>

<script setup>
import CustomActions from '@/components/CustomActions.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import CrmCsvImportModal from '@/components/Modals/CrmCsvImportModal.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import RecordsListChrome from '@/components/ListViews/RecordsListChrome.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import ViewControls from '@/components/ViewControls.vue'
import AstraButton from '@/components/astra/AstraButton.vue'
import { useRecordsViews } from '@/composables/useRecordsViews'
import { getMeta } from '@/stores/meta'
import { canUseCrmCsvExport, crmCsvExportUrl } from '@/utils/csvExport'
import { formatDate } from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { ref, computed } from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('Contact')

const showContactModal = ref(false)
const showCrmCsvImport = ref(false)

const contactsListView = ref(null)

const contacts = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const {
  activeView,
  viewTabs,
  selectView,
  saveView,
  filterChipsFromList,
  removeFilterChip,
} = useRecordsViews({
  doctype: 'Contact',
  list: contacts,
  viewControls,
  defaultFilters: () => ({}),
  allLabel: __('All contacts'),
})

const filterChips = computed(() => filterChipsFromList())
const canExportContacts = computed(() => canUseCrmCsvExport('Contact'))

const PARITY_FILTER_CHIPS = [
  {
    id: 'company',
    key: __('Company'),
    value: __('Any'),
    active: false,
    trailing: 'chevron',
  },
]

const displayFilterChips = computed(() => {
  const fromList = filterChips.value
  if (fromList.length) {
    return fromList.map((c) => ({
      ...c,
      active: c.active === true,
      trailing: c.trailing || 'dismiss',
    }))
  }
  const fromData = contacts.value?.data?.parity_filter_chips
  if (Array.isArray(fromData) && fromData.length) {
    return fromData.map((c) => ({
      id: c.id,
      key: __(c.key || c.label),
      value: c.value,
      fieldname: c.fieldname,
      active: c.active === true,
      trailing: c.trailing || 'dismiss',
    }))
  }
  return PARITY_FILTER_CHIPS
})

function openFilters() {}
function noop() {}

function exportContactsCsv() {
  const fields = (contacts.value?.data?.columns || []).map((c) => c.key)
  window.location.href = crmCsvExportUrl({
    doctype: 'Contact',
    fields,
    filters: contacts.value?.params?.filters || {},
    orderBy: contacts.value?.params?.order_by,
    limit: contacts.value?.data?.total_count || 100,
    title: 'Contact',
  })
}

const rows = computed(() => {
  if (
    !contacts.value?.data?.data ||
    !['list', 'group_by'].includes(contacts.value.data.view_type)
  )
    return []
  return contacts.value?.data.data.map((contact) => {
    let _rows = { name: contact.name }
    contacts.value?.data.rows.forEach((row) => {
      _rows[row] = contact[row]

      let fieldType = contacts.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(contact[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, contact)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, contact)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, contact)
      }

      if (row == 'full_name') {
        _rows[row] = contact.full_name
      } else if (row == 'company_name') {
        _rows[row] = contact.company_name
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = timestampCell(contact[row])
      }
    })
    // Keep designation / open_deals helpers available to the list view.
    _rows.designation = contact.designation
    _rows.open_deals = contact.open_deals
    _rows.open_deals_count = contact.open_deals_count
    _rows.open_deals_value = contact.open_deals_value
    _rows.image = contact.image
    return _rows
  })
})

const columns = computed(() => contacts.value?.data?.columns || [])
</script>
