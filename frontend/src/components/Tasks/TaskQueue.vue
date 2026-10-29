<template>
  <div
    class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg [text-rendering:geometricPrecision]"
  >
    <div class="min-h-0 flex-1 overflow-y-auto">
      <header class="flex items-center gap-3 px-crm-page-x pb-3.5 pt-[19px]">
        <div class="min-w-0">
          <h1
            class="m-0 text-[20px] font-semibold leading-[1.45] tracking-[-0.015em] text-crm-fg"
          >
            {{ __('Tasks') }}
          </h1>
          <p
            class="relative top-px m-0 -mt-px text-[13px] leading-[1.45] tracking-[-0.005em] text-crm-muted-fg"
          >
            {{ __('Your tasks across leads and deals') }}
          </p>
        </div>
        <div class="flex-1" />
        <slot name="actions" />
        <AstraButton size="sm" variant="primary" :label="__('New task')" @click="$emit('create')">
          <template #prefix>
            <LucidePlus class="size-3.5" aria-hidden="true" />
          </template>
        </AstraButton>
      </header>

      <div class="flex h-[46px] items-start border-b border-crm-border px-crm-page-x pt-[3px]">
        <div class="flex items-start" role="tablist" :aria-label="__('Tasks')">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            type="button"
            role="tab"
            :aria-selected="activeTab === tab.value"
            class="inline-flex h-[39px] items-center gap-1.5 whitespace-nowrap border-b-2 px-3 pt-0.5 text-[12.5px]"
            :class="
              activeTab === tab.value
                ? 'border-crm-primary font-semibold text-crm-fg'
                : 'border-transparent font-medium text-crm-muted-fg'
            "
            @click="setTab(tab.value)"
          >
            {{ tab.label }}
            <span class="text-[11px] font-medium text-crm-faint">
              {{ tab.count }}
            </span>
          </button>
          <span
            class="inline-flex h-[39px] items-center gap-1.5 whitespace-nowrap border-b-2 border-transparent px-3 pt-0.5 text-[12.5px] font-semibold text-crm-primary"
          >
            <LucidePlus class="size-3.5" aria-hidden="true" />
            {{ __('Save view') }}
          </span>
        </div>
        <div class="flex-1" />
        <div
          class="-mt-[3px] flex h-[45px] items-start gap-0.5 rounded-crm-panel border border-crm-border bg-crm-muted p-[2px]"
          role="group"
          :aria-label="__('View')"
        >
          <span
            class="inline-flex h-10 items-center gap-1.5 rounded-crm-control border border-crm-border bg-crm-card px-2.5 shadow-[inset_0_-2px_0_var(--crm-primary)] text-[12.5px] font-semibold text-crm-fg"
          >
            <LucideList class="size-3.5" aria-hidden="true" />
            {{ __('List') }}
          </span>
          <router-link
            :to="{ name: 'Tasks', params: { viewType: 'kanban' } }"
            class="inline-flex h-10 items-center gap-1.5 rounded-crm-control border border-transparent px-2.5 text-[12.5px] font-medium text-crm-muted-fg"
          >
            <LucideSquareKanban class="size-3.5" aria-hidden="true" />
            {{ __('Board') }}
          </router-link>
        </div>
      </div>

      <div class="flex h-12 items-center gap-2 px-crm-page-x">
        <button
          type="button"
          class="inline-flex h-crm-control-sm items-center gap-1.5 rounded-crm-control-sm border px-2.5 text-[12.5px] font-medium"
          :class="
            assignedToMe
              ? 'border-crm-primary bg-crm-primary-soft'
              : 'border-crm-border-strong bg-crm-card'
          "
          @click="setTab(assignedToMe ? 'team' : 'mine')"
        >
          <span class="text-crm-muted-fg">{{ __('Assigned to') }}</span>
          <span class="font-semibold text-crm-primary">{{ __('Me') }}</span>
          <LucideX
            v-if="assignedToMe"
            class="size-3.5 text-crm-faint"
            aria-hidden="true"
          />
        </button>
        <label
          class="relative inline-flex h-crm-control-sm items-center gap-1.5 rounded-crm-control-sm border border-crm-border bg-crm-card pl-3 pr-2.5 text-[12.5px] font-medium"
        >
          <span class="text-crm-muted-fg">{{ __('Priority') }}</span>
          <span class="font-semibold text-crm-fg">{{ priorityLabel }}</span>
          <LucideChevronDown class="size-3.5 text-crm-faint" aria-hidden="true" />
          <select
            v-model="priority"
            class="absolute inset-0 cursor-pointer opacity-0"
            :aria-label="__('Priority')"
          >
            <option value="">{{ __('Any') }}</option>
            <option v-for="p in priorities" :key="p" :value="p">
              {{ __(p) }}
            </option>
          </select>
        </label>
        <AstraButton size="sm" :label="__('Filter')" @click="$emit('filter')">
          <template #prefix>
            <LucidePlus class="size-3.5 text-crm-faint" aria-hidden="true" />
          </template>
        </AstraButton>
        <div class="flex-1" />
        <button
          type="button"
          class="inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-crm-muted-fg"
          :aria-label="__('Sort by due date')"
          @click="toggleSort"
        >
          <LucideArrowDownUp class="size-3.5" aria-hidden="true" />
          {{ __('Due date') }}
        </button>
      </div>

      <div
        v-if="board.loading && !board.data"
        class="px-crm-page-x text-crm-body text-crm-muted-fg"
      >
        {{ __('Loading…') }}
      </div>

      <div
        v-else
        class="grid items-stretch gap-4 px-crm-page-x pb-6 lg:grid-cols-[1fr_360px]"
      >
        <section
          class="min-w-0 self-start overflow-hidden rounded-crm-panel border border-crm-border bg-crm-card"
        >
          <AstraEmptyState
            v-if="!groups.length && !doneCount"
            :title="__('No tasks yet')"
            :body="
              __(
                'Tasks are to-dos for you and your team, like a follow-up call or sending a quote. Add them here or from a lead or deal.',
              )
            "
          />
          <template v-for="(group, gIndex) in groups" :key="group.id">
            <button
              type="button"
              class="flex h-[43px] w-full items-center gap-2.5 border-t border-crm-border bg-crm-muted px-4 text-left text-[12.5px]"
              :aria-expanded="!collapsed[group.id]"
              @click="collapsed[group.id] = !collapsed[group.id]"
            >
              <component
                :is="collapsed[group.id] ? LucideChevronRight : LucideChevronDown"
                class="size-3.5 text-crm-muted-fg"
                aria-hidden="true"
              />
              <AstraBadge :label="__(group.label)" :tone="statusTone(group.id)" dot />
              <span class="text-[12.5px] font-semibold text-crm-muted-fg">
                {{ group.count }}
              </span>
            </button>
            <template v-if="!collapsed[group.id]">
              <div
                v-for="item in group.items"
                :key="item.name"
                class="grid h-[55.9px] cursor-pointer grid-cols-[18px_8px_1fr_auto_22px] items-center gap-3 border-t border-crm-border px-4"
                :class="
                  selectedName === item.name
                    ? 'bg-crm-row-selected shadow-[inset_3px_0_0_var(--crm-primary)]'
                    : 'hover:bg-crm-row-hover'
                "
                role="button"
                tabindex="0"
                :aria-pressed="selectedName === item.name"
                @click="selectTask(item.name)"
                @keydown.enter="selectTask(item.name)"
              >
                <span
                  class="size-[18px] rounded-full border-[1.5px] border-crm-border-strong"
                  aria-hidden="true"
                />
                <span
                  class="-ml-[7px] size-2 rounded-[2px]"
                  :class="priorityDot(item.priority)"
                  aria-hidden="true"
                />
                <div class="-ml-1.5 flex min-w-0 flex-col pt-0.5 leading-[1.45]">
                  <b class="truncate text-[12.5px] font-semibold text-crm-fg">
                    {{ item.title }}
                  </b>
                  <span class="truncate text-[11.5px] text-crm-muted-fg">
                    {{ item.record_label }}
                  </span>
                </div>
                <span
                  class="whitespace-nowrap text-[12px]"
                  :class="
                    item.overdue
                      ? 'font-semibold text-crm-danger'
                      : 'text-crm-muted-fg'
                  "
                >
                  {{ item.due_label }}
                </span>
                <span
                  class="flex size-[22px] items-center justify-center rounded-full bg-crm-primary-soft text-[9px] font-bold text-crm-primary"
                  aria-hidden="true"
                >
                  {{ initialsFrom(item.assigned_name || item.assigned_to || '') }}
                </span>
              </div>
            </template>
          </template>
          <div
            v-if="doneCount"
            class="flex h-[43px] items-center gap-2.5 bg-crm-muted px-4 text-[12.5px]"
            :class="{ 'border-t border-crm-border': groups.length }"
          >
            <LucideChevronRight class="size-3.5 text-crm-muted-fg" aria-hidden="true" />
            <AstraBadge :label="__('Done')" tone="ok" dot />
            <span class="font-semibold text-crm-muted-fg">{{ doneCount }}</span>
            <span class="text-[12px] text-crm-faint">
              {{ doneSummary }}
            </span>
          </div>
        </section>

        <aside
          v-if="detail.data"
          class="hidden overflow-hidden rounded-crm-panel border border-crm-border bg-crm-card lg:block"
        >
          <div
            class="flex h-[50px] items-center gap-3 border-b border-crm-border px-4"
          >
            <button
              type="button"
              class="size-4 shrink-0 rounded-full border-[1.5px] border-crm-border-strong"
              :aria-label="__('Mark done')"
              @click="markDone"
            />
            <h2
              class="m-0 truncate text-[14px] font-semibold leading-[21.5px] tracking-[-0.005em] text-crm-fg"
            >
              {{ detail.data.title }}
            </h2>
          </div>
          <div class="grid grid-cols-2 gap-x-[11px] gap-y-[10.5px] p-4 text-[12.5px]">
            <label class="flex flex-col gap-1">
              <span class="text-[12px] font-semibold text-crm-fg">{{ __('Status') }}</span>
              <span
                class="relative flex h-8 items-center rounded-crm-control border border-crm-border-strong bg-crm-card pl-[9px] pr-2"
              >
                <AstraBadge :label="__(detail.data.status)" :tone="statusTone(detail.data.status)" dot />
                <LucideChevronDown class="ml-auto size-3.5 text-crm-faint" aria-hidden="true" />
                <select
                  :value="detail.data.status"
                  class="absolute inset-0 cursor-pointer opacity-0"
                  @change="updateField('status', $event.target.value)"
                >
                  <option v-for="s in statuses" :key="s" :value="s">{{ __(s) }}</option>
                </select>
              </span>
            </label>
            <label class="flex flex-col gap-1">
              <span class="text-[12px] font-semibold text-crm-fg">{{ __('Priority') }}</span>
              <span
                class="relative flex h-8 items-center gap-2 rounded-crm-control border border-crm-border-strong bg-crm-card pl-[9px] pr-2"
              >
                <span class="size-2 rounded-[2px]" :class="priorityDot(detail.data.priority)" />
                <span class="text-crm-fg">{{ __(detail.data.priority) }}</span>
                <LucideChevronDown class="ml-auto size-3.5 text-crm-faint" aria-hidden="true" />
                <select
                  :value="detail.data.priority"
                  class="absolute inset-0 cursor-pointer opacity-0"
                  @change="updateField('priority', $event.target.value)"
                >
                  <option v-for="p in priorities" :key="p" :value="p">{{ __(p) }}</option>
                </select>
              </span>
            </label>
            <label class="flex flex-col gap-1">
              <span class="text-[12px] font-semibold text-crm-fg">{{ __('Due') }}</span>
              <span
                class="relative flex h-8 items-center rounded-crm-control border border-crm-primary bg-crm-card px-[11px] text-crm-fg shadow-crm-input-focus"
              >
                {{ dueLabel }}
                <input
                  type="datetime-local"
                  :value="dueInputValue"
                  class="absolute inset-0 cursor-pointer opacity-0"
                  :aria-label="__('Due')"
                  @change="updateField('due_date', $event.target.value)"
                />
              </span>
            </label>
            <label class="flex flex-col gap-1">
              <span class="text-[12px] font-semibold text-crm-fg">{{ __('Assigned to') }}</span>
              <span
                class="relative flex h-8 items-center gap-2 rounded-crm-control border border-crm-border-strong bg-crm-card px-2"
              >
                <span
                  class="flex size-[22px] items-center justify-center rounded-full bg-crm-primary-soft text-[9px] font-bold text-crm-primary"
                >
                  {{ initialsFrom(detail.data.assigned_name || detail.data.assigned_to || '') }}
                </span>
                <span class="truncate text-crm-fg">
                  {{ detail.data.assigned_name || detail.data.assigned_to }}
                </span>
                <select
                  :value="detail.data.assigned_to"
                  class="absolute inset-0 cursor-pointer opacity-0"
                  @change="updateField('assigned_to', $event.target.value)"
                >
                  <option v-for="u in crmUsers" :key="u.name" :value="u.name">
                    {{ u.full_name || u.name }}
                  </option>
                </select>
              </span>
            </label>
            <div class="col-span-2 mt-[3px] flex flex-col gap-1">
              <span class="text-[12px] font-semibold text-crm-fg">{{ __('Linked to') }}</span>
              <router-link
                v-if="detail.data.linked_label"
                :to="recordRoute"
                class="flex h-8 items-center gap-2 rounded-crm-control border border-crm-border bg-crm-card px-[11px] text-crm-fg"
              >
                <LucideUsers class="size-3.5 text-crm-faint" aria-hidden="true" />
                <span class="truncate">{{ detail.data.linked_label }}</span>
              </router-link>
              <span v-else class="text-crm-faint">—</span>
            </div>
            <div class="col-span-2 mt-[3px] flex flex-col gap-1">
              <span class="text-[12px] font-semibold text-crm-fg">{{ __('Description') }}</span>
              <textarea
                :value="plainDescription"
                rows="2"
                class="h-14 resize-none rounded-crm-control border border-crm-border bg-crm-card px-[11px] py-[9px] text-[12.5px] leading-[1.45] text-crm-fg"
                @change="updateField('description', $event.target.value)"
              />
            </div>
            <div class="col-span-2 mt-0.5 flex items-center gap-2">
              <AstraButton
                v-if="connectReady && detail.data.reference_docname"
                size="sm"
                variant="primary"
                :label="__('Call')"
                @click="callLinked"
              >
                <template #prefix>
                  <LucidePhone class="size-3.5" aria-hidden="true" />
                </template>
                <template #suffix>
                  <LucideExternalLink class="size-3.5" aria-hidden="true" />
                </template>
              </AstraButton>
              <AstraButton size="sm" :label="__('Mark done')" @click="markDone" />
              <div class="flex-1" />
              <span class="relative -top-[3px] text-[11.5px] text-crm-muted-fg">
                {{ detail.data.source_label }}
              </span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { call, createResource } from 'frappe-ui'
