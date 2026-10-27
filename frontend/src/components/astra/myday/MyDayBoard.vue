<template>
  <div class="astra-bento flex min-w-0 flex-col gap-4 overflow-x-hidden">
    <header class="flex min-w-0 flex-wrap items-end justify-between gap-3">
      <div class="min-w-0">
        <h1
          class="truncate text-[1.75rem] font-bold tracking-tight text-[var(--astra-text)] sm:text-[2rem]"
        >
          {{ greeting }}, {{ firstName }}
        </h1>
        <p class="astra-muted mt-1 text-sm">{{ dateLabel }}</p>
      </div>
    </header>

    <!--
      Row 1 fills width: Today | Target | 3 KPIs
      Row 2 fills width: Upcoming calls | Hot leads
      No row-span holes at lg/xl; single column at mobile.
    -->
    <div class="grid min-w-0 grid-cols-1 gap-4 lg:grid-cols-12">
      <!-- Today tasks -->
      <AstraCard
        class="min-w-0 lg:col-span-3"
        :title="__('Today')"
      >
        <div v-if="myDayLoading" class="astra-muted text-sm">
          {{ __('Loading…') }}
        </div>
        <AstraEmptyState
          v-else-if="!tasks.length"
          :title="__('Nothing due today')"
          :body="__('Tasks assigned to you that are due today will appear here.')"
        />
        <ul v-else class="flex flex-col gap-2" role="list">
          <li
            v-for="task in tasks"
            :key="task.name"
            class="flex items-start gap-2.5"
          >
            <span
              class="mt-0.5 size-4 shrink-0 rounded-[4px] border border-[var(--astra-border)]"
              aria-hidden="true"
            />
            <button
              type="button"
              class="min-w-0 flex-1 text-left text-sm font-medium text-[var(--astra-text)] hover:underline"
              @click="openTask(task)"
            >
              <span>{{ task.title }}</span>
              <span
                class="mt-0.5 block text-xs font-normal"
                :class="task.overdue ? 'text-[var(--astra-danger)]' : 'astra-muted'"
              >
                {{ taskDueLabel(task) }}
                <template v-if="task.priority"> · {{ task.priority }}</template>
              </span>
            </button>
          </li>
        </ul>
        <div v-if="meetings.length" class="mt-4 border-t border-[var(--astra-border)] pt-3">
          <p class="astra-label mb-2">{{ __('Meetings') }}</p>
          <ul class="flex flex-col gap-1.5">
            <li
              v-for="m in meetings"
              :key="m.name"
              class="text-sm text-[var(--astra-text)]"
            >
              {{ m.subject }}
              <span v-if="m.starts_on" class="astra-muted">
                · {{ formatTime(m.starts_on) }}
              </span>
            </li>
          </ul>
        </div>
      </AstraCard>

      <!-- Target -->
      <AstraCard class="min-w-0 lg:col-span-3" :title="__('Target')">
        <AstraGauge
          v-if="target"
          :percent="target.percent"
          :caption="target.caption"
          :aria-label="__('Monthly target')"
        />
        <AstraEmptyState
          v-else
          :title="__('No sales target configured')"
          :body="__(
            'A monthly target gauge will appear here when a sales target field is available on your CRM settings.',
          )"
        />
      </AstraCard>

      <!-- KPI strip -->
      <div class="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-3 lg:col-span-6">
        <AstraCard
          v-for="kpi in kpis"
          :key="kpi.key"
          class="min-w-0 !p-4"
        >
          <p class="astra-label">{{ __(kpi.label) }}</p>
          <p class="astra-value mt-1 truncate">
            <span v-if="kpi.loading" class="astra-muted text-base font-medium">{{
              __('Loading…')
            }}</span>
            <span v-else>{{ kpi.value }}</span>
          </p>
          <div class="mt-3 flex min-w-0 items-end justify-between gap-2">
            <div class="min-w-0 flex-1">
              <AstraSparkline :values="kpi.spark" />
            </div>
            <span
              v-if="kpi.delta"
              class="astra-badge astra-badge--success shrink-0"
            >{{ kpi.delta }}</span>
          </div>
        </AstraCard>
      </div>

      <!-- Upcoming calls -->
      <AstraCard
        class="min-w-0 lg:col-span-5"
        :title="__('Upcoming calls')"
      >
        <div v-if="myDayLoading" class="astra-muted text-sm">
          {{ __('Loading…') }}
        </div>
        <AstraEmptyState
          v-else-if="!calls.length"
          :title="__('No upcoming calls scheduled')"
          :body="__(
            'Future scheduled calls will appear here. Completed call logs stay in the feed below.',
          )"
        />
        <ul v-else class="divide-y divide-[var(--astra-border)]" role="list">
          <li
            v-for="call in calls"
            :key="call.name"
            class="flex min-w-0 flex-wrap items-center gap-3 py-2.5 first:pt-0 last:pb-0"
          >
            <AstraAvatar
              :name="callLabel(call)"
              :seed="call.name"
              size="sm"
            />
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold text-[var(--astra-text)]">
                {{ formatTime(call.creation) }}
                <span class="font-medium">· {{ callLabel(call) }}</span>
              </p>
              <p class="astra-muted truncate text-xs">
                {{ call.type }} · {{ call.status }}
                <template v-if="call.outcome"> · {{ call.outcome }}</template>
              </p>
            </div>
            <button
              v-if="callEnabled"
              type="button"
              class="astra-btn astra-btn--primary shrink-0"
              :aria-label="__('Open call log')"
              @click="openCall(call)"
            >
              {{ __('Call') }}
            </button>
            <button
              v-else
              type="button"
              class="astra-btn astra-btn--outline shrink-0"
              :aria-label="__('Open call log')"
              @click="openCall(call)"
            >
              {{ __('Open') }}
            </button>
          </li>
        </ul>
      </AstraCard>

      <!-- Hot leads -->
      <AstraCard class="min-w-0 lg:col-span-7" :title="__('Hot leads')">
        <div v-if="hotLeads.loading" class="astra-muted text-sm">
          {{ __('Loading…') }}
        </div>
        <AstraEmptyState
          v-else-if="!hotLeadRows.length"
          :title="__('No scored hot leads')"
          :body="__(
            'Leads with a lead score or Hot temperature will appear here.',
          )"
        />
        <ul v-else role="list">
          <li
            v-for="lead in hotLeadRows"
            :key="lead.name"
            class="astra-row min-w-0"
          >
            <AstraAvatar
              :name="lead.organization || lead.lead_name || lead.name"
              :seed="lead.name"
              size="sm"
            />
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold text-[var(--astra-text)]">
                {{ lead.organization || lead.lead_name || lead.name }}
              </p>
              <p v-if="lead.lead_name && lead.organization" class="astra-muted truncate text-xs">
                {{ lead.lead_name }}
              </p>
            </div>
            <span
              v-if="lead.lead_score != null"
              class="shrink-0 tabular-nums text-sm font-bold text-[var(--astra-text)]"
            >{{ lead.lead_score }}</span>
            <button
              type="button"
              class="astra-btn astra-btn--outline shrink-0"
              :aria-label="__('Open lead')"
              @click="openLead(lead)"
            >
              {{ __('Open') }}
            </button>
          </li>
        </ul>
      </AstraCard>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AstraCard from '@/components/astra/AstraCard.vue'
