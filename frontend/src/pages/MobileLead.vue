<template>
  <div
    v-if="doc.name"
    class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg"
  >
    <nav
      class="flex items-center gap-1.5 px-3 pt-2.5 text-crm-meta text-crm-muted-fg"
      aria-label="Breadcrumb"
    >
      <router-link :to="{ name: 'Leads' }" class="hover:text-crm-fg">
        {{ __('Leads') }}
      </router-link>
      <span aria-hidden="true">›</span>
      <span class="truncate text-crm-fg">{{ title }}</span>
    </nav>

    <AstraRecordHeader
      :title="title"
      :avatar-src="doc.image || doc.organization_logo || ''"
      :status="doc.status || ''"
      :status-tone="leadStatusTone"
      :meta="leadMeta"
    >
      <template #actions>
        <ConnectActions
          record-type="CRM Lead"
          :record-id="leadId"
          :phone="doc.mobile_no || doc.phone || ''"
          show-labels
        />
        <AssignTo
          v-model="assignees.data"
          doctype="CRM Lead"
          :docname="leadId"
        />
        <CustomActions
          v-if="document._actions?.length"
          :actions="document._actions"
        />
        <CustomActions
          v-if="document.actions?.length"
          :actions="document.actions"
        />
        <Dropdown
          v-if="doc"
          :options="
            statusOptions(
              'lead',
              document.statuses?.length
                ? document.statuses
                : document._statuses,
              triggerStatusChange,
            )
          "
        >
          <template #default="{ open }">
            <Button
              v-if="doc.status"
              :label="statusLabel(doc.status)"
              :iconRight="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
            >
              <template #prefix>
                <IndicatorIcon :class="getLeadStatus(doc.status).color" />
              </template>
            </Button>
          </template>
        </Dropdown>
        <Tooltip
          :disabled="!isLeadConversionDisabled"
          :text="__('Cannot convert a lost lead to deal')"
        >
          <div class="inline-flex">
            <AstraButton
              variant="primary"
              size="sm"
              :label="__('Convert')"
              :disabled="isLeadConversionDisabled"
              @click="showConvertToDealModal = true"
            />
          </div>
        </Tooltip>
      </template>
      <template #stage>
        <StagePath
          :stages="leadStages"
          :current="doc.status"
          :dates="stageDates"
          @select="triggerStatusChange"
        />
      </template>
    </AstraRecordHeader>

    <div class="flex min-h-0 flex-1 overflow-hidden">
    <Tabs
      v-model="activeTab"
      as="div"
      :tabs="tabs"
      :class="recordTabsClass({ scroll: true })"
    >
      <template #tab-panel="{ tab }">
        <div v-if="tab.name == 'Details' && !tab.component">
          <SLASection
            v-if="doc.sla_status"
            v-model="doc"
            @updateField="updateField"
          />
          <div
            v-if="sections.data"
            class="flex flex-1 flex-col justify-between overflow-hidden"
          >
            <SidePanelLayout
              :sections="sections.data"
              doctype="CRM Lead"
              :docname="leadId"
              @reload="sections.reload"
              @beforeFieldChange="beforeStatusChange"
              @afterFieldChange="reloadAssignees"
            />
          </div>
        </div>
        <Activities
          v-else
          v-model:reload="reload"
          v-model:activeTab="activeTab"
          doctype="CRM Lead"
          :docname="leadId"
          :tabs="tabs"
          @beforeSave="beforeStatusChange"
          @afterSave="reloadAssignees"
        />
      </template>
    </Tabs>
    </div>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <ConvertToDealModal
    v-if="showConvertToDealModal"
    v-model="showConvertToDealModal"
    :lead="doc"
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'CRM Lead'"
    :docname="leadId"
    :title="doc.lead_name"
    name="Leads"
  />
  <LostReasonModal
    v-if="showLostReasonModal"
    v-model="showLostReasonModal"
    doctype="CRM Lead"
    :document="document"
  />
</template>
<script setup>
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import LostReasonModal from '@/components/Modals/LostReasonModal.vue'
import AstraRecordHeader from '@/components/astra/AstraRecordHeader.vue'
import AstraButton from '@/components/astra/AstraButton.vue'
import { STATUS_TONES } from '@/components/astra/format'
import ConnectActions from '@/components/AstraConnect/ConnectActions.vue'
import StagePath from '@/components/Pipeline/StagePath.vue'
import { recordTabsClass } from '@/components/Pipeline/recordChrome'
import { pipelineStages, stageEnteredOn } from '@/components/Pipeline/stageRail'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import { setupCustomizations, isTranslatable } from '@/utils'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { mergeFormTabs } from '@/utils/formTabs'
import { isMobileView } from '@/composables/settings'
import { whatsappEnabled } from '@/composables/whatsapp'
import { useActiveTabManager } from '@/composables/useActiveTabManager'
import { useVisitedRecords } from '@/composables/useVisitedRecords'
import {
  createResource,
  Dropdown,
  Tooltip,
  Tabs,
  call,
  usePageMeta,
} from 'frappe-ui'
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ConvertToDealModal from '@/components/Modals/ConvertToDealModal.vue'

const { brand } = getSettings()
const { $dialog, $socket } = globalStore()
const { statusOptions, getLeadStatus, leadStatuses } = statusesStore()
const { doctypeMeta } = getMeta('CRM Lead')

const router = useRouter()

const props = defineProps({
  leadId: { type: String, required: true },
})

