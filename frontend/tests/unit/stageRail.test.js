import { describe, expect, it } from 'vitest'
import {
  daysSince,
  openStageStart,
  pipelineStages,
  stageEnteredOn,
  stageMarkerColor,
  stageState,
} from '@/components/Pipeline/stageRail'

describe('stage rail', () => {
  const stages = [
    { name: 'Qualification', type: 'Open' },
    { name: 'Negotiation', type: 'Ongoing' },
    { name: 'Won', type: 'Won' },
    { name: 'Lost', type: 'Lost' },
  ]

  it('keeps pipeline order and drops rows without a name', () => {
    const allowed = ['Negotiation', 'Won']
    expect(
      pipelineStages(
        [{ name: 'Qualification' }, { type: 'Open' }, { name: 'Negotiation' }, { name: 'Won' }],
        allowed,
      ).map((stage) => stage.name),
    ).toEqual(['Negotiation', 'Won'])
  })

  it('marks the current stage, earlier stages done, and later stages todo', () => {
    expect(stageState(stages[0], 0, 1)).toBe('done')
    expect(stageState(stages[1], 1, 1)).toBe('current')
    expect(stageState(stages[2], 2, 1)).toBe('todo')
    expect(stageState(stages[2], 2, 2)).toBe('won')
    expect(stageState(stages[3], 3, 3)).toBe('lost')
  })

  it('reads the date a stage was entered and the open stage start', () => {
    const rows = [
      { from: 'Qualification', to: 'Negotiation', to_date: '2026-10-16' },
      { from: 'Negotiation', from_date: '2026-10-22' },
    ]
    expect(stageEnteredOn(rows)).toEqual({
      Negotiation: '2026-10-16',
    })
    expect(openStageStart(rows, 'Negotiation')).toBe('2026-10-22')
    expect(daysSince('2026-10-26', Date.parse('2026-10-28T00:00:00Z'))).toBe(2)
    expect(daysSince('')).toBe(null)
  })

  it('maps known stage names onto token colours', () => {
    expect(stageMarkerColor('Won')).toBe('var(--crm-success)')
    expect(stageMarkerColor('Lost')).toBe('var(--crm-danger)')
    expect(stageMarkerColor('Negotiation')).toBe('var(--crm-c5)')
  })
})