import AstraEmptyState from '@/components/astra/AstraEmptyState.vue'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import AstraGauge from '@/components/astra/AstraGauge.vue'
import AstraSparkline from '@/components/astra/AstraSparkline.vue'
import {
  formatShortDate,
  formatTime,
  greetingFor,
} from '@/components/astra/format'
import { useMyDayMetrics } from '@/components/astra/myday/useMyDayMetrics'
import { filterUpcomingCalls } from '@/components/astra/myday/myDayHelpers'
import { taskDueReason } from '@/components/astra/workqueue/queueHelpers'
import { callEnabled } from '@/composables/telephony'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'
import { useDoctypeModal } from '@/composables/doctypeModal'
import '@/components/astra/astra-bento.css'

const props = defineProps({
  /** Resource data from crm.api.activities.get_my_day */
  myDayData: { type: Object, default: null },
  myDayLoading: { type: Boolean, default: false },
})

const router = useRouter()
const { getUser } = usersStore()
const { user } = sessionStore()
const { showModal } = useDoctypeModal()
const { kpis, hotLeadRows, hotLeads, target } = useMyDayMetrics()

const firstName = computed(() => {
  const full = getUser(user)?.full_name || user || ''
  return String(full).split(/\s+/)[0] || __('there')
})

const greeting = computed(() => __(greetingFor()))
const dateLabel = computed(() => formatShortDate())

const tasks = computed(() => props.myDayData?.tasks || [])
const calls = computed(() =>
  filterUpcomingCalls(props.myDayData?.calls || [], new Date()),
)
const meetings = computed(() => props.myDayData?.meetings || [])

function taskDueLabel(task) {
  if (task.overdue) return __('Overdue')
  return __(taskDueReason(task.due_date, {}))
}

function callLabel(call) {
  return (
    call.reference_docname ||
    call.to ||
    call.from ||
    call.name ||
    __('Call')
  )
}

function openTask(task) {
  showModal({
    doctype: 'CRM Task',
    name: task.name,
    title: 'Task',
  })
}

function openCall(call) {
  if (call.reference_doctype && call.reference_docname) {
    const map = {
      'CRM Lead': { name: 'Lead', params: { leadId: call.reference_docname } },
      'CRM Deal': { name: 'Deal', params: { dealId: call.reference_docname } },
      Contact: { name: 'Contact', params: { contactId: call.reference_docname } },
    }
    const route = map[call.reference_doctype]
    if (route) {
      router.push(route)
      return
    }
  }
  router.push({ name: 'Call Logs', query: { callLogId: call.name } })
}

function openLead(lead) {
  router.push({ name: 'Lead', params: { leadId: lead.name } })
}
</script>
