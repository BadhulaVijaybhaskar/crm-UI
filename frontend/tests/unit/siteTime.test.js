import { describe, expect, it } from 'vitest'
import {
  calendarDateInTimezone,
  getSiteTimezone,
  siteDayBounds,
} from '@/components/astra/siteTime'

describe('siteDayBounds', () => {
  it('uses a whole-day range in the site timezone (not UTC slice)', () => {
    // 2026-10-27 20:30 UTC → still 2026-10-28 early morning in IST
    const utcEvening = new Date('2026-10-27T20:30:00.000Z')
    const ist = siteDayBounds(utcEvening, 'Asia/Kolkata')
    expect(ist.date).toBe('2026-10-28')
    expect(ist.start).toBe('2026-10-28 00:00:00')
    expect(ist.end).toBe('2026-10-28 23:59:59')
    expect(ist.monthStart).toBe('2026-10-01')
  })

  it('keeps the UTC calendar day when timezone is UTC', () => {
    const noon = new Date('2026-10-27T12:00:00.000Z')
    const bounds = siteDayBounds(noon, 'UTC')
    expect(bounds.date).toBe('2026-10-27')
    expect(bounds.start).toBe('2026-10-27 00:00:00')
    expect(bounds.end).toBe('2026-10-27 23:59:59')
  })

  it('calendarDateInTimezone differs from UTC ISO near midnight boundaries', () => {
    const almostMidnightUtc = new Date('2026-03-15T22:00:00.000Z')
    expect(almostMidnightUtc.toISOString().slice(0, 10)).toBe('2026-03-15')
    expect(calendarDateInTimezone(almostMidnightUtc, 'Asia/Kolkata')).toBe(
      '2026-03-16',
    )
  })

  it('prefers systemTimezone from getConfig', () => {
    const getConfig = (key) =>
      key === 'systemTimezone' ? 'Asia/Kolkata' : null
    expect(getSiteTimezone(getConfig)).toBe('Asia/Kolkata')
  })
})