import LucideArrowDownUp from '~icons/lucide/arrow-down-up'
import LucideChevronDown from '~icons/lucide/chevron-down'
import LucideChevronRight from '~icons/lucide/chevron-right'
import LucideExternalLink from '~icons/lucide/external-link'
import LucideList from '~icons/lucide/list'
import LucidePhone from '~icons/lucide/phone'
import LucidePlus from '~icons/lucide/plus'
import LucideSquareKanban from '~icons/lucide/square-kanban'
import LucideUsers from '~icons/lucide/users'
import LucideX from '~icons/lucide/x'
import { AstraBadge, AstraButton, AstraEmptyState } from '@/components/astra'
import { initialsFrom } from '@/components/astra/format'
import { usersStore } from '@/stores/users'
import { isAstraConnectConfigured, openConnectCompose } from '@/utils/astraConnect'
import dayjs from 'dayjs'

defineEmits(['create', 'filter'])

const { crmUsers: crmUsersRef } = usersStore()
const crmUsers = computed(() => crmUsersRef.value || [])

const statuses = ['Backlog', 'Todo', 'In Progress', 'Done', 'Canceled']
const priorities = ['Low', 'Medium', 'High']
const activeTab = ref('mine')
const assignedToMe = computed(() => activeTab.value !== 'team')
const priority = ref('')
const sortAsc = ref(true)
const selectedName = ref(null)
const collapsed = reactive({})
const connectReady = computed(() => isAstraConnectConfigured())

