<template>
  <div
    v-if="contact.doc"
    class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg"
  >
    <div
      class="grid min-h-0 flex-1 grid-cols-1 overflow-y-auto xl:grid-cols-crm-record xl:overflow-hidden"
    >
      <div
        class="flex min-h-0 min-w-0 flex-col overflow-hidden max-xl:min-h-[24rem]"
      >
        <!-- Figma .rhead: crumb + identity + KPIs -->
        <header
          class="flex flex-col gap-3.5 border-b border-crm-border bg-crm-card px-crm-page-x pb-3.5 pt-4"
        >
          <nav
            class="flex min-w-0 items-center gap-1.5 text-[12.5px] text-crm-muted-fg"
            aria-label="Breadcrumb"
          >
            <router-link :to="{ name: 'Contacts' }" class="hover:text-crm-fg">
              {{ __('Contacts') }}
            </router-link>
            <span
              class="lucide-chevron-right size-3.5 shrink-0"
              aria-hidden="true"
            />
            <span class="truncate font-semibold text-crm-fg">{{ title }}</span>
            <span class="flex-1" aria-hidden="true" />
            <span
              data-parity-mask="example-data"
              class="inline-flex h-6 items-center gap-1.5 rounded-md border border-dashed border-crm-border-strong px-[9px] text-[11.5px] font-medium text-crm-muted-fg"
            >
              <span
                class="size-1.5 rounded-full bg-crm-warning"
                aria-hidden="true"
              />
              {{ __('Example data') }}
            </span>
          </nav>

          <div class="flex items-center gap-3">
            <RecordAvatar
              :name="title"
              :src="contact.doc.image || ''"
              :removable="!!contact.doc.image"
              @upload="changeContactImage"
              @remove="changeContactImage('')"
            />
            <div class="min-w-0">
              <h1
                class="m-0 text-[19px] font-semibold tracking-[-0.015em] text-crm-fg"
              >
                {{ title }}
              </h1>
              <div
                class="mt-0.5 flex flex-wrap items-center gap-2.5 whitespace-nowrap text-[12.5px] text-crm-muted-fg"
              >
                <template
                  v-for="(item, index) in contactMetaItems"
                  :key="item.key"
                >
                  <span
                    v-if="index"
                    class="size-[3px] rounded-full bg-crm-faint"
                    aria-hidden="true"
                  />
                  <span>{{ item.label }}</span>
                </template>
              </div>
            </div>
            <span class="min-w-0 flex-1" aria-hidden="true" />
            <div class="flex shrink-0 flex-wrap items-center gap-2 -translate-x-6">
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
                short-labels
                size="sm"
              />
              <AstraButton
                variant="secondary"
                size="sm"
                :label="__('Message')"
                @click="openMessage"
              >
                <template #prefix>
                  <span
                    class="lucide-message-circle size-3.5"
                    aria-hidden="true"
                  />
                </template>
                <template #suffix>
                  <span
                    class="lucide-external-link size-3.5"
                    aria-hidden="true"
                  />
                </template>
              </AstraButton>
              <AstraButton
                variant="secondary"
                size="sm"
                :label="__('Email')"
                @click="
                  contact.doc.email_id || contact.doc.email
                    ? toast.info(__('Compose email'))
                    : toast.error(__('Please set an email address'))
                "
              >
                <template #prefix>
                  <span class="lucide-mail size-3.5" aria-hidden="true" />
                </template>
              </AstraButton>
              <Dropdown :options="moreOptions" align="end">
                <AstraButton
                  variant="secondary"
                  size="sm"
                  icon-only
                  :label="__('More')"
                >
                  <template #prefix>
                    <span class="lucide-ellipsis size-4" aria-hidden="true" />
                  </template>
                </AstraButton>
              </Dropdown>
            </div>
          </div>

          <div class="grid grid-cols-4 gap-2.5">
            <div
              v-for="kpi in contactKpis"
              :key="kpi.label"
              class="rounded-[10px] border border-crm-border bg-crm-card px-3 py-2.5"
            >
              <div class="text-[12px] text-crm-muted-fg">{{ kpi.label }}</div>
              <div
                class="mt-1 text-[18px] font-semibold tabular-nums tracking-crm-num text-crm-fg"
              >
                {{ kpi.value }}
              </div>
              <div class="mt-0.5 text-[11.5px] text-crm-muted-fg">
                {{ kpi.detail }}
              </div>
            </div>
          </div>
        </header>

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
              class="ml-1 rounded bg-crm-neutral-soft px-1 text-crm-micro font-semibold text-crm-muted-fg"
            >
              {{ tab.count }}
            </span>
          </template>
          <template #tab-panel="{ tab }">
            <div
              v-if="tab.value === 'deals'"
              class="flex flex-col gap-3.5 px-crm-page-x py-3.5"
            >
              <section
                class="overflow-hidden rounded-[10px] border border-crm-border bg-crm-card"
              >
                <table
                  class="w-full border-collapse text-[12.5px] [&_tbody_tr:last-child_td]:border-b-0"
                >
                  <thead>
                    <tr>
                      <th
                        v-for="col in contactDealColumns"
                        :key="col.key"
                        class="h-[34px] whitespace-nowrap border-b border-crm-border bg-crm-muted px-2.5 text-left text-[11.5px] font-semibold uppercase tracking-[0.04em] text-crm-muted-fg"
                        :class="{ 'text-right': col.align === 'right' }"
                      >
                        {{ col.label }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="row in contactDealRows"
                      :key="row.name"
                      class="cursor-pointer hover:bg-crm-row-hover"
                      @click="
                        router.push({
                          name: 'Deal',
                          params: { dealId: row.name },
                        })
                      "
                    >
                      <td
                        class="h-11 whitespace-nowrap border-b border-crm-border px-2.5 font-semibold text-crm-fg"
                      >
                        {{ row.deal_name }}
                      </td>
                      <td
                        class="h-11 whitespace-nowrap border-b border-crm-border px-2.5"
                      >
                        <span
                          class="inline-flex h-[22px] items-center gap-1.5 whitespace-nowrap rounded-md px-2 text-[11.5px] font-semibold"
                          :class="
                            row.statusTone === 'success'
                              ? 'bg-crm-success-soft text-crm-success'
                              : row.statusTone === 'danger'
                                ? 'bg-crm-danger-soft text-crm-danger'
                                : 'bg-crm-neutral-soft text-crm-fg'
                          "
                        >
                          <i
                            class="size-[7px] shrink-0 rounded-[2px]"
                            :style="{ backgroundColor: row.statusDot }"
                            aria-hidden="true"
                          />
                          {{ row.status }}
                        </span>
                      </td>
                      <td
                        class="h-11 whitespace-nowrap border-b border-crm-border px-2.5 text-right font-semibold tabular-nums text-crm-fg"
                      >
                        {{ row.value }}
                      </td>
                      <td
                        class="h-11 whitespace-nowrap border-b border-crm-border px-2.5 tabular-nums text-crm-fg"
                      >
                        {{ row.closeDate }}
                      </td>
                      <td
                        class="h-11 whitespace-nowrap border-b border-crm-border px-2.5"
                      >
                        <AstraBadge
                          v-if="row.role === 'Primary'"
                          :label="__('Primary')"
                          tone="info"
                        />
                        <span v-else class="text-crm-muted-fg">{{
                          row.role
                        }}</span>
                      </td>
                      <td
                        class="h-11 whitespace-nowrap border-b border-crm-border px-2.5"
                      >
                        <AstraAvatar :name="row.ownerName" size="sm" />
                      </td>
                    </tr>
                    <tr v-if="!contactDealRows.length">
                      <td
                        colspan="6"
                        class="px-2.5 py-8 text-center text-crm-muted-fg"
                      >
                        {{ __('No deals yet') }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </section>

              <section
                class="overflow-hidden rounded-[10px] border border-crm-border bg-crm-card"
              >
                <header
                  class="flex items-center gap-2.5 px-[18px] py-3.5"
                >
                  <h2
                    class="m-0 text-[14px] font-semibold tracking-[-0.005em] text-crm-fg"
                  >
                    {{ __('Recent conversation') }}
                  </h2>
                  <span class="text-[12.5px] font-normal text-crm-muted-fg">
                    {{ __('calls, emails and messages · read-only') }}
                  </span>
                  <span class="flex-1" aria-hidden="true" />
                  <button
                    type="button"
                    class="inline-flex items-center gap-0.5 text-[12.5px] font-semibold text-crm-primary hover:underline"
                    @click="activeTab = 'activity'"
                  >
                    {{ __('Conversations') }}
                    <span
                      class="lucide-chevron-right size-3.5"
                      aria-hidden="true"
                    />
                  </button>
                </header>
                <div
                  v-for="item in recentConversations"
                  :key="item.name"
                  class="flex items-center gap-2.5 border-t border-crm-border px-4 py-[9px] text-[12.5px]"
                >
                  <span
                    class="inline-flex h-[18px] shrink-0 items-center gap-1 rounded px-1.5 text-[10.5px] font-semibold"
                    :class="conversationChipClass(item.type)"
                  >
                    <svg
                      class="size-[11px]"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      aria-hidden="true"
                    >
                      <template
                        v-if="String(item.type).toLowerCase() === 'call'"
                      >
                        <path
                          d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"
                        />
                      </template>
                      <template
                        v-else-if="
                          String(item.type).toLowerCase() === 'whatsapp'
                        "
                      >
                        <path d="M3 21l1.6-4.8A8.5 8.5 0 1 1 8 19.6z" />
                      </template>
                      <template v-else>
                        <rect x="2" y="4" width="20" height="16" rx="2" />
                        <path d="m22 7-10 6L2 7" />
                      </template>
                    </svg>
                    {{ item.type }}
                  </span>
                  <div class="min-w-0 flex-1">
                    <div class="truncate font-semibold text-crm-fg">
                      <template
                        v-if="String(item.type).toLowerCase() === 'whatsapp'"
                      >
                        “{{ item.title }}”
                      </template>
                      <template v-else>{{ item.title }}</template>
                    </div>
                    <div class="truncate text-[11.5px] text-crm-muted-fg">
                      {{ item.meta }}
                    </div>
                  </div>
                  <button
                    v-if="item.action"
                    type="button"
                    class="inline-flex items-center gap-0.5 text-[12.5px] font-semibold text-crm-primary hover:underline"
                  >
                    {{ item.action }}
                    <span
                      class="lucide-external-link size-3.5"
                      aria-hidden="true"
                    />
                  </button>
                </div>
              </section>
            </div>
            <Activities
              v-else-if="tab.value === 'activity'"
              ref="activitiesRef"
              v-model:activeTab="activityTab"
              doctype="Contact"
              :docname="contact.doc.name"
              :tabs="activityTabs"
            />
            <div
              v-else
              class="px-crm-page-x py-6 text-crm-label text-crm-muted-fg"
            >
              {{ __('No {0} yet', [tab.label]) }}
            </div>
          </template>
        </Tabs>
      </div>

      <AstraSidePanel stacked class="-translate-x-px">
        <section class="border-b border-crm-border">
          <header
            class="flex items-center gap-2 px-4 pb-1 pt-3 text-[12px] font-bold text-crm-fg"
          >
            <span>{{ __('Details') }}</span>
            <span class="flex-1" aria-hidden="true" />
            <button
              type="button"
              class="text-[12px] font-semibold text-crm-primary hover:underline"
              @click="sections.reload()"
            >
              {{ __('Edit') }}
            </button>
          </header>
          <dl
            class="grid grid-cols-[118px_minmax(0,1fr)] gap-x-2.5 gap-y-2 px-4 pb-3.5 pt-2 text-[12.5px]"
          >
            <dt class="text-crm-muted-fg">{{ __('Salutation') }}</dt>
            <dd class="truncate">{{ contact.doc.salutation || '—' }}</dd>
            <dt class="text-crm-muted-fg">{{ __('First name') }}</dt>
            <dd class="truncate">{{ contact.doc.first_name || '—' }}</dd>
            <dt class="text-crm-muted-fg">{{ __('Last name') }}</dt>
            <dd class="truncate">{{ contact.doc.last_name || '—' }}</dd>
            <dt class="text-crm-muted-fg">{{ __('Designation') }}</dt>
            <dd class="truncate">{{ contact.doc.designation || '—' }}</dd>
            <dt class="text-crm-muted-fg">{{ __('Gender') }}</dt>
            <dd class="truncate text-crm-faint">
              {{ contact.doc.gender || __('Not set') }}
            </dd>
          </dl>
        </section>
        <section class="border-b border-crm-border">
          <header
            class="flex items-center gap-2 px-4 pb-1 pt-3 text-[12px] font-bold text-crm-fg"
          >
            <span>{{ __('Reach') }}</span>
            <span class="flex-1" aria-hidden="true" />
            <button
              type="button"
              class="inline-flex items-center gap-0.5 text-[12px] font-semibold text-crm-primary hover:underline"
            >
              <span class="lucide-plus size-3.5" aria-hidden="true" />
              {{ __('Add') }}
            </button>
          </header>
          <dl
            class="grid grid-cols-[118px_minmax(0,1fr)] gap-x-2.5 gap-y-2 px-4 pb-3.5 pt-2 text-[12.5px]"
          >
            <dt class="text-crm-muted-fg">{{ __('Email') }}</dt>
            <dd class="flex min-w-0 items-center gap-1.5 whitespace-nowrap">
              <span>{{
                contact.doc.email_id || contact.doc.email || '—'
              }}</span>
              <AstraBadge
                class="shrink-0"
                :label="__('Primary')"
                tone="info"
              />
            </dd>
            <dt class="text-crm-muted-fg">{{ __('Mobile') }}</dt>
            <dd class="truncate tabular-nums">
              {{ contact.doc.mobile_no || '—' }}
            </dd>
            <dt class="text-crm-muted-fg">{{ __('Phone') }}</dt>
            <dd class="truncate tabular-nums">
              {{ contact.doc.phone || '—' }}
            </dd>
            <dt class="text-crm-muted-fg">{{ __('WhatsApp') }}</dt>
            <dd>
              <span
                v-if="contact.doc.whatsapp || contact.doc.channels === 'WhatsApp'"
                class="inline-flex h-[18px] items-center gap-1 rounded bg-crm-success-soft px-1.5 text-[10.5px] font-semibold text-crm-success"
              >
                <svg
                  class="size-[11px]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  aria-hidden="true"
                >
                  <path d="M3 21l1.6-4.8A8.5 8.5 0 1 1 8 19.6z" />
                </svg>
                {{ contact.doc.whatsapp || __('Active · Astra Connect') }}
              </span>
              <span v-else>—</span>
            </dd>
          </dl>
        </section>
        <section class="border-b border-crm-border">
          <header class="px-4 pb-1 pt-3 text-[12px] font-bold text-crm-fg">
            {{ __('Company') }}
          </header>
          <div class="flex items-center gap-[9px] px-4 pb-3 pt-1.5">
            <AstraAvatar
              :name="contact.doc.company_name || 'Org'"
              tone="company"
              squared
            />
            <div class="flex min-w-0 flex-col leading-[1.3]">
              <b class="truncate font-semibold text-crm-fg">{{
                contact.doc.company_name || '—'
              }}</b>
              <span class="truncate text-[11.5px] text-crm-muted-fg">
                {{ companySubtitle }}
              </span>
            </div>
          </div>
        </section>
        <section class="border-0">
          <header class="px-4 pb-1 pt-3 text-[12px] font-bold text-crm-fg">
            {{ __('Address') }}
          </header>
          <div
            class="whitespace-pre-line px-4 pb-3.5 pt-1.5 text-[12.5px] leading-[1.5] text-crm-fg"
          >
            {{ addressText }}
          </div>
        </section>
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
    :docname="contact.doc?.name || props.contactId"
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
import Activities from '@/components/Activities/Activities.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import DealModal from '@/components/Modals/DealModal.vue'
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import CustomActions from '@/components/CustomActions.vue'
import ConnectActions from '@/components/AstraConnect/ConnectActions.vue'
import RecordAvatar from '@/components/Pipeline/RecordAvatar.vue'
import { recordTabsClass } from '@/components/Pipeline/recordChrome'
import AstraButton from '@/components/astra/AstraButton.vue'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import AstraBadge from '@/components/astra/AstraBadge.vue'
import { formatInrAmount, stageToken } from '@/components/astra/format'
import { setupCustomizations } from '@/utils'
import { openConnectCompose } from '@/utils/astraConnect'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { statusesStore } from '@/stores/statuses'
import {
  Tabs,
  call,
  createResource,
  usePageMeta,
  toast,
  Dropdown,
} from 'frappe-ui'
import { useTelemetry } from '@framework/ui/telemetry'
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const { brand } = getSettings()
const { $dialog, $socket } = globalStore()
const { getUser } = usersStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('Contact')
const { capture } = useTelemetry()
const router = useRouter()

const props = defineProps({
  contactId: { type: String, required: true },
})

const errorTitle = ref('')
const errorMessage = ref('')
const showDeleteLinkedDocModal = ref(false)
const showDealModal = ref(false)
const dealDefaults = ref({})
const activitiesRef = ref(null)
const activityTab = ref('activity')
const activeTab = ref('deals')

const {
  document: contact,
  permissions,
  scripts,
  triggerOnRender,
} = useDocument('Contact', props.contactId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

onMounted(async () => {
  if (contact.doc) await triggerOnRender()
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return contact.doc?.[t] || props.contactId
})

const contactMetaItems = computed(() => {
  const doc = contact.doc || {}
  const items = []
  if (doc.designation) items.push({ key: 'role', label: doc.designation })
  if (doc.company_name)
    items.push({ key: 'company', label: doc.company_name })
  if (doc.city) items.push({ key: 'city', label: doc.city })
  return items
})

const companySubtitle = computed(() => {
  const doc = contact.doc || {}
  const bits = ['Logistics']
  if (doc.city) bits.push(doc.city)
  return bits.join(' · ')
})

const addressText = computed(() => {
  const doc = contact.doc || {}
  const lines = [doc.address_display, doc.address_line].filter(Boolean)
  return lines.length ? lines.join('\n') : '—'
})

function inr(value) {
  if (value == null || value === '') return ''
  return formatInrAmount(value)
}

const contactKpis = computed(() => {
  const doc = contact.doc || {}
  return [
    {
      label: __('Open deals'),
      value: String(doc.open_deals_count ?? 0),
      detail: __('{0} · {1}', [
        inr(doc.open_deals_value) || '—',
        doc.open_deals_stage || '—',
      ]),
    },
    {
      label: __('Won with us'),
      value: inr(doc.won_value) || '—',
      detail: doc.won_label || __('—'),
    },
    {
      label: __('Calls · 30 days'),
      value: String(doc.calls_30d ?? 0),
      detail: __('avg {0}', [doc.calls_avg || '—']),
    },
    {
      label: __('Last touch'),
      value: doc.last_touch || '—',
      detail: doc.last_touch_type || '',
    },
  ]
})

const moreOptions = computed(() => {
  const options = [
    {
      label: __('New Deal'),
      icon: 'lucide-plus',
      onClick: openDealModal,
    },
  ]
  if (canDelete.value) {
    options.push({
      label: __('Delete'),
      icon: 'lucide-trash-2',
      onClick: deleteContact,
    })
  }
  return options
})

usePageMeta(() => ({
  title: title.value,
  icon: brand.favicon,
}))

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
    onSuccess: () => toast.success(__('Contact image updated')),
  })
}