const errorTitle = ref('')
const errorMessage = ref('')
const showDeleteLinkedDocModal = ref(false)

const {
  triggerOnChange,
  triggerOnRender,
  assignees,
  document,
  scripts,
  error,
} = useDocument('CRM Lead', props.leadId)

const doc = computed(() => document.doc || {})
const isLeadConversionDisabled = computed(
  () => doc.value.status && getLeadStatus(doc.value.status)?.type === 'Lost',
)

const { markVisited } = useVisitedRecords('CRM Lead')

onMounted(async () => {
  if (document.doc) await triggerOnRender()
  markVisited(props.leadId)
})

watch(error, (err) => {
  if (err) {
    errorTitle.value = __(
      err.exc_type == 'DoesNotExistError'
        ? __('Document Not Found')
        : __('Error Occurred'),
    )
    errorMessage.value = __(err.messages?.[0] || 'An Error Occurred')
  } else {
    errorTitle.value = ''
    errorMessage.value = ''
  }
})

watch(
  () => document.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        updateField,
        deleteDoc: deleteLead,
        call,
      })
      document._actions = s.actions || []
      document._statuses = s.statuses || []
    }
  },
  { once: true },
)

const reload = ref(false)

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return doc.value?.[t] || props.leadId
})

const leadMeta = computed(() => {
  const parts = []
  if (doc.value?.job_title) parts.push(doc.value.job_title)
  if (doc.value?.organization) parts.push(doc.value.organization)
  return parts
})

const leadStatusTone = computed(() => STATUS_TONES[doc.value?.status] || 'mute')

const leadStages = computed(() => {
  const allowed = document.statuses?.length ? document.statuses : document._statuses
  return pipelineStages(leadStatuses.data, allowed).map((stage) => ({
    ...stage,
    label: statusLabel(stage.name),
  }))
})

const stageDates = computed(() => stageEnteredOn(doc.value?.status_change_log))

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

const tabs = computed(() => {
  let tabOptions = [
    {
      name: 'Details',
      value: 'details',
      label: __('Details'),
      iconLeft: DetailsIcon,
      condition: () => isMobileView.value,
    },
    {
      name: 'Activity',
      value: 'activity',
      label: __('Activity'),
      iconLeft: ActivityIcon,
    },
    {
      name: 'Emails',
      value: 'emails',
      label: __('Emails'),
      iconLeft: EmailIcon,
    },
    {
      name: 'Comments',
      value: 'comments',
      label: __('Comments'),
      iconLeft: CommentIcon,
    },
    {
      name: 'Data',
      value: 'data',
      label: __('Data'),
      iconLeft: DetailsIcon,
    },
    {
      name: 'Calls',
      value: 'calls',
      label: __('Calls'),
      iconLeft: PhoneIcon,
    },
    {
      name: 'Tasks',
      value: 'tasks',
      label: __('Tasks'),
      iconLeft: TaskIcon,
    },
    {
      name: 'Notes',
      value: 'notes',
      label: __('Notes'),
      iconLeft: NoteIcon,
    },
    {
      name: 'Attachments',
      value: 'attachments',
      label: __('Attachments'),
      iconLeft: AttachmentIcon,
    },
    {
      name: 'WhatsApp',
      value: 'whatsapp',
      label: __('WhatsApp'),
      iconLeft: WhatsAppIcon,
      condition: () => whatsappEnabled.value,
    },
  ]
  return mergeFormTabs(tabOptions, document.tabs)
})

const { activeTab } = useActiveTabManager(tabs, 'lastLeadTab')

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Lead'],
  params: { doctype: 'CRM Lead' },
  auto: true,
})

function updateField(name, value) {
  value = Array.isArray(name) ? '' : value
  let oldValues = Array.isArray(name) ? {} : doc.value[name]

  if (Array.isArray(name)) {
    name.forEach((field) => (doc.value[field] = value))
  } else {
    doc.value[name] = value
  }

  document.save.submit(null, {
    onSuccess: () => (reload.value = true),
    onError: () => {
      if (Array.isArray(name)) {
        name.forEach((field) => (doc.value[field] = oldValues[field]))
      } else {
        doc.value[name] = oldValues
      }
    },
  })
}

function deleteLead() {
  showDeleteLinkedDocModal.value = true
}

// Convert to Deal
const showConvertToDealModal = ref(false)

function statusLabel(status) {
  if (isTranslatable('CRM Lead Status')) return __(status)
  return status
}

async function triggerStatusChange(value) {
  await triggerOnChange('status', value)
  setLostReason()
}

const showLostReasonModal = ref(false)

function setLostReason() {
  if (
    getLeadStatus(doc.value.status).type !== 'Lost' ||
    (doc.value.lost_reason && doc.value.lost_reason !== 'Other') ||
    (doc.value.lost_reason === 'Other' && doc.value.lost_notes)
  ) {
    document.save.submit()
    return
  }

  showLostReasonModal.value = true
}

function beforeStatusChange(data) {
  if (
    Object.hasOwn(data ?? {}, 'status') &&
    getLeadStatus(data.status).type == 'Lost'
  ) {
    setLostReason()
  } else {
    document.save.submit(null, {
      onSuccess: () => reloadAssignees(data),
    })
  }
}
function reloadAssignees(data) {
  if (Object.hasOwn(data ?? {}, 'lead_owner')) {
    assignees.reload()
  }
}
</script>
