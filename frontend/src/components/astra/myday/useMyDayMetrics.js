import { computed } from 'vue'
import { createListResource, getConfig } from 'frappe-ui'
import { formatCompactCurrency } from '@/components/astra/format'
import { getSiteTimezone, siteDayBounds } from '@/components/astra/siteTime'
import { wonDealsInPeriod } from '@/components/astra/myday/myDayHelpers'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { buildOwnerScope } from '@/components/astra/workqueue/queueHelpers'

/**
 * Extra My day metrics from existing list/API resources (no new backend).
 * Target gauge is omitted unless a sales-target field is discoverable on boot/meta.
 */
export function useMyDayMetrics() {
  const { user } = sessionStore()
  const { isManager } = usersStore()
  const manager = isManager()

  const tz = getSiteTimezone(getConfig)
  const bounds = siteDayBounds(new Date(), tz)
  const monthStart = bounds.monthStart
  const dayStart = bounds.start
  const dayEnd = bounds.end

  const openDeals = createListResource({
    doctype: 'CRM Deal',
    fields: [
      'name',
      'deal_value',
      'expected_deal_value',
      'exchange_rate',
      'status',
      'modified',
    ],
    filters: {},
    orderBy: 'modified desc',
    pageLength: 200,
    auto: true,
    cache: 'astra-myday-open-deals',
  })

  const dealStatuses = createListResource({
    doctype: 'CRM Deal Status',
    fields: ['name', 'type'],
    pageLength: 50,
    auto: true,
    cache: 'astra-myday-deal-statuses',
  })

  const wonDeals = createListResource({
    doctype: 'CRM Deal',
    fields: [
      'name',
      'deal_value',
      'exchange_rate',
      'closed_date',
      'modified',
      'status',
    ],
    filters: {
      // Won KPI keys off close date, not modified.
      closed_date: ['>=', monthStart],
    },
    orderBy: 'closed_date desc',
    pageLength: 200,
    auto: true,
    cache: 'astra-myday-won-deals',
  })

  const hotLeads = createListResource({
    doctype: 'CRM Lead',
    fields: [
      'name',
      'lead_name',
      'organization',
      'lead_score',
      'lead_temperature',
      'mobile_no',
      'email',
      'status',
    ],
    filters: {
      converted: 0,
    },
    orderBy: 'lead_score desc',
    pageLength: 8,
    auto: true,
    cache: 'astra-myday-hot-leads',
  })

  const callScope = buildOwnerScope({
    isManager: manager,
    user,
    doctype: 'CRM Call Log',
    ownerField: 'owner',
  })
  // Calls KPI: non-managers see only their calls (caller / receiver / owner).
  const callOrFilters = manager
    ? undefined
    : [
        ['CRM Call Log', 'caller', '=', user],
        ['CRM Call Log', 'receiver', '=', user],
        ['CRM Call Log', 'owner', '=', user],
      ]

  const todayCalls = createListResource({
    doctype: 'CRM Call Log',
    fields: [
      'name',
      'creation',
      'type',
      'status',
      'duration',
      'caller',
      'receiver',
      'owner',
    ],
    filters: {
      creation: ['between', [dayStart, dayEnd]],
      ...callScope.filters,
    },
    orFilters: callOrFilters,
    orderBy: 'creation desc',
    pageLength: 100,
    auto: true,
    cache: 'astra-myday-calls-today',
  })

  // No monthly sales-target field exists on CRM Deal / FCRM Settings today.
  // Keep target null so the UI shows a designed empty state (never invent %).
  const target = computed(() => null)

  const statusTypeByName = computed(() => {
    const map = {}
    for (const s of dealStatuses.data || []) map[s.name] = s.type
    return map
  })

  const pipelineDeals = computed(() => {
    const types = statusTypeByName.value
    return (openDeals.data || []).filter((d) => {
      const t = types[d.status]
      return t !== 'Won' && t !== 'Lost'
    })
  })

  const pipelineValue = computed(() =>
    pipelineDeals.value.reduce((sum, d) => sum + dealAmount(d), 0),
  )

  const wonThisMonth = computed(() =>
    wonDealsInPeriod(wonDeals.data || [], {
      monthStart,
      statusTypeByName: statusTypeByName.value,
    }),
  )

  const wonValue = computed(() =>
    wonThisMonth.value.reduce((sum, d) => sum + dealAmount(d), 0),
  )

  const callsCount = computed(() => (todayCalls.data || []).length)

  const pipelineSpark = computed(() => sparkFromDeals(pipelineDeals.value))
  const wonSpark = computed(() => sparkFromDeals(wonThisMonth.value, 'closed_date'))
  const callsSpark = computed(() =>
    (todayCalls.data || [])
      .slice()
      .reverse()
      .map((_, i) => i + 1),
  )

  const hotLeadRows = computed(() => {
    const rows = hotLeads.data || []
    const hot = rows.filter((r) => r.lead_temperature === 'Hot')
    const source = hot.length ? hot : rows
    return source
      .filter((r) => Number(r.lead_score) > 0 || r.lead_temperature === 'Hot')
      .slice(0, 5)
  })

  const kpis = computed(() => [
    {
      key: 'pipeline',
      label: 'Pipeline',
      value: formatCompactCurrency(pipelineValue.value) || '—',
      spark: pipelineSpark.value,
      delta: null,
      loading: openDeals.loading || dealStatuses.loading,
    },
    {
      key: 'won',
      label: 'Won',
      value: formatCompactCurrency(wonValue.value) || '—',
      spark: wonSpark.value,
      delta: null,
      loading: wonDeals.loading || dealStatuses.loading,
    },
    {
      key: 'calls',
      label: 'Calls',
      value: String(callsCount.value),
      spark: callsSpark.value,
      delta: null,
      loading: todayCalls.loading,
    },
  ])

  return {
    kpis,
    hotLeadRows,
    hotLeads,
    target,
    reload() {
      openDeals.reload()
      wonDeals.reload()
      hotLeads.reload()
      todayCalls.reload()
      dealStatuses.reload()
    },
  }
}

function dealAmount(d) {
  const value = Number(d.deal_value || d.expected_deal_value || 0)
  const rate = Number(d.exchange_rate || 1) || 1
  return value * rate
}

function sparkFromDeals(deals, dateField = 'modified') {
  if (!deals?.length) return []
  const sorted = [...deals].sort((a, b) =>
    String(a[dateField] || a.modified).localeCompare(
      String(b[dateField] || b.modified),
    ),
  )
  let running = 0
  return sorted.map((d) => {
    running += dealAmount(d)
    return running
  })
}
