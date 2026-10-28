import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const NAV_API = join(HERE, '../../../crm/api/nav.py')
const NAV_STORE = join(HERE, '../../src/stores/navCounts.js')

describe('nav counts API', () => {
  it('ships a single whitelisted get_nav_counts endpoint', () => {
    const src = readFileSync(NAV_API, 'utf8')
    expect(src).toMatch(/@frappe\.whitelist\(\)/)
    expect(src).toMatch(/def get_nav_counts/)
    expect(src).toMatch(/lead_owner/)
    expect(src).toMatch(/deal_owner/)
    expect(src).toMatch(/CRM Task/)
    // Never invent — omit rather than fake
    expect(src).toMatch(/omit a key rather than fake/)
  })

  it('uses a cached createResource on the frontend', () => {
    const src = readFileSync(NAV_STORE, 'utf8')
    expect(src).toMatch(/crm\.api\.nav\.get_nav_counts/)
    expect(src).toMatch(/cache:\s*['"]crm-nav-counts['"]/)
  })
})
