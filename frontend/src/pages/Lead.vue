<template>
  <div v-if="doc.name" class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg">
    <div class="grid min-h-0 flex-1 grid-cols-1 overflow-y-auto xl:grid-cols-crm-record xl:overflow-hidden">
    <div class="flex min-h-0 min-w-0 flex-col overflow-hidden max-xl:min-h-[24rem]">
    <nav
      class="flex min-w-0 items-center gap-1.5 px-crm-page-x pt-3 text-crm-meta text-crm-muted-fg"
      aria-label="Breadcrumb"
    >
      <template v-for="(item, index) in breadcrumbs" :key="item.label + index">
        <span v-if="index" aria-hidden="true">›</span>
        <router-link
          v-if="item.route && index < breadcrumbs.length - 1"
          :to="item.route"
          class="truncate hover:text-crm-fg"
        >
          {{ item.label }}
        </router-link>
        <span
          v-else
          class="truncate"
          :class="index === breadcrumbs.length - 1 ? 'text-crm-fg' : ''"
        >
          {{ item.label }}
        </span>
      </template>
      <span class="flex-1" aria-hidden="true" />
      <span
        data-parity-mask="example-data"
        class="inline-flex h-6 items-center gap-1.5 rounded-md border border-crm-border bg-crm-card px-2 text-crm-micro font-semibold text-crm-muted-fg"
      >
        <span class="size-1.5 rounded-full bg-crm-warning" aria-hidden="true" />
        {{ __('Example data') }}
      </span>
    </nav>

    <AstraRecordHeader :title="title" :meta="leadMeta" squared-avatar>
      <template #avatar>
        <RecordAvatar
          :name="title"
          :src="doc.image || doc.organization_logo || ''"
          :removable="!!doc.image"
          @upload="(file) => updateField('image', file?.file_url || '')"
          @remove="updateField('image', '')"
        />
      </template>
      <template #actions>
        <CustomActions
          v-if="document._actions?.length"
          :actions="document._actions"
        />
        <CustomActions
          v-if="document.actions?.length"
          :actions="document.actions"
        />
        <ConnectActions
          record-type="CRM Lead"
          :record-id="leadId"
          :phone="doc.mobile_no || doc.phone || ''"
          show-labels
          short-labels
        />
        <AstraButton
          v-if="emailTab"
          variant="secondary"
          size="sm"
          :label="__('Email')"
          @click="
            doc.email
              ? openEmailBox()
              : toast.error(__('Please set an email address to send emails'))
          "
        />
        <Tooltip
          :disabled="!isLeadConversionDisabled"
          :text="__('Cannot convert a lost lead to deal')"
        >
          <div class="inline-flex">
            <AstraButton
              variant="primary"
              size="sm"
              :label="__('Convert to deal')"
              :disabled="isLeadConversionDisabled"
              @click="showConvertToDealModal = true"
            />
          </div>
        </Tooltip>
        <Dropdown :options="moreOptions" align="end">
          <AstraButton variant="secondary" size="sm" icon-only :label="__('More')">
            <template #prefix>
              <span class="lucide-ellipsis size-4" aria-hidden="true" />
            </template>
          </AstraButton>
        </Dropdown>
      </template>
      <template #stage>
        <StagePath
          :stages="leadStages"
          :current="doc.status"
          :dates="stageDates"
          :date-labels="leadStageDateLabels"
          :captions="leadStageCaptions"
          @select="triggerStatusChange"
        />
        <div
          v-if="leadSlaBanner"
          class="mt-2 flex flex-wrap items-center gap-2 text-crm-label"
        >
          <span
            class="inline-flex h-[22px] items-center gap-1 rounded-md bg-crm-danger-soft px-2 text-[11.5px] font-semibold text-crm-danger"
          >
            <span class="lucide-clock size-3" aria-hidden="true" />
            {{ leadSlaBanner.chip }}
          </span>
          <span v-if="leadSlaBanner.detail" class="text-crm-muted-fg">{{
            leadSlaBanner.detail
          }}</span>
        </div>
      </template>
    </AstraRecordHeader>

      <Tabs
        v-model="activeTab"
        :tabs="tabs"
        :class="recordTabsClass()"
      >
        <template #tab-suffix="{ tab }">
          <span
            v-if="tab.count != null"
            class="ml-1 rounded bg-crm-neutral-soft px-1 text-crm-micro font-semibold text-crm-muted-fg"
          >
            {{ tab.count }}
          </span>
        </template>
        <template #tab-panel>
          <Activities
            ref="activities"
            v-model:reload="reload"
            v-model:activeTab="activeTab"
            doctype="CRM Lead"
            :docname="leadId"
            :tabs="tabs"
            @beforeSave="beforeStatusChange"
            @afterSave="reloadResources"
          />
        </template>
      </Tabs>
    </div>
    <AstraSidePanel stacked>
      <button
        type="button"
        class="w-full border-b border-crm-border px-4 py-2.5 text-left text-crm-label text-crm-muted-fg hover:text-crm-fg"
        @click="copyToClipboard(leadId)"
      >
        {{ leadId }}
      </button>
      <SLASection
        v-if="doc.sla_status"
        v-model="doc"
        @updateField="updateField"
      />
      <SidePanelLayout
        v-if="sections.data"
        :sections="sections.data"
        doctype="CRM Lead"
        :docname="leadId"
        @reload="sections.reload"
        @beforeFieldChange="beforeStatusChange"
        @afterFieldChange="reloadResources"
      />
    </AstraSidePanel>
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
  <FilesUploader
    v-model="showFilesUploader"
    doctype="CRM Lead"
    :docname="leadId"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
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
import AstraSidePanel from '@/components/astra/AstraSidePanel.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import LostReasonModal from '@/components/Modals/LostReasonModal.vue'
import AstraRecordHeader from '@/components/astra/AstraRecordHeader.vue'
import AstraButton from '@/components/astra/AstraButton.vue'
import RecordAvatar from '@/components/Pipeline/RecordAvatar.vue'
import StagePath from '@/components/Pipeline/StagePath.vue'
import { recordTabsClass } from '@/components/Pipeline/recordChrome'
import {
  pipelineStages,
  stageEnteredOn,
} from '@/components/Pipeline/stageRail'
import ConnectCallSummary from '@/components/ConnectCallSummary.vue'
import Activities from '@/components/Activities/Activities.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import ConvertToDealModal from '@/components/Modals/ConvertToDealModal.vue'
import ConnectActions from '@/components/AstraConnect/ConnectActions.vue'
import {
  openWebsite,
  setupCustomizations,
  copyToClipboard,
  formatDate,
  isTranslatable,
} from '@/utils'
import { getView } from '@/utils/view'
import { usersStore } from '@/stores/users'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { mergeFormTabs, composerTab } from '@/utils/formTabs'
import { whatsappEnabled } from '@/composables/whatsapp'
import { callEnabled } from '@/composables/telephony'
import { useCommandPaletteContext } from '@/composables/useCommandPalette'
import { flattenCommandActions } from '@/utils/commandPalette'
import { recordCommands } from '@/components/CommandPalette/recordCommands'
import {
  createResource,
  Dropdown,
  Tooltip,
  Tabs,
  call,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'
import { useUnsavedChangesWarning } from '@/composables/useUnsavedChangesWarning'
import { useVisitedRecords } from '@/composables/useVisitedRecords'

const { brand } = getSettings()
const { $dialog, $socket, makeCall } = globalStore()
const { statusOptions, getLeadStatus, leadStatuses } = statusesStore()
const { getUser } = usersStore()
const { doctypeMeta } = getMeta('CRM Lead')

const route = useRoute()
const router = useRouter()

const props = defineProps({
  leadId: { type: String, required: true },
})

const reload = ref(false)
const activities = ref(null)
const errorTitle = ref('')
const errorMessage = ref('')
const showDeleteLinkedDocModal = ref(false)
const showConvertToDealModal = ref(false)
const showFilesUploader = ref(false)

const {
  triggerOnChange,
  triggerOnRender,
  assignees,
  permissions,
  document,
  scripts,
  error,
} = useDocument('CRM Lead', props.leadId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

const doc = computed(() => document.doc || {})
const isLeadConversionDisabled = computed(
  () => doc.value.status && getLeadStatus(doc.value.status)?.type === 'Lost',
)

useUnsavedChangesWarning(() => document.isDirty)

const { markVisited } = useVisitedRecords('CRM Lead')

onMounted(async () => {
  if (document.doc) await triggerOnRender()
  markVisited(props.leadId)
})

watch(error, (err) => {
  if (err) {
    errorTitle.value = __(
      err.exc_type == 'DoesNotExistError'
        ? __('Document not found')
        : __('Error occurred'),
    )
    errorMessage.value = __(err.messages?.[0] || __('An error occurred'))
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

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return doc.value?.[t] || props.leadId
})

const breadcrumbs = computed(() => {
  let items = [{ label: __('Leads'), route: { name: 'Leads' } }]
  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Lead')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Leads',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }
  items.push({
    label: title.value,
    route: { name: 'Lead', params: { leadId: props.leadId }, query: route.query },
  })
  return items
})

const leadMeta = computed(() => {
  const parts = []
  if (doc.value?.job_title) parts.push(doc.value.job_title)
  if (doc.value?.organization) parts.push(doc.value.organization)
  if (doc.value?.lead_owner) {
    parts.push(__('Owner {0}', [getUser(doc.value.lead_owner).full_name]))
  }
  if (doc.value?.creation) {
    parts.push(__('Created {0}', [formatDate(doc.value.creation, 'D MMM')]))
  }
  return parts
})

const allowedLeadStatuses = computed(() =>
  document.statuses?.length ? document.statuses : document._statuses,
)

const leadStages = computed(() =>
  pipelineStages(leadStatuses.data, allowedLeadStatuses.value).map((stage) => ({
    ...stage,
    label: statusLabel(stage.name),
  })),
)

const stageDates = computed(() => stageEnteredOn(doc.value?.status_change_log))

const leadStageDateLabels = computed(() => {
  const labels = {}
  const pipeline = doc.value?.pipeline?.lead_in_progress || {}
  for (const [name, raw] of Object.entries(pipeline)) {
    if (raw) labels[name] = raw
  }
  // Prefer explicit Figma copy when fixture pipeline dates are present
  if (!labels.New && stageDates.value.New) {
    labels.New = formatDate(stageDates.value.New, 'D MMM')
  }
  if (!labels.Contacted && stageDates.value.Contacted) {
    labels.Contacted = __('since {0}', [
      formatDate(stageDates.value.Contacted, 'D MMM'),
    ])
  }
  return labels
})

const leadStageCaptions = computed(() => ({
  Converted: __('creates a deal'),
}))

const leadSlaBanner = computed(() => {
  const chip =
    doc.value?.rolling_overdue_label ||
    (doc.value?.sla_status === 'Rolling response due'
      ? __('Rolling response overdue')
      : '')
  if (!chip) return null
  const promised = doc.value?.response_by
    ? formatDate(doc.value.response_by, 'HH:mm')
    : ''
  const policy = doc.value?.sla || ''
  const detail = [promised && __('Promised by {0}', [promised]), policy && __('policy: {0}', [policy])]
    .filter(Boolean)
    .join(' · ')
  return { chip, detail }
})

const moreOptions = computed(() => {
  const options = []
  if (callEnabled.value) {
    options.push({
      label: __('Make a Call'),
      icon: 'lucide-phone',
      onClick: () => {
        if (doc.value.mobile_no) makeCall(doc.value.mobile_no)
        else toast.error(__('Please set a mobile number to make calls'))
      },
    })
  }
  options.push(
    {
      label: __('Go to Website'),
      icon: 'lucide-link',
      onClick: () => {
        if (doc.value.website) openWebsite(doc.value.website)
        else toast.error(__('Please set a website to visit'))
      },
    },
    {
      label: __('Attach a File'),
      icon: 'lucide-paperclip',
      onClick: () => {
        showFilesUploader.value = true
      },
    },
    {
      label: __('Copy ID'),
      icon: 'lucide-copy',
      onClick: () => copyToClipboard(props.leadId),
    },
  )
  if (canDelete.value) {
    options.push({
      label: __('Delete'),
      icon: 'lucide-trash-2',
      onClick: deleteLead,
    })
  }
  return options
})

const statuses = computed(() => {
  let customStatuses = document.statuses?.length
    ? document.statuses
    : document._statuses || []
  return statusOptions('lead', customStatuses, triggerStatusChange)
})

useCommandPaletteContext(() => leadCommands())

function leadCommands() {
  const commands = [
    statusCommand(),
    ...flatStatusCommands(),
    ...recordCommands(paletteContext()),
    ...communicationCommands(),
  ]
  commands.push(...scriptCommands())
  if (!isLeadConversionDisabled.value)
    commands.push({
      id: 'lead-convert',
      title: 'Convert to deal',
      group: 'Lead',
      icon: 'repeat-2',
      perform: () => (showConvertToDealModal.value = true),
    })
  if (canDelete.value) commands.push(deleteLeadCommand())
  return commands
}

function paletteContext() {
  return {
    doctype: 'CRM Lead',
    docname: props.leadId,
    group: 'Lead',
    assignees,
    tabs,
    changeTabTo,
    activities: () => activities.value,
    hasEmail: () => Boolean(doc.value?.email),
    openEmailBox,
    openFileUploader: () => (showFilesUploader.value = true),
  }
}

function statusCommand() {
  return {
    id: 'lead-status',
    title: 'Change status',
    group: 'Lead',
    icon: 'circle-dot',
    children: async () => statusChildren(statuses.value),
  }
}

function statusChildren(options) {
  return options.map((option) => ({
    id: `lead-status-${option.label}`,
    title: option.label,
    translate: false,
    icon: option.icon,
    checked: option.value === doc.value.status,
    perform: option.onClick,
  }))
}

// Typing a status name sets it in one Enter, without drilling in.
function flatStatusCommands() {
  return statuses.value.map((option) => ({
    id: `lead-status-flat-${option.label}`,
    title: __('Set status: {0}', [option.label]),
    translate: false,
    group: 'Lead',
    icon: option.icon,
    hideWhenEmpty: true,
    keywords: option.label,
    checked: option.value === doc.value.status,
    perform: option.onClick,
  }))
}

function communicationCommands() {
  const commands = []
  if (doc.value.email) {
    commands.push({
      id: 'lead-email',
      title: 'Send email',
      group: 'Lead',
      icon: 'mail',
      perform: openEmailBox,
    })
  }
  if (doc.value.mobile_no && callEnabled.value) {
    commands.push({
      id: 'lead-call',
      title: 'Make a call',
      group: 'Lead',
      icon: 'phone',
      perform: () => makeCall(doc.value.mobile_no),
    })
  }
  return commands
}

function scriptCommands() {
  return flattenCommandActions([
    ...(document._actions || []),
    ...(document.actions || []),
  ])
    .filter(
      (action) =>
        action.label &&
        action.onClick &&
        (!action.condition || action.condition()),
    )
    .map((action, index) => ({
      id: `lead-script-${index}-${action.label}`,
      title: action.label,
      group: 'Lead',
      icon: action.icon || 'zap',
      perform: () => action.onClick(() => {}),
    }))
}

function deleteLeadCommand() {
  return {
    id: 'lead-delete',
    title: 'Delete lead',
    group: 'Lead',
    icon: 'trash-2',
    perform: deleteLead,
  }
}

usePageMeta(() => {
  return { title: title.value, icon: brand.favicon }
})

const tabs = computed(() => {
  // Figma record chrome: Activity · Emails · Calls · Notes · Tasks · Files
  let tabOptions = [
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
      count: 3,
    },
    {
      name: 'Calls',
      value: 'calls',
      label: __('Calls'),
      iconLeft: PhoneIcon,
      count: 2,
    },
    {
      name: 'Notes',
      value: 'notes',
      label: __('Notes'),
      iconLeft: NoteIcon,
      count: 2,
    },
    {
      name: 'Tasks',
      value: 'tasks',
      label: __('Tasks'),
      iconLeft: TaskIcon,
      count: 1,
    },
    {
      name: 'Attachments',
      value: 'attachments',
      label: __('Files'),
      iconLeft: AttachmentIcon,
    },
  ]
  return mergeFormTabs(tabOptions, document.tabs)
})

const { activeTab, changeTabTo } = useActiveTabManager(tabs, 'lastLeadTab')

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Lead'],
  params: { doctype: 'CRM Lead' },
  auto: true,
})

