import { describe, expect, it } from 'vitest'
import { readFileSync, existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const CRM_ROOT = join(HERE, '../../../crm')

function readCrm(...parts) {
  return readFileSync(join(CRM_ROOT, ...parts), 'utf8')
}

describe('Astra branding chrome (no vendor text in served HTML)', () => {
  it('overrides footer_powered with an empty template', () => {
    const html = readCrm('templates/includes/footer/footer_powered.html')
    expect(html).not.toMatch(/frappe|powered by|built on/i)
    // No user-visible markup — comments only
    expect(html.replace(/\{#[\s\S]*?#\}/g, '').trim()).toBe('')
  })

  it('footer_info has no powered-by column', () => {
    const html = readCrm('templates/includes/footer/footer_info.html').replace(
      /\{#[\s\S]*?#\}/g,
      '',
    )
    expect(html).not.toMatch(/footer_powered|powered-by|frappe/i)
    expect(html).not.toMatch(/footer-powered/)
  })

  it('email footer override has no default_mail_footer / Sent via block', () => {
    const html = readCrm('templates/emails/email_footer.html')
    expect(html).not.toMatch(/default_mail_footer|Sent via|frappe/i)
  })

  it('CRM invitation email has no upstream vendor names', () => {
    const html = readCrm('templates/emails/crm_invitation.html')
    expect(html).toMatch(/Astra CRM/)
    expect(html).not.toMatch(/frappe|erpnext|powered by|agpl/i)
  })

  it('CRM login override clears the footer block', () => {
    const html = readCrm('www/login.html')
    expect(html).toMatch(/block footer/)
    expect(html).toMatch(/\{\%\s*block footer\s*\%\}\{\%\s*endblock\s*\%\}/)
  })

  it('does not CSS-hide powered-by (text must be absent from HTML instead)', () => {
    const css = readCrm('public/css/astra-login.css')
    expect(css).not.toMatch(/footer-powered|powered-by-frappe/)
  })

  it('ships the astra branding scrub patch', () => {
    expect(
      existsSync(join(CRM_ROOT, 'patches/v1_0/astra_branding_scrub.py')),
    ).toBe(true)
    const patches = readCrm('patches.txt')
    expect(patches).toMatch(/astra_branding_scrub/)
  })

  it('keeps the Workspace document name stable (label/title only)', () => {
    const ws = readCrm('fcrm/workspace/frappe_crm/frappe_crm.json')
    expect(ws).toMatch(/"name": "Frappe CRM"/)
    expect(ws).toMatch(/"label": "Astra CRM"/)
    expect(ws).toMatch(/"title": "Astra CRM"/)
  })
})
