<template>
  <div
    v-if="organization.doc"
    class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg"
  >
    <div class="grid min-h-0 flex-1 grid-cols-1 overflow-y-auto xl:grid-cols-crm-record xl:overflow-hidden">
    <div class="flex min-h-0 min-w-0 flex-col overflow-hidden max-xl:min-h-[24rem]">
    <!-- Figma .rhead: crumb + identity + KPIs in one padded card block -->
    <header
      class="flex flex-col gap-3.5 border-b border-crm-border bg-crm-card px-crm-page-x pb-3.5 pt-4"
    >
      <nav
        class="flex min-w-0 items-center gap-1.5 text-[12.5px] text-crm-muted-fg"
        aria-label="Breadcrumb"
      >
        <router-link :to="{ name: 'Organizations' }" class="hover:text-crm-fg">
          {{ __('Companies') }}
        </router-link>
        <span class="lucide-chevron-right size-3.5 shrink-0" aria-hidden="true" />
        <span class="truncate font-semibold text-crm-fg">{{ title }}</span>
        <span class="flex-1" aria-hidden="true" />
        <span
          data-parity-mask="example-data"
          class="inline-flex h-6 items-center gap-1.5 rounded-md border border-dashed border-crm-border-strong px-[9px] text-[11.5px] font-medium text-crm-muted-fg"
        >
          <span class="size-1.5 rounded-full bg-crm-warning" aria-hidden="true" />
          {{ __('Example data') }}
        </span>
      </nav>

      <div class="flex items-center gap-3">
        <RecordAvatar
          :name="title"
          tone="neutral"
          :src="organization.doc.organization_logo || ''"
          :removable="!!organization.doc.organization_logo"
          @upload="changeOrganizationImage"
          @remove="changeOrganizationImage('')"
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
              v-for="(item, index) in organizationMetaItems"
              :key="item.key"
            >
              <span
                v-if="index"
                class="size-[3px] rounded-full bg-crm-faint"
                aria-hidden="true"
              />
              <button
                v-if="item.href"
                type="button"
                class="text-crm-primary hover:underline"
                @click="openWebsite"
              >
                {{ item.label }}
              </button>
              <span v-else>{{ item.label }}</span>
            </template>
          </div>
        </div>
        <span class="min-w-0 flex-1" aria-hidden="true" />
        <div class="flex shrink-0 flex-wrap items-center gap-2 -translate-x-3">
          <CustomActions
            v-if="organization._actions?.length"
            :actions="organization._actions"
          />
          <Link
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
                variant="secondary"
                size="sm"
                :label="__('Contact')"
                @click="togglePopover()"
              >
                <template #prefix>
                  <span class="lucide-plus size-3.5" aria-hidden="true" />
                </template>
              </AstraButton>
            </template>
          </Link>
          <AstraButton
            variant="primary"
            size="sm"
            :label="__('New deal')"
            @click="showDealModal = true"
          >
            <template #prefix>
              <span class="lucide-plus size-3.5" aria-hidden="true" />
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
          v-for="kpi in organizationKpis"
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
              <table class="w-full border-collapse text-[12.5px] [&_tbody_tr:last-child_td]:border-b-0">
                <thead>
                  <tr>
                    <th
                      v-for="col in orgDealColumns"
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
                    v-for="row in orgDealRows"
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
                    <td class="h-11 whitespace-nowrap border-b border-crm-border px-2.5">
                      <!-- Figma .st — neutral chip + 7px square; open stages use fg ink -->
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
                      class="h-11 whitespace-nowrap border-b border-crm-border px-2.5 text-right tabular-nums text-crm-muted-fg"
                    >
                      {{ row.probability }}
                    </td>
                    <td
                      class="h-11 whitespace-nowrap border-b border-crm-border px-2.5 tabular-nums text-crm-fg"
                    >
                      {{ row.closeDate }}
                    </td>
                    <td
                      class="h-11 whitespace-nowrap border-b border-crm-border px-2.5 text-crm-muted-fg"
                    >
                      {{ row.contacts }}
                    </td>
                    <td class="h-11 whitespace-nowrap border-b border-crm-border px-2.5">
                      <AstraAvatar
                        :name="row.ownerName"
                        size="sm"
                      />
                    </td>
                  </tr>
                  <tr v-if="!orgDealRows.length">
                    <td
                      colspan="7"
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
                class="flex items-center gap-2.5 border-b border-crm-border px-[18px] py-3.5"
              >
                <h2 class="m-0 text-[14px] font-semibold tracking-[-0.005em] text-crm-fg">
                  {{ __('People') }}
                </h2>
                <span class="flex-1" aria-hidden="true" />
                <button
                  type="button"
                  class="inline-flex items-center gap-0.5 text-[12.5px] font-semibold text-crm-primary hover:underline"
                  @click="activeTab = 'contacts'"
                >
                  {{ __('All contacts') }}
                  <span class="lucide-chevron-right size-3.5" aria-hidden="true" />
                </button>
              </header>
              <div class="grid grid-cols-1 sm:grid-cols-2">
                <div
                  v-for="person in orgPeople"
                  :key="person.name"
                  class="flex items-center gap-2.5 border-t border-crm-border px-4 py-[9px] text-[12.5px] first:border-t first:border-crm-border"
                >
                  <div class="flex min-w-0 items-center gap-[9px]">
                    <AstraAvatar :name="person.full_name" />
                    <div class="flex min-w-0 flex-col leading-[1.3]">
                      <b class="truncate font-semibold text-crm-fg">
                        {{ person.full_name }}
                      </b>
                      <span class="truncate text-[11.5px] text-crm-muted-fg">
                        {{ person.designation }}
                      </span>
                    </div>
                  </div>
                  <span class="flex-1" aria-hidden="true" />
                  <AstraBadge
                    v-if="person.chip === 'Primary · deal'"
                    :label="person.chip"
                    tone="info"
                  />
                  <span
                    v-else-if="person.channels === 'WhatsApp' || person.chip === 'WhatsApp'"
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
                    {{ __('WhatsApp') }}
                  </span>
                  <span
                    v-else-if="person.last_activity"
                    class="text-[12px]"
                    :class="
                      person.last_activity === 'No activity yet'
                        ? 'text-crm-faint'
                        : 'text-crm-muted-fg'
                    "
                  >
                    {{ person.last_activity }}
                  </span>
                </div>
              </div>
            </section>

            <section
              class="overflow-hidden rounded-[10px] border border-crm-border bg-crm-card"
            >
              <header
                class="flex items-center gap-2.5 border-b border-crm-border px-[18px] py-3.5"
              >
                <h2 class="m-0 text-[14px] font-semibold tracking-[-0.005em] text-crm-fg">
                  {{ __('Recent activity') }}
                </h2>
                <span class="text-[12.5px] font-normal text-crm-muted-fg">
                  {{
                    __('across all {0} deals and contacts', [
                      title.split(' ')[0] || title,
                    ])
                  }}
                </span>
                <span class="flex-1" aria-hidden="true" />
                <button
                  type="button"
                  class="inline-flex items-center gap-0.5 text-[12.5px] font-semibold text-crm-primary hover:underline"
                  @click="activeTab = 'activity'"
                >
                  {{ __('Activity tab') }}
                  <span class="lucide-chevron-right size-3.5" aria-hidden="true" />
                </button>
              </header>
              <div
                v-for="item in orgRecentActivity"
                :key="item.name"
                class="flex items-center gap-2.5 border-t border-crm-border px-4 py-[9px] text-[12.5px]"
              >
                <span
                  class="inline-flex h-[18px] shrink-0 items-center gap-1 rounded px-1.5 text-[10.5px] font-semibold"
                  :class="activityChipClass(item.type)"
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
                    <template v-if="String(item.type).toLowerCase() === 'call'">
                      <path
                        d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"
                      />
                    </template>
                    <template
                      v-else-if="String(item.type).toLowerCase() === 'email'"
                    >
                      <rect x="2" y="4" width="20" height="16" rx="2" />
                      <path d="m22 7-10 6L2 7" />
                    </template>
                    <template v-else>
                      <rect x="3" y="3" width="18" height="18" rx="2" />
                      <path d="M8 7v7M12 7v4M16 7v9" />
                    </template>
                  </svg>
                  {{ item.type }}
                </span>
                <div class="min-w-0 flex-1">
                  <div class="truncate font-semibold text-crm-fg">
                    {{ item.title }}
                  </div>
                  <div class="truncate text-[11.5px] text-crm-muted-fg">
                    {{ item.meta }}
                  </div>
                </div>
              </div>
            </section>
          </div>
          <ContactsListView
            v-else-if="tab.value === 'contacts' && rows.length"
            class="mt-4"
            :rows="rows"
            :columns="columns"
            :options="{ selectable: false, showTooltip: false }"
          />
          <EmptyState
            v-else-if="tab.value === 'contacts'"
            :icon="tab.iconLeft"
            :name="__(tab.label)"
            description=""
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
            <dt class="text-crm-muted-fg">{{ __('Industry') }}</dt>
            <dd class="truncate">{{ organization.doc.industry || '—' }}</dd>
            <dt class="text-crm-muted-fg">{{ __('Employees') }}</dt>
            <dd class="truncate">
              {{ organization.doc.no_of_employees || '—' }}
            </dd>
            <dt class="text-crm-muted-fg">{{ __('Annual revenue') }}</dt>
            <dd class="truncate tabular-nums">
              {{ crLabel(organization.doc.annual_revenue) }}
            </dd>
            <dt class="text-crm-muted-fg">{{ __('Currency') }}</dt>
            <dd class="truncate">{{ organization.doc.currency || 'INR' }}</dd>
            <dt class="text-crm-muted-fg">{{ __('Territory') }}</dt>
            <dd class="truncate">{{ organization.doc.territory || '—' }}</dd>
            <dt class="text-crm-muted-fg">{{ __('Website') }}</dt>
            <dd class="truncate text-crm-primary">
              <button
                type="button"
                class="text-crm-primary hover:underline"
                @click="openWebsite"
              >
                {{ website(organization.doc.website) || '—' }}
              </button>
            </dd>
            <dt class="text-crm-muted-fg">{{ __('LinkedIn') }}</dt>
            <dd class="truncate text-crm-primary">
              {{ organization.doc.linkedin || '—' }}
            </dd>
          </dl>
        </section>
        <section class="border-b border-crm-border">
          <header
            class="px-4 pb-1 pt-3 text-[12px] font-bold text-crm-fg"
          >
            {{ __('Address') }}
          </header>
          <div
            class="whitespace-pre-line px-4 pb-3.5 pt-1.5 text-[12.5px] leading-[1.5] text-crm-fg"
          >
            {{ organization.doc.address_display || '—' }}
          </div>
        </section>
        <section class="border-0">
          <header
            class="px-4 pb-1 pt-3 text-[12px] font-bold text-crm-fg"
          >
            {{ __('About') }}
          </header>
          <div
            class="px-4 pb-3.5 pt-1.5 text-[12.5px] leading-[1.5] text-crm-muted-fg"
          >
            {{ organization.doc.company_description || '—' }}
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
import AstraSidePanel from '@/components/astra/AstraSidePanel.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import DealModal from '@/components/Modals/DealModal.vue'
import Link from '@/components/Controls/Link.vue'
import CustomActions from '@/components/CustomActions.vue'
import RecordAvatar from '@/components/Pipeline/RecordAvatar.vue'
import { recordTabsClass } from '@/components/Pipeline/recordChrome'
import AstraButton from '@/components/astra/AstraButton.vue'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import AstraBadge from '@/components/astra/AstraBadge.vue'
import {
  formatInrAmount,
  stageToken,
  statusToneFor,
} from '@/components/astra/format'
import { formatCurrency } from '@/utils/numberFormat'
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
  Dropdown,
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

