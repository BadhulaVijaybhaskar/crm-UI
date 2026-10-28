<template>
  <RecordsListChrome
    :title="__('Contacts')"
    :description="__('People at your customers and prospects.')"
    :create-label="__('+ New contact')"
    :view-tabs="viewTabs"
    :active-view="activeView"
    :show-save-view="true"
    :show-view-switch="false"
    view-type="list"
    :filter-chips="filterChips"
    :show-filter-bar="filterChips.length > 0"
    @create="showContactModal = true"
    @select-view="selectView"
    @save-view="saveView"
    @remove-filter="removeFilterChip"
  >
    <template #actions>
      <CustomActions
        v-if="contactsListView?.customListActions"
        :actions="contactsListView.customListActions"
      />
      <AstraButton
        variant="primary"
        :label="__('+ New contact')"
        @click="showContactModal = true"
      />
    </template>
    <div class="astra-records-vc border-b border-crm-border bg-crm-card">
      <ViewControls
        ref="viewControls"
        v-model="contacts"
        v-model:loadMore="loadMore"
        v-model:resizeColumn="triggerResize"
        v-model:updatedPageCount="updatedPageCount"
        doctype="Contact"
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
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import RecordsListChrome from '@/components/ListViews/RecordsListChrome.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import ViewControls from '@/components/ViewControls.vue'
import AstraButton from '@/components/astra/AstraButton.vue'
import { useRecordsViews } from '@/composables/useRecordsViews'
import { getMeta } from '@/stores/meta'
import { organizationsStore } from '@/stores/organizations.js'
import { formatDate } from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { ref, computed } from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('Contact')
const { getOrganization } = organizationsStore()

const showContactModal = ref(false)

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

const rows = computed(() => {
  if (
    !contacts.value?.data?.data ||
    !['list', 'group_by'].includes(contacts.value.data.view_type)
  )
    return []
  return contacts.value?.data.data.map((contact) => {
    let _rows = {}
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
        _rows[row] = {
          label: contact.full_name,
          image_label: contact.full_name,
          image: contact.image,
        }
      } else if (row == 'company_name') {
        _rows[row] = {
          label: contact.company_name,
          logo: getOrganization(contact.company_name)?.organization_logo,
        }
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = timestampCell(contact[row])
      }
    })
    return _rows
  })
})

const columns = computed(() => {
  let _columns = contacts.value?.data?.columns || []

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
</script>
