import { describe, expect, it } from 'vitest'
import { formatCompactCurrency } from '@/utils/compactCurrency'

describe('formatCompactCurrency', () => {
  it('formats INR lakhs and crores', () => {
    expect(formatCompactCurrency(3840000, 'INR')).toBe('₹38.4 L')
    expect(formatCompactCurrency(21000000, 'INR')).toBe('₹2.1 Cr')
  })

  it('formats smaller INR amounts with a symbol', () => {
    expect(formatCompactCurrency(850, 'INR')).toMatch(/₹|INR|850/)
  })
})
