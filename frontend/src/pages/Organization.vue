<template>
  <div
    v-if="organization.doc"
    class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg"
  >
    <nav
      class="flex items-center gap-1.5 px-crm-page-x pt-3 text-crm-meta text-crm-muted-fg"
      aria-label="Breadcrumb"
    >
      <router-link :to="{ name: 'Organizations' }" class="hover:text-crm-fg">
        {{ __('Companies') }}
      </router-link>
      <span aria-hidden="true">›</span>
      <span class="truncate text-crm-fg">{{ title }}</span>
    </nav>

    <AstraRecordHeader :title="title" :meta="organizationMeta" squared-avatar>
      <template #avatar>
        <RecordAvatar
          :name="title"
          :src="organization.doc.organization_logo || ''"
          :removable="!!organization.doc.organization_logo"
          @upload="changeOrganizationImage"
          @remove="changeOrganizationImage('')"
        />
      </template>
      <template #actions>
        <CustomActions
          v-if="organization._actions?.length"
          :actions="organization._actions"
        />
        <EnrichFromWebsite
          doctype="CRM Organization"
          :docname="props.organizationId"
          :website="organization.doc?.website"
          @done="onEnriched"
        />
        <AstraButton
          v-if="activeTab === 'deals'"
          variant="primary"
          size="sm"
          :label="__('New Deal')"
          @click="showDealModal = true"
        />
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
          :label="__('Open Website')"
          @click="openWebsite"
        />
        <AstraButton
          v-if="canDelete"
          variant="negative"
          size="sm"
          :label="__('Delete')"
          @click="deleteOrganization()"
        />
      </template>
    </AstraRecordHeader>

    <div class="flex min-h-0 flex-1 overflow-hidden">
      <Tabs
        v-model="activeTab"
        as="div"
        :tabs="tabs"
        :class="recordTabsClass()"
      >
        <template #tab-label="{ tab }">{{ __(tab.label) }}</template>
        <template #tab-suffix="{ tab }">
          <span
            v-if="tab.count != null && tab.value !== 'details'"
            class="rounded bg-crm-neutral-soft px-1 text-crm-micro font-semibold text-crm-muted-fg"
          >
            {{ tab.count }}
          </span>
        </template>
        <template #tab-panel="{ tab }">
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
          <EmptyState
            v-if="!rows.length"
            :icon="tab.iconLeft"
            :name="__(tab.label)"
            :description="
              tab.value === 'deals'
                ? __('Use New Deal to create a deal for this organization.')
                : ''
            "
          />
        </template>
      </Tabs>
      <Resizer
        side="right"
        :defaultWidth="340"
        class="flex h-full flex-col overflow-hidden border-l border-crm-border bg-crm-card"
      >
        <div
          v-if="sections.data"
          class="flex flex-1 flex-col justify-between overflow-hidden"
        >
          <SidePanelLayout
            :sections="sections.data"
            doctype="CRM Organization"
            :docname="organization.doc.name"
            @reload="sections.reload"
            @beforeFieldChange="beforeFieldChange"
          />
        </div>
      </Resizer>
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
    :doctype="'CRM Organization'"
    :docname="props.organizationId"
    name="Organizations"
  />
  <ContactModal
    v-if="showContactModal"
    v-model="showContactModal"
    :contact="_contact"
    :options="{ redirect: false, afterInsert: () => contacts.reload() }"
  />
  <DealModal
    v-if="showDealModal"
    v-model="showDealModal"
    :defaults="{ organization: props.organizationId }"
  />
</template>

<script setup>
import ErrorPage from '@/components/ErrorPage.vue'
import Resizer from '@/components/Resizer.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import DealModal from '@/components/Modals/DealModal.vue'
import Link from '@/components/Controls/Link.vue'
import CustomActions from '@/components/CustomActions.vue'
import EnrichFromWebsite from '@/components/EnrichFromWebsite.vue'
import AstraRecordHeader from '@/components/astra/AstraRecordHeader.vue'
import RecordAvatar from '@/components/Pipeline/RecordAvatar.vue'
import { recordTabsClass } from '@/components/Pipeline/recordChrome'
import AstraButton from '@/components/astra/AstraButton.vue'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import {
  setupCustomizations,
  openWebsite as openExternalWebsite,
} from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import {
  Tabs,
  createListResource,
  usePageMeta,
  createResource,
  toast,
  call,
} from 'frappe-ui'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from '@framework/ui/telemetry'
import { computed, ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  organizationId: { type: String, required: true },
})

const { brand } = getSettings()
const { $dialog, $socket } = globalStore()
const { getUser } = usersStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('CRM Organization')
const { capture } = useTelemetry()

const router = useRouter()

const errorTitle = ref('')
const errorMessage = ref('')

const showDeleteLinkedDocModal = ref(false)
const showContactModal = ref(false)
const showDealModal = ref(false)
const _contact = ref({})

const {
  document: organization,
  permissions,
  scripts,
  triggerOnRender,
} = useDocument('CRM Organization', props.organizationId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

function onEnriched() {
  organization.reload?.()
  sections.reload()
}

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
  if (doc.industry) parts.push(doc.industry)
  if (doc.no_of_employees) parts.push(__('{0} employees', [doc.no_of_employees]))
  if (doc.website) parts.push(website(doc.website))
  if (doc.territory) parts.push(doc.territory)
  return parts
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

async function deleteOrganization() {
  showDeleteLinkedDocModal.value = true
}

function changeOrganizationImage(file) {
  organization.setValue.submit({
    organization_logo: file?.file_url || null,
  })
}

function beforeFieldChange(data) {
  if (Object.hasOwn(data ?? {}, 'organization_name')) {
    call('frappe.client.rename_doc', {
      doctype: 'CRM Organization',
      old_name: props.organizationId,
      new_name: data.organization_name,
    }).then(() => {
      router.push({
        name: 'Organization',
        params: { organizationId: data.organization_name },
      })
    })
  } else {
    organization.save.submit()
  }
}

function website(url) {
  return url && url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, '')
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

const activeTab = ref('deals')
const tabs = [
  {
    value: 'deals',
    label: 'Deals',
    iconLeft: DealsIcon,
    count: computed(() => deals.data?.length),
  },
  {
    value: 'contacts',
    label: 'Contacts',
    iconLeft: ContactsIcon,
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

// Setup custom actions from Form Scripts
watch(
  () => organization.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        updateField: organization.setValue.submit,
        deleteDoc: deleteOrganization,
        call,
      })
      organization._actions = s.actions || []
    }
  },
  { once: true },
)
</script>
