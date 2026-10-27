/**
 * Unified Activity timeline filter chips (CRM-08).
 * Pure helpers so filter behaviour is unit-tested without mounting Vue.
 */

export const TIMELINE_FILTER_ALL = 'all'

/** Chip definitions shown on the Activity tab (order = display order). */
export const TIMELINE_FILTER_CHIPS = [
  { value: TIMELINE_FILTER_ALL, label: 'All' },
  { value: 'calls', label: 'Calls' },
  { value: 'emails', label: 'Emails' },
  { value: 'notes', label: 'Notes' },
  { value: 'stage', label: 'Stage' },
  { value: 'changes', label: 'Changes' },
  { value: 'comments', label: 'Comments' },
  { value: 'whatsapp', label: 'WhatsApp' },
]

const FILTER_TYPES = {
  calls: new Set(['incoming_call', 'outgoing_call']),
  emails: new Set(['communication']),
  notes: new Set(['note']),
  stage: new Set(['stage_change']),
  changes: new Set(['changed', 'added', 'removed', 'creation', 'attachment_log']),
  comments: new Set(['comment']),
  whatsapp: new Set(['whatsapp']),
}

/**
 * Keep activities matching the selected chip. Unknown filter values behave like All.
 */
export function filterTimelineActivities(activities = [], filter = TIMELINE_FILTER_ALL) {
  if (!filter || filter === TIMELINE_FILTER_ALL) return activities || []
  const allowed = FILTER_TYPES[filter]
  if (!allowed) return activities || []
  return (activities || []).filter((a) => allowed.has(a?.activity_type))
}

/**
 * Map WhatsApp MessageList rows into Activity-timeline shaped events (read-only).
 */
export function whatsappMessagesAsActivities(messages = []) {
  return (messages || []).map((m) => ({
    name: m.name || m.id || `wa-${m.creation}`,
    activity_type: 'whatsapp',
    creation: m.creation || m.timestamp || m.modified,
    owner: m.owner || '',
    data: {
      text: m.message || m.text || m.content || '',
      direction: m.direction,
      status: m.status,
    },
    is_lead: false,
  }))
}