const organizationMetaItems = computed(() => {
  const doc = organization.doc || {}
  const items = []
  if (doc.industry) items.push({ key: 'industry', label: doc.industry })
  if (doc.no_of_employees) {
    items.push({
      key: 'employees',
      label: __('{0} employees', [doc.no_of_employees]),
    })
  }
  if (doc.website) {
    items.push({
      key: 'website',
      label: website(doc.website),
      href: true,
    })
  }
  if (doc.territory) items.push({ key: 'territory', label: doc.territory })
  return items
})

function inr(value) {
  if (value == null || value === '') return ''
  return formatCurrency(value, '', docCurrency(), 0)
}

function docCurrency() {
  return organization.doc?.currency || 'INR'
}

function crLabel(value) {
  if (value == null || value === '') return ''
  const cr = Number(value) / 10000000
  if (Number.isNaN(cr)) return inr(value)
  const rounded = Number.isInteger(cr) ? String(cr) : cr.toFixed(0)
  return `₹${rounded} Cr`
}

const organizationKpis = computed(() => {
  const doc = organization.doc || {}
  return [
    {
      label: __('Open pipeline'),
      value: inr(doc.open_pipeline),
      detail: __(
        '{0} deals · weighted {1}',
        [
          doc.open_deals_count ?? deals.data?.length ?? 0,
          doc.weighted_pipeline != null
            ? `₹${(Number(doc.weighted_pipeline) / 100000).toFixed(1)} L`
            : '—',
        ],
      ),
    },
    {
      label: __('Won lifetime'),
      value: inr(doc.won_lifetime),
      detail: __(
        '{0} deal · since {1}',
        [doc.won_count ?? 0, doc.won_since || '—'],
      ),
    },
    {
      label: __('Contacts'),
      value: String(doc.contacts_count ?? contacts.data?.length ?? 0),
      detail: __('{0} on open deals', [doc.contacts_on_open_deals ?? 0]),
    },
    {
      label: __('Annual revenue'),
      value: crLabel(doc.annual_revenue),
      detail: doc.currency || 'INR',
    },
  ]
})