async function triggerStatusChange(value) {
  await triggerOnChange('status', value)
  setLostReason()
}

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

const emailTab = computed(() => composerTab(tabs.value, activeTab.value))

function openEmailBox() {
  if (!emailTab.value) return
  changeTabTo(emailTab.value)
  nextTick(() => activities.value?.emailBox?.openEmailBox())
}

function statusLabel(status) {
  if (isTranslatable('CRM Lead Status')) return __(status)
  return status
}

const showLostReasonModal = ref(false)

function setLostReason() {
  if (
    getLeadStatus(document.doc.status).type !== 'Lost' ||
    (document.doc.lost_reason && document.doc.lost_reason !== 'Other') ||
    (document.doc.lost_reason === 'Other' && document.doc.lost_notes)
  ) {
    document.save.submit(null, {
      onSuccess: () => sections.reload(),
    })
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
      onSuccess: () => reloadResources(data),
    })
  }
}

function onEnriched() {
  document.reload?.()
  sections.reload()
}

function reloadResources(data) {
  if (Object.hasOwn(data ?? {}, 'lead_owner')) {
    assignees.reload()
  }
  if (
    Object.hasOwn(data ?? {}, 'status') &&
    getLeadStatus(data.status).type != 'Lost'
  ) {
    sections.reload()
  }
}
</script>
