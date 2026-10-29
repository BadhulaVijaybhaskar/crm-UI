import { TEMPERATURE_TONES } from '@/components/astra/format'

/** Days since a date string; null when missing/invalid. */
export function quietDaysSince(dateValue) {
  if (!dateValue) return null
  const then = new Date(dateValue)
  if (Number.isNaN(then.getTime())) return null
  const ms = Date.now() - then.getTime()
  if (ms < 0) return 0
  return Math.floor(ms / 86400000)
}

/**
 * Chip tones matching Figma crm.css `.mini.call` / `.mini.note` on the deals board.
 * Warm / Demo / Quote / PO → teal; No next step / Quiet → warning.
 */
function toneForChipLabel(label, fallback = 'mute') {
  if (label === 'Warm') return 'call'
  if (
    label === 'Demo 12:30' ||
    label === 'Quote today' ||
    label === 'PO expected'
  ) {
    return 'call'
  }
  if (label === 'No next step' || /^Quiet\b/i.test(label)) return 'note'
  if (TEMPERATURE_TONES[label]) {
    const t = TEMPERATURE_TONES[label]
    return t === 'muted' ? 'mute' : t
  }
  return fallback
}

/**
 * Build deal-card chips from real row fields only.
 * When the row includes a `chip` key (parity list/kanban payloads), that label
 * is authoritative — empty string means no chip (do not synthesize).
 * Temperature is shown only when the row carries it.
 * Next-step / open-task chips use next_step and _task_count.
 * Quiet N d uses last_responded_on, then modified.
 */
export function dealCardChips(row = {}) {
  const chips = []
  const hasChipKey = Object.prototype.hasOwnProperty.call(row, 'chip')
  const explicit =
    (typeof row.chip === 'object' ? row.chip?.label : row.chip) || ''

  if (hasChipKey) {
    if (explicit) {
      chips.push({
        label: String(explicit),
        tone: toneForChipLabel(String(explicit), 'call'),
      })
    }
    return chips
  }

  const temperature =
    row.temperature?.label ||
    row.temperature ||
    row.deal_temperature?.label ||
    row.deal_temperature ||
    row.lead_temperature?.label ||
    row.lead_temperature ||
    ''
  if (temperature) {
    chips.push({
      label: String(temperature),
      tone: toneForChipLabel(String(temperature), 'mute'),
    })
  }

  const nextActivity =
    (typeof row.next_activity === 'object'
      ? row.next_activity?.label || row.next_activity?.timeAgo
      : row.next_activity) ||
    (typeof row.next_activity_at === 'object'
      ? row.next_activity_at?.label || row.next_activity_at?.timeAgo
      : row.next_activity_at) ||
    (typeof row._next_activity === 'object'
      ? row._next_activity?.label || row._next_activity?.timeAgo
      : row._next_activity) ||
    ''
  const nextStep =
    (typeof row.next_step === 'object' ? row.next_step?.label : row.next_step) ||
    ''
  const taskCount = Number(
    typeof row._task_count === 'object'
      ? row._task_count?.label
      : row._task_count,
  )
  const hasOpenTask = Number.isFinite(taskCount) ? taskCount > 0 : false

  if (nextActivity) {
    chips.push({
      label: String(nextActivity),
      tone: toneForChipLabel(String(nextActivity), 'info'),
    })
  } else if (nextStep) {
    chips.push({
      label: String(nextStep),
      tone: toneForChipLabel(String(nextStep), 'info'),
    })
  } else if (!hasOpenTask) {
    chips.push({ label: __('No next step'), tone: 'warn' })
  }

  const quietSource =
    row.last_responded_on?.label ||
    row.last_responded_on ||
    row.modified?.label ||
    row.modified ||
    ''
  const quiet = quietDaysSince(quietSource)
  if (quiet != null && quiet >= 1) {
    chips.push({ label: __('Quiet {0} d', [quiet]), tone: 'mute' })
  }

  return chips
}

export function stageColourVar(token) {
  if (!token) return 'var(--crm-c6)'
  if (token === 'success') return 'var(--crm-success)'
  if (token === 'danger') return 'var(--crm-danger)'
  return `var(--crm-${token})`
}
