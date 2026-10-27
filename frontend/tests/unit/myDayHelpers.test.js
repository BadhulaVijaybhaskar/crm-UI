import { describe, expect, it } from 'vitest'
import {
  ONBOARDING_APP_NAME,
  filterUpcomingCalls,
  formatOnboardingProgressLabel,
  isUpcomingCall,
  onboardingProgressPercent,
  shouldShowGettingStartedBanner,
  wonDealsInPeriod,
} from '@/components/astra/myday/myDayHelpers'

describe('isUpcomingCall / filterUpcomingCalls', () => {
  const now = new Date('2026-10-27T12:00:00.000Z')

  it('excludes completed and other terminal statuses', () => {
    expect(
      isUpcomingCall(
        { status: 'Completed', creation: '2026-10-27 18:00:00' },
        now,
      ),
    ).toBe(false)
    expect(
      isUpcomingCall(
        { status: 'Failed', start_time: '2026-10-28 10:00:00' },
        now,
      ),
    ).toBe(false)
    expect(
      isUpcomingCall(
        { status: 'No Answer', creation: '2026-10-28 10:00:00' },
        now,
      ),
    ).toBe(false)
  })

  it('keeps only future scheduled calls', () => {
    expect(
      isUpcomingCall(
        { status: 'Queued', start_time: '2026-10-27T18:00:00.000Z' },
        now,
      ),
    ).toBe(true)
    expect(
      isUpcomingCall(
        { status: 'Initiated', creation: '2026-10-27T08:00:00.000Z' },
        now,
      ),
    ).toBe(false)

    const list = filterUpcomingCalls(
      [
        {
          name: 'a',
          status: 'Completed',
          creation: '2026-10-27T13:00:00.000Z',
        },
        {
          name: 'b',
          status: 'Queued',
          start_time: '2026-10-27T15:00:00.000Z',
        },
        {
          name: 'c',
          status: 'Ringing',
          creation: '2026-10-27T11:00:00.000Z',
        },
      ],
      now,
    )
    expect(list.map((c) => c.name)).toEqual(['b'])
  })
})

describe('wonDealsInPeriod', () => {
  it('filters by closed_date and Won status type', () => {
    const types = { Won: 'Won', Open: 'Open' }
    const deals = [
      { name: '1', status: 'Won', closed_date: '2026-10-05' },
      { name: '2', status: 'Won', closed_date: '2026-09-30' },
      { name: '3', status: 'Open', closed_date: '2026-10-10' },
      { name: '4', status: 'Won', closed_date: null },
    ]
    expect(
      wonDealsInPeriod(deals, {
        monthStart: '2026-10-01',
        statusTypeByName: types,
      }).map((d) => d.name),
    ).toEqual(['1'])
  })
})

describe('Getting started empty / NaN guard', () => {
  it('keeps the internal onboarding app name as frappecrm', () => {
    expect(ONBOARDING_APP_NAME).toBe('frappecrm')
  })

  it('returns null percent and hides banner when totalSteps is 0', () => {
    expect(onboardingProgressPercent(0, 0)).toBe(null)
    expect(onboardingProgressPercent(1, 0)).toBe(null)
    expect(formatOnboardingProgressLabel(0, 0)).toBe(null)
    expect(String(formatOnboardingProgressLabel(0, 0) ?? '')).not.toMatch(/NaN/)
    expect(shouldShowGettingStartedBanner({ completed: false, totalSteps: 0 })).toBe(
      false,
    )
    expect(
      shouldShowGettingStartedBanner({ completed: false, totalSteps: 4 }),
    ).toBe(true)
    expect(
      shouldShowGettingStartedBanner({ completed: true, totalSteps: 4 }),
    ).toBe(false)
  })

  it('computes a finite percent when steps exist', () => {
    expect(onboardingProgressPercent(1, 4)).toBe(25)
    expect(onboardingProgressPercent(0, 4)).toBe(0)
    expect(Number.isNaN(onboardingProgressPercent(0, 0))).toBe(false)
    expect(formatOnboardingProgressLabel(1, 4)).toBe('1/4 steps · 25%')
    expect(formatOnboardingProgressLabel(0, 4)).toBe('0/4 steps · 0%')
  })
})
