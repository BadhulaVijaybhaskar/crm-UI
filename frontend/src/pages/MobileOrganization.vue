<template>
  <div
    v-if="organization.doc"
    class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg"
  >
    <nav
      class="flex items-center gap-1.5 px-3 pt-2.5 text-crm-meta text-crm-muted-fg"
      aria-label="Breadcrumb"
    >
      <router-link :to="{ name: 'Organizations' }" class="hover:text-crm-fg">
        {{ __('Companies') }}
      </router-link>
      <span aria-hidden="true">›</span>
      <span class="truncate text-crm-fg">{{ title }}</span>
    </nav>

    <AstraRecordHeader
      :title="title"
      :avatar-src="organization.doc.organization_logo || ''"
      squared-avatar
      :meta="organizationMeta"
    >
      <template #actions>
        <Link
          v-if="activeTab === 'contacts'"
          value=""
          doctype="Contact"
          :filters="{ company_name: ['!=', props.organizationId] }"
          :onCreate="
            (value, close) => {
              _contact = {
                first_name: value,
                company_name: props.organizationId,
              }
              showContactModal = true
              close()
            }
          "
          @change="(contact) => addContact(contact)"
        >
          <template #target="{ togglePopover }">
            <AstraButton
              variant="primary"
              size="sm"
              :label="__('Add Contact')"
              @click="togglePopover()"
            />
          </template>
        </Link>
        <AstraButton
          variant="secondary"
          size="sm"
          :label="__('Website')"
          @click="openWebsite"
        />
        <AstraButton
          v-if="canDelete"
          variant="negative"
          size="sm"
          :label="__('Delete')"
          @click="deleteOrganization"
        />
      </template>
    </AstraRecordHeader>

    <FileUploader
      :validateFile="validateIsImageFile"
      @success="changeOrganizationImage"
    >
      <template #default="{ openFileSelector, error }">
        <div
          class="flex items-center gap-2 border-b border-crm-border px-3 py-2"
        >
          <Button
            size="sm"
            :label="
              organization.doc.organization_logo
                ? __('Change Image')
                : __('Upload Image')
            "
            iconLeft="lucide-upload"
            @click="openFileSelector"
          />
          <Button
            v-if="organization.doc.organization_logo"
            size="sm"
            theme="red"
            :label="__('Remove Image')"
            iconLeft="lucide-trash-2"
            @click="changeOrganizationImage('')"
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
          v-if="tab.value !== 'details'"
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
              doctype="CRM Organization"
              :docname="organization.doc.name"
              @reload="sections.reload"
            />
          </div>
        </div>
        <DealsListView
          v-if="tab.label === 'Deals' && rows.length"
          class="mt-4"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <ContactsListView
          v-if="tab.label === 'Contacts' && rows.length"
          class="mt-4"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <div
          v-if="!rows.length && tab.name !== 'Details'"
          class="grid flex-1 place-items-center text-2xl-medium text-ink-gray-4"
        >
          <div class="flex flex-col items-center justify-center space-y-3">
            <component :is="tab.iconLeft" class="!h-10 !w-10" />
            <div>{{ __('No {0} Found', [__(tab.label)]) }}</div>
          </div>
        </div>
      </template>
    </Tabs>
  </div>
  <ContactModal
    v-if="showContactModal"
    v-model="showContactModal"
    :contact="_contact"
    :options="{ redirect: false, afterInsert: () => contacts.reload() }"
  />
</template>

<script setup>
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import Link from '@/components/Controls/Link.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import AstraRecordHeader from '@/components/astra/AstraRecordHeader.vue'
import { recordTabsClass } from '@/components/Pipeline/recordChrome'
import AstraButton from '@/components/astra/AstraButton.vue'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import {
  validateIsImageFile,
  openWebsite as openExternalWebsite,
} from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import {
  FileUploader,
  Tabs,
  call,
  createListResource,
  usePageMeta,
  createResource,
  toast,
} from 'frappe-ui'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from '@framework/ui/telemetry'
import { h, computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  organizationId: { type: String, required: true },
})

const { brand } = getSettings()
const { getUser } = usersStore()
const { $dialog } = globalStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('CRM Organization')
const { capture } = useTelemetry()

const router = useRouter()