const moreOptions = computed(() => {
  const options = [
    {
      label: __('Open Website'),
      icon: 'lucide-link',
      onClick: openWebsite,
    },
    {
      label: __('Enrich from website'),
      icon: 'lucide-sparkles',
      onClick: onEnriched,
    },
  ]
  if (canDelete.value) {
    options.push({
      label: __('Delete'),
      icon: 'lucide-trash-2',
      onClick: deleteOrganization,
    })
  }
  return options
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
const tabs = computed(() => [
  {
    value: 'deals',
    label: __('Deals'),
    count:
      (organization.doc?.open_deals_count || 0) +
        (organization.doc?.won_count || 0) ||
      deals.data?.length ||
      3,
  },
  {
    value: 'contacts',
    label: __('Contacts'),
    iconLeft: ContactsIcon,
    count: organization.doc?.contacts_count ?? contacts.data?.length ?? 4,
  },
  {
    value: 'activity',
    label: __('Activity'),
  },
  {
    value: 'notes',
    label: __('Notes'),
    count: 2,
  },
])

const deals = createListResource({
  type: 'list',
  doctype: 'CRM Deal',
  cache: ['deals', props.organizationId],
  fields: [
    'name',
    'organization',
    'deal_name',
    'currency',
    'deal_value',
    'status',
    'probability',
    'expected_closure_date',
    'contact',
    'contacts_label',
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
    'designation',
    'image',
    'email_id',
    'mobile_no',
    'company_name',
    'chip',
    'channels',
    'last_activity',
    'modified',
  ],
  filters: {
    company_name: props.organizationId,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const orgActivities = createResource({
  url: 'crm.api.activities.get_activities',
  params: { name: props.organizationId },
  auto: true,
  cache: ['org-activities', props.organizationId],
})

const orgDealColumns = [
  { key: 'deal', label: __('Deal') },
  { key: 'stage', label: __('Stage') },
  { key: 'value', label: __('Value'), align: 'right' },
  { key: 'prob', label: __('Prob.'), align: 'right' },
  { key: 'close', label: __('Expected / closed') },
  { key: 'contacts', label: __('Contacts') },
  { key: 'owner', label: __('Owner') },
]

function formatOrgCloseDate(value) {
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
  // Figma .st — open stages use neutral chip + coloured square; only Won/Lost tint the chip
  const type = getDealStatus(status)?.type || ''
  if (type === 'Won' || status === 'Won') return 'success'
  if (type === 'Lost' || status === 'Lost') return 'danger'
  return 'mute'
}

const orgDealRows = computed(() => {
  if (!Array.isArray(deals.data)) return []
  return deals.data.map((deal) => {
    const owner = deal.deal_owner ? getUser(deal.deal_owner) : null
    const token = stageToken(deal.status)
    return {
      name: deal.name,
      deal_name: deal.deal_name || deal.organization || deal.name,
      status: deal.status,
      statusTone: dealStatusTone(deal.status),
      statusDot: `var(--crm-${token})`,
      value: formatInrAmount(deal.deal_value),
      probability:
        deal.probability == null || deal.probability === ''
          ? '—'
          : `${Math.round(Number(deal.probability))}%`,
      closeDate: formatOrgCloseDate(deal.expected_closure_date),
      contacts: deal.contacts_label || deal.contact || '—',
      ownerName: owner?.full_name || deal.deal_owner || '?',
    }
  })
})

const orgPeople = computed(() => {
  if (!Array.isArray(contacts.data)) return []
  return contacts.data.map((c) => ({
    name: c.name,
    full_name: c.full_name,
    designation: c.designation || '',
    chip: c.chip || '',
    channels: c.channels || '',
    last_activity: c.last_activity || '',
  }))
})

const orgRecentActivity = computed(() => {
  const raw = orgActivities.data
  if (Array.isArray(raw)) return raw
  if (Array.isArray(raw?.message)) return raw.message
  return []
})

function activityChipClass(type) {
  const t = String(type || '').toLowerCase()
  if (t === 'call') return 'bg-crm-teal-soft text-crm-teal'
  if (t === 'email') return 'bg-crm-blue-soft text-crm-blue'
  if (t === 'stage') return 'bg-crm-primary-soft text-crm-primary'
  if (t === 'note') return 'bg-crm-warning-soft text-crm-warning'
  return 'bg-crm-neutral-soft text-crm-muted-fg'
}


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
  if (!Array.isArray(contacts.data)) return []
  return contacts.data.map((row) => getContactRowObject(row))
})

const columns = computed(() => contactColumns)

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
