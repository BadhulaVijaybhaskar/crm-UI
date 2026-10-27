import { computed, ref } from 'vue'
import { createListResource } from 'frappe-ui'

const STUCK_DAYS = 14
const QUIET_DAYS = 14

/**
 * Build a prioritized work queue from CRM Task, CRM Lead and CRM Deal
 * via existing list resources only.
 */
export function useWorkQueue() {
  const typeFilter = ref('all')
  const today = isoDate()
  const quietBefore = daysAgo(QUIET_DAYS)
  const stuckBefore = daysAgo(STUCK_DAYS)

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
      due_date: ['<=', today],
    },
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
    },
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
    },
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

    for (const t of tasks.data || []) {
      const overdue = t.due_date && t.due_date < today
      rows.push({
        id: `task-${t.name}`,
        type: 'follow_up',
        priority: normalizePriority(t.priority, overdue ? 'High' : 'Medium'),
        title: t.title || t.name,
        subtitle: t.reference_docname
          ? `${t.reference_doctype || ''} · ${t.reference_docname}`.trim()
          : '',
        reason: overdue ? __('Missed deadline') : __('Due today'),
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
        title: [lead.lead_name, lead.organization].filter(Boolean).join(' - ') || lead.name,
        subtitle: lead.status || '',
        reason: __('No recent activity'),
        action: lead.mobile_no ? 'call' : 'open',
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

  const filtered = computed(() => {
    if (typeFilter.value === 'all') return items.value
    if (typeFilter.value === 'calls')
      return items.value.filter((i) => i.type === 'call' || i.action === 'call')
    if (typeFilter.value === 'follow_ups')
      return items.value.filter((i) => i.type === 'follow_up')
    // WhatsApp channel is Connect-owned — keep filter count empty / unused.
    if (typeFilter.value === 'whatsapp') return []
    return items.value
  })

  const counts = computed(() => {
    const all = items.value
    return {
      all: all.length,
      calls: all.filter((i) => i.type === 'call' || i.action === 'call').length,
      whatsapp: 0,
      follow_ups: all.filter((i) => i.type === 'follow_up').length,
      high: all.filter((i) => i.priority === 'High').length,
      med: all.filter((i) => i.priority === 'Med').length,
      low: all.filter((i) => i.priority === 'Low').length,
    }
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

function isoDate(d = new Date()) {
  return d.toISOString().slice(0, 10)
}

function daysAgo(n) {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().slice(0, 10)
}