const board = createResource({
  url: 'crm.api.task_board.get_task_board',
  auto: true,
  makeParams: () => ({
    tab: activeTab.value,
    priority: priority.value || undefined,
    assigned_to: undefined,
  }),
})

const detail = createResource({
  url: 'crm.api.task_board.get_task_detail',
  makeParams: () => ({ name: selectedName.value }),
})

const counts = computed(() => board.data?.tabs || {})
const tabs = computed(() => [
  { value: 'mine', label: __('My tasks'), count: counts.value.mine ?? 0 },
  { value: 'due_today', label: __('Due today'), count: counts.value.due_today ?? 0 },
  { value: 'overdue', label: __('Overdue'), count: counts.value.overdue ?? 0 },
  { value: 'team', label: __('Team'), count: counts.value.team ?? 0 },
])

const groups = computed(() =>
  (board.data?.groups || []).map((g) => ({
    ...g,
    items: sortAsc.value ? g.items : [...g.items].reverse(),
  })),
)
const doneCount = computed(() => board.data?.done?.count || 0)
const doneSummary = computed(() => {
  const canceled = board.data?.done?.canceled || 0
  return canceled
    ? __('Collapsed · Canceled {0}', [canceled])
    : __('Collapsed')
})
const priorityLabel = computed(() => (priority.value ? __(priority.value) : __('Any')))

