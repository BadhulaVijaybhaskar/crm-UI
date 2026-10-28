<template>
  <div
    v-if="contact.doc"
    class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg"
  >
    <nav
      class="flex items-center gap-1.5 px-3 pt-2.5 text-crm-meta text-crm-muted-fg"
      aria-label="Breadcrumb"
    >
      <router-link :to="{ name: 'Contacts' }" class="hover:text-crm-fg">
        {{ __('Contacts') }}
      </router-link>
      <span aria-hidden="true">›</span>
      <span class="truncate text-crm-fg">{{ title }}</span>
    </nav>

    <AstraRecordHeader
      :title="title"
      :avatar-src="contact.doc.image || ''"
      :meta="contactMeta"
    >
      <template #actions>
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
          v-if="canDelete"
          variant="negative"
          size="sm"
          :label="__('Delete')"
          @click="deleteContact"
        />
      </template>
    </AstraRecordHeader>

    <FileUploader
      :validateFile="validateIsImageFile"
      @success="changeContactImage"
    >
      <template #default="{ openFileSelector, error }">
        <div
          class="flex items-center gap-2 border-b border-crm-border px-3 py-2"
        >
          <Button
            size="sm"
            :label="
              contact.doc.image ? __('Change Image') : __('Upload Image')
            "
            iconLeft="lucide-upload"
            @click="openFileSelector"
          />
          <Button
            v-if="contact.doc.image"
            size="sm"
            theme="red"
            :label="__('Remove Image')"
            iconLeft="lucide-trash-2"
            @click="changeContactImage('')"
          />
          <ErrorMessage :message="__(error)" />
        </div>
      </template>
    </FileUploader>

    <Tabs
      v-model="activeTab"
      as="div"
      :tabs="tabs"
      :class="recordTabsClass({ scroll: true })"
    >
      <template #tab-suffix="{ tab, active }">
        <Badge
          v-if="tab.value === 'deals'"
          :class="[active ? 'bg-surface-gray-10' : 'bg-gray-600']"
          variant="solid"
          theme="gray"
          size="sm"
        >
          {{ tab.count }}
        </Badge>
      </template>
      <template #tab-panel="{ tab }">
        <div v-if="tab.name == 'Details'">
          <div
            v-if="sections.data"
            class="flex flex-1 flex-col justify-between overflow-hidden"
          >
            <SidePanelLayout
              :sections="sections.data"
              doctype="Contact"
              :docname="contact.doc.name"
              @reload="sections.reload"
            />
          </div>
        </div>
        <DealsListView
          v-else-if="tab.label === 'Deals' && rows.length"
          class="mt-4"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <div
          v-if="tab.label === 'Deals' && !rows.length"
          class="grid flex-1 place-items-center text-2xl-medium text-ink-gray-4"
        >
          <div class="flex flex-col items-center justify-center space-y-3">
            <component :is="tab.iconLeft" class="!h-10 !w-10" />
            <div>{{ __('No {0} found', [__(tab.label.toLowerCase())]) }}</div>
          </div>
        </div>
      </template>
    </Tabs>
  </div>
</template>

<script setup>
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import AstraRecordHeader from '@/components/astra/AstraRecordHeader.vue'
import AstraButton from '@/components/astra/AstraButton.vue'
import ConnectActions from '@/components/AstraConnect/ConnectActions.vue'
import { recordTabsClass } from '@/components/Pipeline/recordChrome'
import { validateIsImageFile } from '@/utils'
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
import {
  FileUploader,
  Tabs,
  call,
  createResource,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from '@framework/ui/telemetry'
import { ref, computed, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const { brand } = getSettings()
const { $dialog, makeCall } = globalStore()

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('Contact')
const { capture } = useTelemetry()

const props = defineProps({
  contactId: { type: String, required: true },
})

const router = useRouter()

const {
  document: contact,
  permissions,
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

function changeContactImage(file) {
  contact.doc.image = file?.file_url || ''
  contact.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Contact Image Updated'))
    },
  })
}

async function deleteContact() {
  $dialog({
    title: __('Delete Contact'),
    message: __('Are you sure you want to delete this contact?'),
    actions: [
      {
        label: __('Delete'),
        theme: 'red',
        variant: 'solid',
        async onClick({ close }) {
          await call('frappe.client.delete', {
            doctype: 'Contact',
            name: props.contactId,
          })
          close()
          router.push({ name: 'Contacts' })
        },
      },
    ],
  })
}

const activeTab = ref('details')
const tabs = [
  {
    name: 'Details',
    value: 'details',
    label: __('Details'),
    iconLeft: DetailsIcon,
  },
  {
    name: 'Deals',
    value: 'deals',
    label: __('Deals'),
    iconLeft: h(DealsIcon, { class: 'h-4 w-4' }),
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
  transform: (data) => computed(() => getParsedSections(data)),
})

function getParsedSections(_sections) {
  return _sections.map((section) => {
    section.columns = section.columns.map((column) => {
      column.fields = column.fields.map((field) =>
        transformField(field, { showAddressModal }),
      )
      return column
    })
    return section
  })
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
</script>
