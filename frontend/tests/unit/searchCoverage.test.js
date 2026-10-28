import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

describe('CRM-33 search coverage', () => {
  it('indexes Lead, Deal, Contact and Organization in CRMSearch', () => {
    const path = resolve(__dirname, '../../../crm/search_sqlite.py')
    const src = readFileSync(path, 'utf8')
    for (const dt of ['CRM Lead', 'CRM Deal', 'Contact', 'CRM Organization']) {
      expect(src).toContain(`"${dt}"`)
    }
  })
})
