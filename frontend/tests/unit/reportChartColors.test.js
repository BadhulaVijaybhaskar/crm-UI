import { describe, expect, it } from 'vitest'
import {
  CHART_COLOR_VARS,
  STAGE_COLOR_TOKEN,
  chartColor,
  stageColor,
} from '@/utils/reports/chartColors'
import { formatDelta, formatKpiValue } from '@/utils/reports/formatKpi'

describe('report chart colours', () => {
  it('exposes six --crm-c* CSS variables', () => {
    expect(CHART_COLOR_VARS).toHaveLength(6)
    expect(CHART_COLOR_VARS[0]).toBe('var(--crm-c1)')
    expect(chartColor(7)).toBe('var(--crm-c2)')
  })

  it('maps stage colours from the handoff tokens', () => {
    expect(STAGE_COLOR_TOKEN.Won).toBe('success')
    expect(stageColor('Won')).toBe('var(--crm-success)')
    expect(stageColor('Negotiation')).toBe('var(--crm-c5)')
    expect(stageColor('Unknown')).toBe('var(--crm-c6)')
  })
})

describe('formatKpiValue', () => {
  it('formats currency in lakh-style units', () => {
    expect(formatKpiValue(680000, 'currency')).toContain('L')
    expect(formatKpiValue(28.6, 'percent')).toBe('28.6%')
  })

  it('formats deltas with direction', () => {
    expect(formatDelta(8.2).direction).toBe('up')
    expect(formatDelta(-3.1).direction).toBe('down')
  })
})