const {
  document: organization,
  permissions,
  triggerOnRender,
} = useDocument('CRM Organization', props.organizationId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

onMounted(async () => {
  if (organization.doc) await triggerOnRender()
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return organization.doc?.[t] || props.organizationId
})

const organizationMeta = computed(() => {
  const parts = []
  const doc = organization.doc || {}
  if (doc.website) {
    parts.push(
      doc.website.replace(/^(?:https?:\/\/)?(?:www\.)?/i, ''),
    )
  }
  if (doc.industry) parts.push(doc.industry)
  return parts
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

async function changeOrganizationImage(file) {
  await call('frappe.client.set_value', {
    doctype: 'CRM Organization',
    name: props.organizationId,
    fieldname: 'organization_logo',
    value: file?.file_url || '',
  })
  organization.reload()
}

async function deleteOrganization() {
  $dialog({
    title: __('Delete Organization'),
    message: __('Are you sure you want to delete this organization?'),
    actions: [
      {
        label: __('Delete'),
        theme: 'red',
        variant: 'solid',
        async onClick({ close }) {
          await call('frappe.client.delete', {
            doctype: 'CRM Organization',
            name: props.organizationId,
          })
          close()
          router.push({ name: 'Organizations' })
        },
      },
    ],
  })
}

function openWebsite() {
  if (!organization.doc.website) {
    toast.error(__('No Website Found'))
    return
  }

  openExternalWebsite(organization.doc.website)
}

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Organization'],
  params: { doctype: 'CRM Organization' },
  auto: true,
  transform: (data) => getParsedSections(data),
})

function getParsedSections(_sections) {
  return _sections.map((section) => {
    section.columns = section.columns.map((column) => {
      column.fields = column.fields.map((field) => {
        if (field.fieldname === 'address') {
          return {
            ...field,
            create: (value, close) => {
              showAddressModal()
              close()
            },
            edit: (address) => showAddressModal(address),
          }
        } else {
          return field
        }
      })
      return column
    })
    return section
  })
}

const activeTab = ref('details')
const showContactModal = ref(false)
const _contact = ref({})
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
  {
    name: 'Contacts',
    value: 'contacts',
    label: __('Contacts'),
    iconLeft: h(ContactsIcon, { class: 'h-4 w-4' }),
    count: computed(() => contacts.data?.length),
  },
]

const deals = createListResource({
  type: 'list',
  doctype: 'CRM Deal',
  cache: ['deals', props.organizationId],
  fields: [
    'name',
    'organization',
    'currency',
    'deal_value',
    'status',
    'email',
    'mobile_no',
    'deal_owner',
    'modified',
  ],
  filters: {
    organization: props.organizationId,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const contacts = createListResource({
  type: 'list',
  doctype: 'Contact',
  cache: ['contacts', props.organizationId],
  fields: [
    'name',
    'full_name',
    'image',
    'email_id',
    'mobile_no',
    'company_name',
    'modified',
  ],
  filters: {
    company_name: props.organizationId,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

// Links an existing contact to this organization; `Contact.company_name` is
// the only tie between the two, and until now it could only be set from the
// contact's own page.
async function addContact(contact) {
  if (!contact) return
  await call('frappe.client.set_value', {
    doctype: 'Contact',
    name: contact,
    fieldname: 'company_name',
    value: props.organizationId,
  })
  contacts.reload()
  toast.success(__('Contact added to {0}', [props.organizationId]))
}

const rows = computed(() => {
  let list = activeTab.value === 'deals' ? deals : contacts

  if (!list.data) return []

  return list.data.map((row) => {
    return activeTab.value === 'deals'
      ? getDealRowObject(row)
      : getContactRowObject(row)
  })
})

const { getFormattedCurrency } = getMeta('CRM Deal')

const columns = computed(() => {
  return activeTab.value === 'deals' ? dealColumns : contactColumns
})

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: organization.doc?.organization_logo,
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

function getContactRowObject(contact) {
  return {
    name: contact.name,
    full_name: {
      label: contact.full_name,
      image_label: contact.full_name,
      image: contact.image,
    },
    email: contact.email_id,
    mobile_no: contact.mobile_no,
    company_name: {
      label: contact.company_name,
      logo: organization.doc?.organization_logo,
    },
    modified: timestampCell(contact.modified),
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

const contactColumns = [
  {
    label: __('Name'),
    key: 'full_name',
    width: '17rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem',
  },
  {
    label: __('Phone'),
    key: 'mobile_no',
    width: '12rem',
  },
  {
    label: __('Organization'),
    key: 'company_name',
    width: '12rem',
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
        organization.doc.address = d.name
        organization.save.submit()
      },
    },
  })
}
</script>