function openMessage() {
  openConnectCompose('messages', {
    recordType: 'Contact',
    recordId: contact.doc.name,
    phone: contact.doc.mobile_no || undefined,
  })
}

const activityTabs = [
  {
    name: 'Activity',
    value: 'activity',
    label: __('Activity'),
    iconLeft: ActivityIcon,
  },
]

const tabs = computed(() => [
  { value: 'activity', label: __('Activity') },
  {
    value: 'deals',
    label: __('Deals'),
    count: contactDealRows.value.length || 2,
  },
  { value: 'emails', label: __('Emails'), count: 9 },
  { value: 'calls', label: __('Calls'), count: 4 },
  { value: 'notes', label: __('Notes'), count: 1 },
])

const deals = createResource({
  url: 'crm.api.contact.get_linked_deals',
  cache: ['deals', props.contactId],
  params: { contact: props.contactId },
  auto: true,
})

const conversations = createResource({
  url: 'crm.api.activities.get_conversations',
  cache: ['conversations', props.contactId],
  params: { name: props.contactId },
  auto: true,
})

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'Contact'],
  params: { doctype: 'Contact' },
  auto: true,
})

const contactDealColumns = [
  { key: 'deal', label: __('Deal') },
  { key: 'stage', label: __('Stage') },
  { key: 'value', label: __('Value'), align: 'right' },
  { key: 'close', label: __('Expected / closed') },
  { key: 'role', label: __('Role') },
  { key: 'owner', label: __('Owner') },
]

