import { describe, expect, it } from 'vitest'
import {
  avatarTone,
  formatCompactCurrency,
  formatDeltaPercent,
  greetingFor,
  initialsFrom,
  routeForReference,
} from '@/components/astra/format'

describe('astra format helpers', () => {
  it('builds initials from names', () => {
    expect(initialsFrom('Vijay Bhaskar')).toBe('VB')
    expect(initialsFrom('Priya')).toBe('PR')
    expect(initialsFrom('')).toBe('?')
  })

  it('formats compact INR currency', () => {
    expect(formatCompactCurrency(32000000)).toBe('₹3.2Cr')
    expect(formatCompactCurrency(450000)).toBe('₹4.5L')
    expect(formatCompactCurrency(null)).toBe('')
  })

  it('greets by hour', () => {
    expect(greetingFor(new Date('2026-10-28T09:00:00'))).toBe('Good morning')
    expect(greetingFor(new Date('2026-10-28T15:00:00'))).toBe('Good afternoon')
    expect(greetingFor(new Date('2026-10-28T19:00:00'))).toBe('Good evening')
  })

  it('maps reference doctypes to routes', () => {
    expect(routeForReference('CRM Lead', 'CRM-LEAD-1')).toEqual({
      name: 'Lead',
      params: { leadId: 'CRM-LEAD-1' },
    })
    expect(routeForReference('CRM Deal', 'CRM-DEAL-1')).toEqual({
      name: 'Deal',
      params: { dealId: 'CRM-DEAL-1' },
    })
    expect(routeForReference(null, 'x')).toBeNull()
  })

  it('formats delta percent and avatar tones stably', () => {
    expect(formatDeltaPercent(12.4)).toBe('+12%')
    expect(formatDeltaPercent(-3)).toBe('-3%')
    expect(formatDeltaPercent(0)).toBeNull()
    expect(avatarTone('Infosys')).toMatch(/^#/)
  })
})
