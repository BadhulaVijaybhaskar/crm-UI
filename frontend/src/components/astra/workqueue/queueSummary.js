/**
 * Pure Work queue helpers — counts always derive from one item list.
 */

export function classifyQueueType(item) {
  if (!item) return 'follow_ups'
  if (item.type === 'whatsapp') return 'whatsapp'
  // Quiet leads (no recent activity) — not telephony "calls".
  if (item.type === 'quiet_lead') return 'quiet_leads'
  // Legacy: older rows used type/action "call" for quiet leads.
  if (item.type === 'call' || item.action === 'call') return 'quiet_leads'
  return 'follow_ups'
}

/**
 * Summarize a queue list. Type and priority buckets are partitions of `items`
 * (or of the subset after dropping WhatsApp when it is hidden).
 *
 * Invariants (asserted by unit tests):
 *   total === sum(typeGroups) === sum(priorityGroups)
 */
export function summarizeWorkQueue(items = [], { showWhatsApp = false } = {}) {
  const visible = showWhatsApp
    ? items
    : items.filter((i) => classifyQueueType(i) !== 'whatsapp')

  const byType = { quiet_leads: 0, follow_ups: 0 }
  if (showWhatsApp) byType.whatsapp = 0

  const byPriority = { high: 0, med: 0, low: 0 }

  for (const item of visible) {
    const t = classifyQueueType(item)
    if (t === 'whatsapp') byType.whatsapp += 1
    else if (t === 'quiet_leads') byType.quiet_leads += 1
    else byType.follow_ups += 1

    if (item.priority === 'High') byPriority.high += 1
    else if (item.priority === 'Low') byPriority.low += 1
    else byPriority.med += 1
  }

  const typeTotal = Object.values(byType).reduce((a, b) => a + b, 0)
  const priorityTotal = Object.values(byPriority).reduce((a, b) => a + b, 0)
  const total = visible.length

  return {
    total,
    byType,
    byPriority,
    typeTotal,
    priorityTotal,
  }
}

/**
 * WhatsApp filter chip: only when the app/doctype is installed, a data source
 * is available, and there is at least one real message/action — never a zero chip.
 */
export function shouldShowWhatsAppFilter({
  installed = false,
  hasDataSource = false,
  count = 0,
} = {}) {
  return Boolean(installed && hasDataSource && Number(count) > 0)
}
