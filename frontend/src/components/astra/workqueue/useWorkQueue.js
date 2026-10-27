import { computed, ref, watch } from 'vue'
import { createListResource, getConfig } from 'frappe-ui'
import { callEnabled } from '@/composables/telephony'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { siteDayBounds, getSiteTimezone } from '@/components/astra/siteTime'
import {
  buildOwnerScope,
  buildTaskAssigneeScope,
  isTaskOverdue,
  queueCallAction,
  taskDueReason,
} from '@/components/astra/workqueue/queueHelpers'
import {
  classifyQueueType,
  summarizeWorkQueue,
} from '@/components/astra/workqueue/queueSummary'

const STUCK_DAYS = 14
const QUIET_DAYS = 14

/**
 * Build a prioritized work queue from CRM Task, CRM Lead and CRM Deal
 * via existing list resources only.
 */
export function useWorkQueue() {
  const typeFilter = ref('all')
  const { user } = sessionStore()
  const { isManager } = usersStore()
  const manager = isManager()

  const tz = getSiteTimezone(getConfig)
  const bounds = siteDayBounds(new Date(), tz)
  const today = bounds.date
  const dayStart = bounds.start
  const dayEnd = bounds.end
  const quietBefore = daysAgoInTz(QUIET_DAYS, tz)
  const stuckBefore = daysAgoInTz(STUCK_DAYS, tz)

  const taskScope = buildTaskAssigneeScope({ isManager: manager, user })
  const leadScope = buildOwnerScope({
    isManager: manager,
    user,
    doctype: 'CRM Lead',
    ownerField: 'lead_owner',
  })
  const dealScope = buildOwnerScope({
    isManager: manager,
    user,
    doctype: 'CRM Deal',
    ownerField: 'deal_owner',
  })

  const tasks = createListResource({
    doctype: 'CRM Task',
    fields: [
      'name',
      'title',
      'status',
      'priority',
      'due_date',
      'assigned_to',
      'reference_doctype',
      'reference_docname',
      'modified',
    ],
    filters: {
      status: ['not in', ['Done', 'Canceled', 'Cancelled']],
      // Whole-day upper bound so datetime dues later today are included.
      due_date: ['<=', dayEnd],
      ...taskScope.filters,
    },
    orFilters: taskScope.orFilters,
    orderBy: 'due_date asc',
    pageLength: 50,
    auto: true,
    cache: 'astra-workqueue-tasks',
  })

  const quietLeads = createListResource({
    doctype: 'CRM Lead',
    fields: [
      'name',
      'lead_name',
      'organization',
      'status',
      'mobile_no',
      'email',
      'modified',
      'lead_owner',
    ],
    filters: {
      converted: 0,
      modified: ['<', quietBefore],
      ...leadScope.filters,
    },
    orFilters: leadScope.orFilters,
    orderBy: 'modified asc',
    pageLength: 30,
    auto: true,
    cache: 'astra-workqueue-quiet-leads',
  })

  const stuckDeals = createListResource({
    doctype: 'CRM Deal',
    fields: [
      'name',
      'organization',
      'status',
      'deal_owner',
      'modified',
      'mobile_no',
      'email',
    ],
    filters: {
      modified: ['<', stuckBefore],
      ...dealScope.filters,
    },
    orFilters: dealScope.orFilters,
    orderBy: 'modified asc',
    pageLength: 30,
    auto: true,
    cache: 'astra-workqueue-stuck-deals',
  })

  const dealStatuses = createListResource({
    doctype: 'CRM Deal Status',
    fields: ['name', 'type'],
    pageLength: 50,
    auto: true,
    cache: 'astra-workqueue-deal-statuses',
  })

  const statusTypeByName = computed(() => {
    const map = {}
    for (const s of dealStatuses.data || []) map[s.name] = s.type
    return map
  })

  const items = computed(() => {
    const rows = []
    const telephony = callEnabled.value

    for (const t of tasks.data || []) {
      const overdue = isTaskOverdue(t.due_date, dayStart)
      rows.push({
        id: `task-${t.name}`,
        type: 'follow_up',
        priority: normalizePriority(t.priority, overdue ? 'High' : 'Medium'),
        title: t.title || t.name,
        subtitle: t.reference_docname
          ? `${t.reference_doctype || ''} · ${t.reference_docname}`.trim()
          : '',
        reason: __(
          taskDueReason(t.due_date, { dayStart, todayDate: today }),
        ),
        action: 'follow_up',
        reference_doctype: t.reference_doctype || 'CRM Task',
        reference_docname: t.reference_docname || t.name,
        taskName: t.name,
        phone: null,
        raw: t,
      })
    }

    for (const lead of quietLeads.data || []) {
      rows.push({
        id: `lead-${lead.name}`,
        type: 'call',
        priority: 'Med',
        title:
          [lead.lead_name, lead.organization].filter(Boolean).join(' - ') ||
          lead.name,
        subtitle: lead.status || '',
        reason: __('No recent activity'),
        action: queueCallAction({
          phone: lead.mobile_no,
          telephonyEnabled: telephony,
        }),
        reference_doctype: 'CRM Lead',
        reference_docname: lead.name,
        phone: lead.mobile_no || null,
        raw: lead,
      })
    }

    const types = statusTypeByName.value
    for (const deal of stuckDeals.data || []) {
      const t = types[deal.status]
      if (t === 'Won' || t === 'Lost') continue
      rows.push({
        id: `deal-${deal.name}`,
        type: 'follow_up',
        priority: 'High',
        title: deal.organization || deal.name,
        subtitle: deal.status || '',
        reason: __('Stuck in stage'),
        action: 'follow_up',
        reference_doctype: 'CRM Deal',
        reference_docname: deal.name,
        phone: deal.mobile_no || null,
        raw: deal,
      })
    }

    const rank = { High: 0, Med: 1, Low: 2 }
    rows.sort((a, b) => (rank[a.priority] ?? 9) - (rank[b.priority] ?? 9))
    return rows
  })

  // Work queue never produces WhatsApp rows — no WhatsApp chip here.
  const summary = computed(() =>
    summarizeWorkQueue(items.value, { showWhatsApp: false }),
  )

  const counts = computed(() => {
    const s = summary.value
    return {
      all: s.total,
      calls: s.byType.calls,
      follow_ups: s.byType.follow_ups,
      high: s.byPriority.high,
      med: s.byPriority.med,
      low: s.byPriority.low,
    }
  })

  const filtered = computed(() => {
    const list = items.value.filter(
      (i) => classifyQueueType(i) !== 'whatsapp',
    )
    if (typeFilter.value === 'all') return list
    if (typeFilter.value === 'calls')
      return list.filter((i) => classifyQueueType(i) === 'calls')
    if (typeFilter.value === 'follow_ups')
      return list.filter((i) => classifyQueueType(i) === 'follow_ups')
    return list
  })

  watch(typeFilter, (value) => {
    if (value === 'whatsapp') typeFilter.value = 'all'
  })

  const loading = computed(
    () =>
      tasks.loading ||
      quietLeads.loading ||
      stuckDeals.loading ||
      dealStatuses.loading,
  )

  return {
    typeFilter,
    items: filtered,
    counts,
    summary,
    showWhatsApp: computed(() => false),
    loading,
    resources: { tasks, quietLeads, stuckDeals, dealStatuses },
    reload() {
      tasks.reload()
      quietLeads.reload()
      stuckDeals.reload()
      dealStatuses.reload()
    },
  }
}

function normalizePriority(priority, fallback = 'Med') {
  const p = String(priority || '').toLowerCase()
  if (p === 'high' || p === 'urgent') return 'High'
  if (p === 'medium' || p === 'med' || p === 'normal') return 'Med'
  if (p === 'low') return 'Low'
  return fallback === 'High' ? 'High' : fallback === 'Low' ? 'Low' : 'Med'
}

function daysAgoInTz(n, timeZone) {
  const d = new Date()
  d.setDate(d.getDate() - n)
  const { date } = siteDayBounds(d, timeZone)
  return date
}
