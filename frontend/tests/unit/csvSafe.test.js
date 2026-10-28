import { describe, expect, it } from 'vitest'
import {
  companyDomainFromWebsite,
  guardCsvCell,
} from '@/utils/csvSafe'

describe('guardCsvCell', () => {
  it('prefixes formula-like values', () => {
    expect(guardCsvCell('=CMD()')).toBe("'=CMD()")
    expect(guardCsvCell('+1234')).toBe("'+1234")
    expect(guardCsvCell('-1+1')).toBe("'-1+1")
    expect(guardCsvCell('@sum')).toBe("'@sum")
  })

  it('leaves normal values alone', () => {
    expect(guardCsvCell('hello')).toBe('hello')
    expect(guardCsvCell('user@example.com')).toBe('user@example.com')
    expect(guardCsvCell(42)).toBe('42')
    expect(guardCsvCell(null)).toBe('')
  })
})

describe('companyDomainFromWebsite', () => {
  it('extracts host from urls and emails', () => {
    expect(companyDomainFromWebsite('https://www.Acme.example/path')).toBe(
      'acme.example',
    )
    expect(companyDomainFromWebsite('acme.example')).toBe('acme.example')
    expect(companyDomainFromWebsite('sales@acme.example')).toBe('acme.example')
  })
})