function formatCloseDate(value) {
  if (!value) return '—'
  const d = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function dealStatusTone(status) {
  const type = getDealStatus(status)?.type || ''
  if (type === 'Won' || status === 'Won') return 'success'
  if (type === 'Lost' || status === 'Lost') return 'danger'
  return 'mute'
}

const contactDealRows = computed(() => {
  const raw = deals.data
  const list = Array.isArray(raw) ? raw : Array.isArray(raw?.message) ? raw.message : []
  return list.map((deal) => {
    const owner = deal.deal_owner ? getUser(deal.deal_owner) : null
    return {
      name: deal.name,
      deal_name: deal.deal_name || deal.organization || deal.name,
      status: deal.status,
      statusTone: dealStatusTone(deal.status),
      statusDot: `var(--crm-${stageToken(deal.status)})`,
      value: formatInrAmount(deal.deal_value),
      closeDate: formatCloseDate(deal.expected_closure_date),
      role: deal.role || __('Contact'),
      ownerName: owner?.full_name || deal.deal_owner || '?',
    }
  })
})

const recentConversations = computed(() => {
  const raw = conversations.data
  if (Array.isArray(raw)) return raw
  if (Array.isArray(raw?.message)) return raw.message
  return []
})

function conversationChipClass(type) {
  const t = String(type || '').toLowerCase()
  if (t === 'call') return 'bg-crm-teal-soft text-crm-teal'
  if (t === 'whatsapp') return 'bg-crm-success-soft text-crm-success'
  if (t === 'email') return 'bg-crm-blue-soft text-crm-blue'
  return 'bg-crm-neutral-soft text-crm-muted-fg'
}

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
