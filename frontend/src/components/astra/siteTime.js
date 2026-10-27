/**
 * Site-timezone calendar helpers for day-bounded list filters.
 * Prefer Frappe systemTimezone (boot); fall back to user/local, then UTC.
 */

export function getSiteTimezone(getConfigFn) {
  if (typeof getConfigFn === 'function') {
    return (
      getConfigFn('systemTimezone') ||
      getConfigFn('localTimezone') ||
      'UTC'
    )
  }
  return 'UTC'
}

/**
 * Calendar YYYY-MM-DD for `date` in `timeZone` (Intl, no UTC slice).
 * @param {Date|string|number} [date]
 * @param {string} [timeZone]
 */
export function calendarDateInTimezone(date = new Date(), timeZone = 'UTC') {
  const d = date instanceof Date ? date : new Date(date)
  if (Number.isNaN(d.getTime())) return ''
  try {
    // en-CA → YYYY-MM-DD
    return new Intl.DateTimeFormat('en-CA', {
      timeZone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(d)
  } catch {
    return d.toISOString().slice(0, 10)
  }
}

/**
 * Whole-day range [start, end] in site timezone for Datetime filters.
 * @returns {{ date: string, start: string, end: string, monthStart: string }}
 */
export function siteDayBounds(date = new Date(), timeZone = 'UTC') {
  const day = calendarDateInTimezone(date, timeZone)
  if (!day) {
    return { date: '', start: '', end: '', monthStart: '' }
  }
  return {
    date: day,
    start: `${day} 00:00:00`,
    end: `${day} 23:59:59`,
    monthStart: `${day.slice(0, 8)}01`,
  }
}
