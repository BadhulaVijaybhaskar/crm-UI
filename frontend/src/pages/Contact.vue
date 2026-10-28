<template>
  <div
    v-if="contact.doc"
    class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg"
  >
    <div class="grid min-h-0 flex-1 grid-cols-1 overflow-hidden xl:grid-cols-crm-record">
    <div class="flex min-h-0 min-w-0 flex-col overflow-hidden">
    <nav
      class="flex items-center gap-1.5 px-crm-page-x pt-3 text-crm-meta text-crm-muted-fg"
      aria-label="Breadcrumb"
    >
      <router-link :to="{ name: 'Contacts' }" class="hover:text-crm-fg">
        {{ __('Contacts') }}
      </router-link>
      <span aria-hidden="true">›</span>
      <span class="truncate text-crm-fg">{{ title }}</span>
    </nav>

    <AstraRecordHeader :title="title" :meta="contactMeta" squared-avatar>
      <template #avatar>
        <RecordAvatar
          :name="title"
          :src="contact.doc.image || ''"
          :removable="!!contact.doc.image"
          @upload="changeContactImage"
          @remove="changeContactImage('')"
        />
      </template>
      <template #actions>
        <CustomActions
          v-if="contact._actions?.length"
          :actions="contact._actions"
        />
        <ConnectActions
          v-if="contact.doc.name"
          record-type="Contact"
          :record-id="contact.doc.name"
          :phone="contact.doc.mobile_no || ''"
          show-labels
        />
        <AstraButton
          v-if="callEnabled && contact.doc.mobile_no"
          variant="secondary"
          size="sm"
          :label="__('Call')"
          @click="makeCall(contact.doc.mobile_no)"
        />
        <AstraButton
          variant="primary"
          size="sm"
          :label="__('New Deal')"
          @click="openDealModal"
        />
        <AstraButton
          v-if="canDelete"
          variant="negative"
          size="sm"
          :label="__('Delete')"
          @click="deleteContact()"
        />
      </template>
    </AstraRecordHeader>

    <div class="empty:hidden">
      <ConnectCallSummary doctype="Contact" :name="contactId" />
    </div>

      <Tabs
        v-model="activeTab"
        as="div"
        :tabs="tabs"
        :class="recordTabsClass()"
      >
        <template #tab-label="{ tab }">{{ __(tab.label) }}</template>
        <template #tab-suffix="{ tab }">
          <span
            v-if="tab.count != null"
            class="rounded bg-crm-neutral-soft px-1 text-crm-micro font-semibold text-crm-muted-fg"
          >
            {{ tab.count }}
          </span>
        </template>
        <template #tab-panel="{ tab }">
          <Activities
            v-if="tab.value === 'activity'"
            ref="activities"
            v-model:activeTab="activityTab"
            doctype="Contact"
            :docname="contact.doc.name"
            :tabs="activityTabs"
          />
          <DealsListView
            v-else-if="tab.label === 'Deals' && rows.length"
            class="mt-4"
            :rows="rows"
            :columns="columns"
            :options="{ selectable: false, showTooltip: false }"
          />
          <EmptyState
            v-else-if="tab.label === 'Deals' && !rows.length"
            :icon="tab.iconLeft"
            name="Deals"
            :description="__('Use New Deal to create a deal for this contact.')"
          />
        </template>
      </Tabs>
    </div>
      <AstraSidePanel stacked>
        <SidePanelLayout
          v-if="sections.data"
          :sections="parsedSections"
          doctype="Contact"
          :docname="contact.doc.name"
          @reload="sections.reload"
        />
      </AstraSidePanel>
    </div>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'Contact'"
    :docname="contact.doc.name"
    name="Contacts"
  />
  <DealModal
    v-if="showDealModal"
    v-model="showDealModal"
    :defaults="dealDefaults"
  />
</template>

<script setup>
import ErrorPage from '@/components/ErrorPage.vue'
import AstraSidePanel from '@/components/astra/AstraSidePanel.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import ConnectCallSummary from '@/components/ConnectCallSummary.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import Activities from '@/components/Activities/Activities.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import DealModal from '@/components/Modals/DealModal.vue'
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import CustomActions from '@/components/CustomActions.vue'
import ConnectActions from '@/components/AstraConnect/ConnectActions.vue'
import AstraRecordHeader from '@/components/astra/AstraRecordHeader.vue'
import AstraButton from '@/components/astra/AstraButton.vue'
import RecordAvatar from '@/components/Pipeline/RecordAvatar.vue'
import { recordTabsClass } from '@/components/Pipeline/recordChrome'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { setupCustomizations } from '@/utils'
import { useContactFields } from '@/composables/useContactFields'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { organizationsStore } from '@/stores/organizations.js'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/telephony'
import { Tabs, call, createResource, usePageMeta, toast } from 'frappe-ui'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from '@framework/ui/telemetry'
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const { brand } = getSettings()
const { makeCall, $dialog, $socket } = globalStore()

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('Contact')
const { capture } = useTelemetry()

