import { describe, expect, it } from 'vitest'
import {
  LEGAL_SOURCE_LINE,
  legalNotices,
} from '../../src/data/legalNotices'

describe('legal notices content', () => {
  it('lists licence names only — no vendor, project, or repo URLs', () => {
    expect(legalNotices.length).toBeGreaterThan(0)
    for (const item of legalNotices) {
      expect(item.licence).toMatch(/AGPL|MIT|GPL/i)
      expect(item).not.toHaveProperty('name')
      expect(item).not.toHaveProperty('licenceUrl')
      expect(item).not.toHaveProperty('sourceUrl')
      const blob = `${item.licence} ${item.summary}`
      expect(blob).not.toMatch(/frappe|erpnext|github|gitlab|\.io\//i)
    }
  })

  it('points source availability at Astra support only', () => {
    expect(LEGAL_SOURCE_LINE).toMatch(/Source code available on request via Astra support/)
    expect(LEGAL_SOURCE_LINE).not.toMatch(/github|gitlab|frappe/i)
  })
})