const flatItems = computed(() => groups.value.flatMap((g) => g.items))
const plainDescription = computed(() =>
  String(detail.data?.description || '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim(),
)
const dueInputValue = computed(() =>
  detail.data?.due_date ? dayjs(detail.data.due_date).format('YYYY-MM-DDTHH:mm') : '',
)
const dueLabel = computed(() =>
  detail.data?.due_date
    ? dayjs(detail.data.due_date).format(
        /00:00:00$/.test(detail.data.due_date) ? 'D MMM YYYY' : 'D MMM YYYY · HH:mm',
      )
    : '—',
)
const recordRoute = computed(() => {
  const d = detail.data
  if (d?.reference_doctype === 'CRM Deal') return { name: 'Deal', params: { dealId: d.reference_docname } }
  return { name: 'Lead', params: { leadId: d?.reference_docname } }
})

watch(
  () => board.data,
  (data) => {
    if (!data) return
    const names = flatItems.value.map((i) => i.name)
    if (!selectedName.value || !names.includes(selectedName.value)) {
      selectedName.value = names[0] || null
    }
  },
)
watch(selectedName, (name) => name && detail.fetch(), { immediate: true })
watch([activeTab, priority], () => board.reload())

function setTab(value) {
  activeTab.value = value
}

function toggleSort() {
  sortAsc.value = !sortAsc.value
}

function selectTask(name) {
  selectedName.value = name
}

function statusTone(status) {
  return (
    { Todo: 'primary', 'In Progress': 'warn', Backlog: 'mute', Done: 'ok', Canceled: 'mute' }[
      status
    ] || 'mute'
  )
}

function priorityDot(value) {
  return (
    { High: 'bg-crm-danger', Medium: 'bg-crm-warning', Low: 'bg-crm-faint' }[value] ||
    'bg-crm-faint'
  )
}

async function updateField(fieldname, value) {
  if (!selectedName.value) return
  await call('frappe.client.set_value', {
    doctype: 'CRM Task',
    name: selectedName.value,
    fieldname,
    value: fieldname === 'due_date' && value ? value.replace('T', ' ') + ':00' : value,
  })
  await Promise.all([board.reload(), detail.reload()])
}

function markDone() {
  return updateField('status', 'Done')
}

function callLinked() {
  openConnectCompose('calls', {
    recordType: detail.data.reference_doctype,
    recordId: detail.data.reference_docname,
  })
}
</script>
