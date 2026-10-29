import { describe, expect, it } from 'vitest'
import {
  ASTRA_STAGE_COLOURS,
  DEFAULT_STAGE_COLOUR_MAP,
  isAstraStageColour,
  stageColourCssVar,
  stageColourStyle,
  stageColourTailwindStem,
  stageColourVarName,
  toAstraStageColour,
} from '../../src/utils/stageColours'

describe('stageColours', () => {
  it('exposes the Astra palette keys from tokens', () => {
    expect(ASTRA_STAGE_COLOURS).toContain('c1')
    expect(ASTRA_STAGE_COLOURS).toContain('c6')
    expect(ASTRA_STAGE_COLOURS).toContain('success')
    expect(ASTRA_STAGE_COLOURS).toContain('danger')
  })

  it('maps default stage names to token keys', () => {
    expect(DEFAULT_STAGE_COLOUR_MAP.Qualification).toBe('c6')
    expect(DEFAULT_STAGE_COLOUR_MAP.Won).toBe('success')
    expect(DEFAULT_STAGE_COLOUR_MAP.Lost).toBe('danger')
  })

  it('keeps Astra keys and remaps legacy names', () => {
    expect(isAstraStageColour('c2')).toBe(true)
    expect(isAstraStageColour('gray')).toBe(false)
    expect(toAstraStageColour('c2')).toBe('c2')
    expect(toAstraStageColour('gray')).toBe('c6')
    expect(toAstraStageColour('green')).toBe('success')
    expect(toAstraStageColour(null, 'Negotiation')).toBe('c5')
  })

  it('builds --crm-* CSS variable references', () => {
    expect(stageColourVarName('c1')).toBe('--crm-c1')
    expect(stageColourCssVar('success')).toBe('var(--crm-success)')
    expect(stageColourStyle('danger')).toEqual({
      backgroundColor: 'var(--crm-danger)',
    })
  })

  it('provides a Tailwind stem for IndicatorIcon fallback', () => {
    expect(stageColourTailwindStem('c6')).toBe('gray')
    expect(stageColourTailwindStem('success')).toBe('green')
    expect(stageColourTailwindStem('orange')).toBe('amber')
  })
})
