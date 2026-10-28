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
 * Build deal-card chips from real row fields only.
 * Temperature is shown only when the row carries it.
 * Next-step / open-task chips use next_step and _task_count.
 * Quiet N d uses last_responded_on, then modified.
 */
export function dealCardChips(row = {}) {
  const chips = []

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
      tone: TEMPERATURE_TONES[temperature] || 'mute',
    })
  }

  const nextStep =
    (typeof row.next_step === 'object' ? row.next_step?.label : row.next_step) ||
    ''
  const taskCount = Number(
    typeof row._task_count === 'object'
      ? row._task_count?.label
      : row._task_count,
  )
  const hasOpenTask = Number.isFinite(taskCount) ? taskCount > 0 : false

  if (nextStep) {
    chips.push({ label: String(nextStep), tone: 'info' })
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
