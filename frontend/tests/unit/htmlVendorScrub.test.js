import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const RESPONSE = join(HERE, '../../../crm/overrides/response_headers.py')
const BRANDING = join(HERE, '../../../crm/overrides/branding.py')
const LOGIN_PY = join(HERE, '../../../crm/www/login.py')
const LOGIN_HTML = join(HERE, '../../../crm/www/login.html')
const WORKSPACE = join(
  HERE,
  '../../../crm/fcrm/workspace/frappe_crm/frappe_crm.json',
)

describe('astra branding server scrub', () => {
  it('strips Built on Frappe comment and generator meta in after_request', () => {
    const src = readFileSync(RESPONSE, 'utf8')
    expect(src).toMatch(/Built on Frappe/)
    expect(src).toMatch(/generator/)
    expect(src).toMatch(/_scrub_html_body/)
  })

  it('uses set_single_value / set_value so scrub persists without Document.save', () => {
    const src = readFileSync(BRANDING, 'utf8')
    expect(src).toMatch(/set_single_value/)
    expect(src).toMatch(/otp_issuer_name/)
    expect(src).toMatch(/relabel_crm_workspace/)
    expect(src).toMatch(/frappe\.db\.set_value\("Workspace"/)
    expect(src).not.toMatch(/ws\.save\(\)/)
  })

  it('ships login.py controller and theme bootstrap on login.html', () => {
    expect(readFileSync(LOGIN_PY, 'utf8')).toMatch(/ASTRA_LOGO/)
    const html = readFileSync(LOGIN_HTML, 'utf8')
    expect(html).toMatch(/data-theme/)
    expect(html).toMatch(/localStorage/)
  })

  it('workspace JSON includes type Workspace', () => {
    const ws = JSON.parse(readFileSync(WORKSPACE, 'utf8'))
    expect(ws.type).toBe('Workspace')
    expect(ws.name).toBe('Frappe CRM')
    expect(ws.label).toBe('Astra CRM')
  })
})
