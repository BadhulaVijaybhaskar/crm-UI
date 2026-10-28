import { describe, expect, it } from 'vitest'
import {
  LEGAL_SOURCE_LINE,
  legalNotices,
} from '../../src/data/legalNotices'

describe('legal notices content', () => {
  it('lists unique licence names only — no summaries or intro copy', () => {
    expect(legalNotices).toEqual(['GNU AGPL-3.0', 'GPL-3.0', 'MIT'])
    expect(new Set(legalNotices).size).toBe(legalNotices.length)
    for (const item of legalNotices) {
      expect(typeof item).toBe('string')
      expect(item).toMatch(/AGPL|MIT|GPL/i)
      expect(item).not.toMatch(/frappe|erpnext|github|gitlab|\.io\//i)
    }
  })

  it('points source availability at Astra support only', () => {
    expect(LEGAL_SOURCE_LINE).toBe(
      'Source code available on request via Astra support',
    )
    expect(LEGAL_SOURCE_LINE).not.toMatch(/github|gitlab|frappe/i)
  })
})
