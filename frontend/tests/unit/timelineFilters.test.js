import { describe, expect, it } from 'vitest'
import {
  TIMELINE_FILTER_ALL,
  TIMELINE_FILTER_CHIPS,
  filterTimelineActivities,
  whatsappMessagesAsActivities,
} from '@/utils/timelineFilters'

describe('timelineFilters (CRM-08)', () => {
  const sample = [
    { activity_type: 'incoming_call', name: '1' },
    { activity_type: 'communication', name: '2' },
    { activity_type: 'stage_change', name: '3' },
    { activity_type: 'note', name: '4' },
    { activity_type: 'comment', name: '5' },
    { activity_type: 'changed', name: '6' },
    { activity_type: 'whatsapp', name: '7' },
  ]

  it('exposes chip definitions including stage and whatsapp', () => {
    expect(TIMELINE_FILTER_CHIPS.map((c) => c.value)).toContain('stage')
    expect(TIMELINE_FILTER_CHIPS.map((c) => c.value)).toContain('whatsapp')
  })

  it('returns all rows for the All filter', () => {
    expect(filterTimelineActivities(sample, TIMELINE_FILTER_ALL)).toHaveLength(
      sample.length,
    )
  })

  it('filters by chip type', () => {
    expect(filterTimelineActivities(sample, 'calls').map((a) => a.name)).toEqual([
      '1',
    ])
    expect(filterTimelineActivities(sample, 'stage').map((a) => a.name)).toEqual([
      '3',
    ])
    expect(
      filterTimelineActivities(sample, 'emails').map((a) => a.name),
    ).toEqual(['2'])
  })

  it('maps WhatsApp messages into timeline activities', () => {
    const mapped = whatsappMessagesAsActivities([
      {
        name: 'WA-1',
        creation: '2026-10-27 10:00:00',
        message: 'Hello',
        direction: 'Incoming',
      },
    ])
    expect(mapped[0]).toMatchObject({
      name: 'WA-1',
      activity_type: 'whatsapp',
      data: { text: 'Hello', direction: 'Incoming' },
    })
  })
})
