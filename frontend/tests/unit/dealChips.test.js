import { describe, expect, it } from 'vitest'
import {
  dealCardChips,
  quietDaysSince,
  stageColourVar,
} from '@/components/astra/dealChips'

describe('dealCardChips', () => {
  it('omits temperature when the row has none', () => {
    const chips = dealCardChips({ next_step: 'Send quote', _task_count: 1 })
    expect(chips.some((c) => c.label === 'Hot')).toBe(false)
    expect(chips.some((c) => c.label === 'Send quote')).toBe(true)
  })

  it('adds temperature only from real fields', () => {
    const chips = dealCardChips({ lead_temperature: 'Hot', _task_count: 1 })
    expect(chips[0]).toMatchObject({ label: 'Hot', tone: 'danger' })
  })

  it('shows No next step when there is no open task and no next_step', () => {
    const chips = dealCardChips({ _task_count: 0 })
    expect(chips.some((c) => c.label.includes('No next step'))).toBe(true)
  })

  it('does not show No next step when a next_step exists', () => {
    const chips = dealCardChips({ next_step: 'Call CFO', _task_count: 0 })
    expect(chips.some((c) => c.label.includes('No next step'))).toBe(false)
    expect(chips.some((c) => c.label === 'Call CFO')).toBe(true)
  })

  it('adds Quiet N d from last activity date', () => {
    const threeDaysAgo = new Date(Date.now() - 3 * 86400000).toISOString()
    const chips = dealCardChips({
      _task_count: 1,
      last_responded_on: threeDaysAgo,
    })
    expect(chips.some((c) => /Quiet 3 d/.test(c.label))).toBe(true)
  })
})

describe('quietDaysSince', () => {
  it('returns null for empty values', () => {
    expect(quietDaysSince('')).toBeNull()
    expect(quietDaysSince(null)).toBeNull()
  })
})

describe('stageColourVar', () => {
  it('maps stage tokens to css vars', () => {
    expect(stageColourVar('c6')).toBe('var(--crm-c6)')
    expect(stageColourVar('success')).toBe('var(--crm-success)')
    expect(stageColourVar('danger')).toBe('var(--crm-danger)')
  })
})
