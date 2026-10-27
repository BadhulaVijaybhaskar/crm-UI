import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const SIDEBAR = join(HERE, '../../src/components/Layouts/AppSidebar.vue')

describe('HelpModal branding (Astra)', () => {
  it('overrides frappe-ui HelpModal defaults that would show vendor title/docs', () => {
    const src = readFileSync(SIDEBAR, 'utf8')
    expect(src).toMatch(/<HelpModal[\s\S]*?title="Astra CRM"/)
    expect(src).toMatch(/docsLink=""/)
    expect(src).not.toMatch(/docs\.frappe\.io/)
    // Default frappe-ui strings must not be relied on
    expect(src).not.toMatch(/title="Frappe CRM"/)
  })
})