const props = defineProps({
  contactId: { type: String, required: true },
})

const router = useRouter()

const errorTitle = ref('')
const errorMessage = ref('')

const {
  document: contact,
  permissions,
  scripts,
  triggerOnRender,
} = useDocument('Contact', props.contactId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

const transformField = useContactFields(contact)

onMounted(async () => {
  if (contact.doc) await triggerOnRender()
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return contact.doc?.[t] || props.contactId
})

const contactMeta = computed(() => {
  const parts = []
  const doc = contact.doc || {}
  if (doc.designation) parts.push(doc.designation)
  else if (doc.job_title) parts.push(doc.job_title)
  if (doc.company_name) parts.push(doc.company_name)
  if (doc.city) parts.push(doc.city)
  return parts
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})
const showDeleteLinkedDocModal = ref(false)
const showDealModal = ref(false)
const dealDefaults = ref({})

// company_name is free text, so only pick an existing organization; otherwise the deal creates one
async function openDealModal() {
  const company = contact.doc.company_name
  const isOrganization =
    company &&
    (await call('frappe.client.get_count', {
      doctype: 'CRM Organization',
      filters: { name: company },
    }))
  dealDefaults.value = {
    contact: contact.doc.name,
    ...(isOrganization
      ? { organization: company }
      : { organization_name: company }),
  }
  showDealModal.value = true
}

async function deleteContact() {
  showDeleteLinkedDocModal.value = true
}

function changeContactImage(file) {
  contact.doc.image = file?.file_url || ''
  contact.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Contact image updated'))
    },
  })
}

const activeTab = ref('activity')
const activityTab = ref('activity')
const activityTabs = [
  {
    name: 'Activity',
    value: 'activity',
    label: __('Activity'),
    iconLeft: ActivityIcon,
  },
]
const tabs = [
  {
    value: 'activity',
    label: 'Activity',
    iconLeft: ActivityIcon,
  },
  {
    value: 'deals',
    label: 'Deals',
    iconLeft: DealsIcon,
    count: computed(() => deals.data?.length),
  },
]

const deals = createResource({
  url: 'crm.api.contact.get_linked_deals',
  cache: ['deals', props.contactId],
  params: { contact: props.contactId },
  auto: true,
})

const rows = computed(() => {
  if (!deals.data || deals.data == []) return []

  return deals.data.map((row) => getDealRowObject(row))
})

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'Contact'],
  params: { doctype: 'Contact' },
  auto: true,
})

const parsedSections = computed(() => {
  if (!sections.data) return []
  return sections.data.map((section) => ({
    ...section,
    columns: section.columns.map((column) => ({
      ...column,
      fields: column.fields.map((field) => {
        field.label = fieldLabelMap[field.fieldname] || field.label
        field.placeholder =
          fieldPlaceholderMap[field.fieldname] || field.placeholder
        return transformField(field, { showAddressModal })
      }),
    })),
  }))
})

const fieldLabelMap = {
  mobile_no: __('Mobile Number'),
  company_name: __('Organization'),
}

const fieldPlaceholderMap = {
  mobile_no: __('Add Mobile Number...'),
  company_name: __('Add Organization...'),
}

const { getFormattedCurrency } = getMeta('CRM Deal')

const columns = computed(() => dealColumns)

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: getOrganization(deal.organization)?.organization_logo,
    },
    deal_value: getFormattedCurrency('deal_value', deal),
    status: {
      label: deal.status,
      color: getDealStatus(deal.status)?.color,
    },
    email: deal.email,
    mobile_no: deal.mobile_no,
    deal_owner: {
      label: deal.deal_owner && getUser(deal.deal_owner).full_name,
      ...(deal.deal_owner && getUser(deal.deal_owner)),
    },
    modified: timestampCell(deal.modified),
  }
}

const dealColumns = [
  {
    label: __('Organization'),
    key: 'organization',
    width: '11rem',
  },
  {
    label: __('Amount'),
    key: 'deal_value',
    align: 'right',
    width: '9rem',
  },
  {
    label: __('Status'),
    key: 'status',
    width: '10rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem',
  },
  {
    label: __('Mobile Number'),
    key: 'mobile_no',
    width: '11rem',
  },
  {
    label: __('Deal Owner'),
    key: 'deal_owner',
    width: '10rem',
  },
  {
    label: __('Last Modified'),
    key: 'modified',
    width: '8rem',
  },
]

const { showModal } = useDoctypeModal()

function showAddressModal(_address) {
  showModal({
    name: _address || null,
    doctype: 'Address',
    callbacks: {
      afterInsert: (d) => {
        capture('address_created')
        contact.doc.address = d.name
        contact.save.submit()
      },
    },
  })
}

// Setup custom actions from Form Scripts
watch(
  () => contact.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        updateField: contact.setValue.submit,
        deleteDoc: deleteContact,
        call,
      })
      contact._actions = s.actions || []
    }
  },
  { once: true },
)
</script>
