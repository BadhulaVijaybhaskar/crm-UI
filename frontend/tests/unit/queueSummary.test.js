import { describe, expect, it } from 'vitest'
import {
  classifyQueueType,
  shouldShowWhatsAppFilter,
  summarizeWorkQueue,
} from '@/components/astra/workqueue/queueSummary'

const fixture = [
  { type: 'quiet_lead', action: 'open', priority: 'High' },
  { type: 'follow_up', action: 'follow_up', priority: 'Med' },
  { type: 'follow_up', action: 'follow_up', priority: 'High' },
  { type: 'follow_up', action: 'open', priority: 'Low' },
]

describe('summarizeWorkQueue', () => {
  it('keeps total === sum(type groups) === sum(priority groups)', () => {
    const s = summarizeWorkQueue(fixture, { showWhatsApp: false })
    expect(s.total).toBe(4)
    expect(s.byType.quiet_leads).toBe(1)
    expect(s.byType.follow_ups).toBe(3)
    expect(s.byType.calls).toBeUndefined()
    expect(s.byType.whatsapp).toBeUndefined()
    expect(s.typeTotal).toBe(s.total)
    expect(s.priorityTotal).toBe(s.total)
    expect(s.byPriority.high + s.byPriority.med + s.byPriority.low).toBe(s.total)
    expect(s.byType.quiet_leads + s.byType.follow_ups).toBe(s.total)
  })

  it('includes WhatsApp in type partitions only when shown', () => {
    const withWa = [
      ...fixture,
      { type: 'whatsapp', action: 'whatsapp', priority: 'Med' },
    ]
    const hidden = summarizeWorkQueue(withWa, { showWhatsApp: false })
    expect(hidden.total).toBe(4)
    expect(hidden.typeTotal).toBe(hidden.total)
    expect(hidden.priorityTotal).toBe(hidden.total)

    const shown = summarizeWorkQueue(withWa, { showWhatsApp: true })
    expect(shown.total).toBe(5)
    expect(shown.byType.whatsapp).toBe(1)
    expect(shown.typeTotal).toBe(shown.total)
    expect(shown.priorityTotal).toBe(shown.total)
  })

  it('classifies quiet leads vs follow_up (not Calls)', () => {
    expect(classifyQueueType({ type: 'quiet_lead' })).toBe('quiet_leads')
    expect(classifyQueueType({ type: 'call', action: 'call' })).toBe(
      'quiet_leads',
    )
    expect(classifyQueueType({ type: 'follow_up', action: 'open' })).toBe(
      'follow_ups',
    )
    expect(classifyQueueType({ type: 'whatsapp' })).toBe('whatsapp')
  })
})

describe('shouldShowWhatsAppFilter', () => {
  it('hides when WhatsApp is not installed or has no data', () => {
    expect(
      shouldShowWhatsAppFilter({
        installed: false,
        hasDataSource: false,
        count: 0,
      }),
    ).toBe(false)
    expect(
      shouldShowWhatsAppFilter({
        installed: true,
        hasDataSource: true,
        count: 0,
      }),
    ).toBe(false)
    expect(
      shouldShowWhatsAppFilter({
        installed: false,
        hasDataSource: true,
        count: 3,
      }),
    ).toBe(false)
  })

  it('shows only when installed, data source exists, and count > 0', () => {
    expect(
      shouldShowWhatsAppFilter({
        installed: true,
        hasDataSource: true,
        count: 2,
      }),
    ).toBe(true)
  })
})
