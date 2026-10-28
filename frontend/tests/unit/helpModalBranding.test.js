import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  ONBOARDING_APP_NAME,
  formatOnboardingProgressLabel,
} from '@/components/astra/myday/myDayHelpers'

const HERE = dirname(fileURLToPath(import.meta.url))
const SIDEBAR = join(HERE, '../../src/components/Layouts/AppSidebar.vue')
const HELP_WRAP = join(
  HERE,
  '../../src/components/Layouts/OnboardingHelpModal.vue',
)

describe('HelpModal branding (Astra)', () => {
  it('overrides frappe-ui HelpModal defaults that would show vendor title/docs', () => {
    const src = readFileSync(SIDEBAR, 'utf8')
    expect(src).toMatch(/<OnboardingHelpModal[\s\S]*?title="Astra CRM"/)
    expect(src).toMatch(/docsLink=""/)
    expect(src).not.toMatch(/docs\.frappe\.io/)
    expect(src).not.toMatch(/title="Frappe CRM"/)
  })

  it('uses the internal frappecrm onboarding key (not branded crm)', () => {
    expect(ONBOARDING_APP_NAME).toBe('frappecrm')
    const sidebar = readFileSync(SIDEBAR, 'utf8')
    const wrap = readFileSync(HELP_WRAP, 'utf8')
    // Must not reintroduce the branding mismatch that caused HelpModal 0/0 · NaN%.
    expect(sidebar).not.toMatch(/appName="crm"/)
    expect(wrap).toMatch(/ONBOARDING_APP_NAME/)
    expect(wrap).toMatch(/:appName="ONBOARDING_APP_NAME"/)
    expect(sidebar).toMatch(/useOnboarding\(ONBOARDING_APP_NAME\)/)
  })

  it('never formats a NaN% progress label for HelpModal', () => {
    expect(formatOnboardingProgressLabel(0, 0)).toBe(null)
    expect(formatOnboardingProgressLabel(1, 0)).toBe(null)
    const label = formatOnboardingProgressLabel(1, 4)
    expect(label).toBe('1/4 steps · 25%')
    expect(label).not.toMatch(/NaN/)
  })
})
