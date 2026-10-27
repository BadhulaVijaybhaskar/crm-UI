/**
 * Pure My day helpers — upcoming calls, Won date, Getting started empty guard.
 */

const TERMINAL_CALL_STATUSES = new Set([
  'Completed',
  'Failed',
  'Busy',
  'No Answer',
  'Canceled',
  'Cancelled',
])

/**
 * Upcoming calls: future/scheduled only — exclude completed/terminal statuses
 * and anything whose start/creation is already in the past.
 */
export function isUpcomingCall(call, now = new Date()) {
  if (!call) return false
  if (TERMINAL_CALL_STATUSES.has(call.status)) return false
  const when = call.start_time || call.creation
  if (!when) return true
  const t = new Date(when)
  if (Number.isNaN(t.getTime())) return true
  const n = now instanceof Date ? now : new Date(now)
  return t.getTime() >= n.getTime()
}

export function filterUpcomingCalls(calls = [], now = new Date()) {
  return calls.filter((c) => isUpcomingCall(c, now))
}

/** Won KPI uses deal closed_date (not modified). */
export function wonDealsInPeriod(deals = [], { monthStart, statusTypeByName } = {}) {
  if (!monthStart) return []
  return deals.filter((d) => {
    if (!d?.closed_date) return false
    if (String(d.closed_date).slice(0, 10) < monthStart) return false
    if (statusTypeByName) {
      return statusTypeByName[d.status] === 'Won'
    }
    return true
  })
}

/**
 * Getting started progress. Guard 0/0 → null (hide), never NaN%.
 * @returns {number|null}
 */
export function onboardingProgressPercent(stepsCompleted, totalSteps) {
  const total = Number(totalSteps)
  const done = Number(stepsCompleted)
  if (!Number.isFinite(total) || total <= 0) return null
  if (!Number.isFinite(done) || done < 0) return 0
  return Math.round((done / total) * 100)
}

/**
 * Human-readable progress for Getting started / Help panels.
 * Returns null when there are no steps — callers must not render "0/0 · NaN%".
 * @returns {string|null}
 */
export function formatOnboardingProgressLabel(stepsCompleted, totalSteps) {
  const percent = onboardingProgressPercent(stepsCompleted, totalSteps)
  if (percent == null) return null
  const total = Number(totalSteps)
  const done = Math.min(Math.max(0, Number(stepsCompleted) || 0), total)
  return `${done}/${total} steps · ${percent}%`
}

export function shouldShowGettingStartedBanner({
  completed = false,
  totalSteps = 0,
} = {}) {
  const total = Number(totalSteps)
  if (!Number.isFinite(total) || total <= 0) return false
  return !completed
}
