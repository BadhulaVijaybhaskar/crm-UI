import { beforeAll, describe, expect, it, vi } from 'vitest'

vi.mock('@/composables/whatsapp', () => ({
  isWhatsAppInstalled: { value: false },
}))

vi.mock('@/stores/users', () => ({
  usersStore: () => ({
    isManager: () => true,
    isAdmin: () => true,
  }),
}))

let sectionFromSlug
let settingsGroups
let slugFromLabel

beforeAll(async () => {
  ;({ sectionFromSlug, settingsGroups, slugFromLabel } = await import(
    '@/components/Settings/settingsSections'
  ))
})

describe('settings sections', () => {
  it('uses the settings page groups', () => {
    expect(settingsGroups.map((group) => group.label)).toEqual([
      'Personal',
      'Workspace',
      'Users',
      'Pipeline & Fields',
      'Automation',
      'Email',
      'Integrations',
    ])
  })

  it('resolves slugs and the labels callers already pass', () => {
    expect(sectionFromSlug('users')?.label).toBe('Users')
    expect(sectionFromSlug('pipeline-stages')?.label).toBe('Pipeline stages')
    expect(sectionFromSlug('fields-layout')?.label).toBe('Fields layout')
    expect(slugFromLabel('Invite User')).toBe('invite-user')
    expect(slugFromLabel('invite-user')).toBe('invite-user')
    expect(slugFromLabel('Accounts')).toBe('accounts')
    expect(slugFromLabel('WhatsApp')).toBe('whatsapp')
    expect(slugFromLabel('Templates')).toBe('templates')
    expect(slugFromLabel('API & webhooks')).toBe('api-webhooks')
    expect(slugFromLabel('missing')).toBeNull()
  })

  it('keeps the sections that already work', () => {
    const labels = settingsGroups.flatMap((group) =>
      group.items.map((item) => item.label),
    )
    expect(labels).toEqual(
      expect.arrayContaining([
        'Profile',
        'Preferences',
        'General',
        'Defaults',
        'Brand',
        'Users',
        'Sales hierarchy',
        'Pipeline stages',
        'Fields layout',
        'Web forms',
        'Workflow automations',
        'Assignment rules',
        'SLA policies',
        'Enrichment',
        'Accounts',
        'Templates',
        'Telephony',
        'WhatsApp',
        'ERP',
        'Lead syncing',
      ]),
    )
    // Still registered for deep links / buttons, but hidden from snav.
    expect(sectionFromSlug('invite-user')?.nav).toBe(false)
    expect(sectionFromSlug('dashboard')?.nav).toBe(false)
  })

  it('hides non-Figma snav rows from visibleSettingsGroups', async () => {
    const { visibleSettingsGroups } = await import(
      '@/components/Settings/settingsSections'
    )
    const labels = visibleSettingsGroups().flatMap((group) =>
      group.items.map((item) => item.label),
    )
    expect(labels).not.toContain('Invite User')
    expect(labels).not.toContain('Dashboard')
    expect(labels).not.toContain('Astra Connect')
    expect(labels).toContain('Web forms')
  })

  it('keeps deep-link sections registered', () => {
    expect(
      settingsGroups.flatMap((g) => g.items.map((i) => i.label)),
    ).toEqual(
      expect.arrayContaining([
        'Invite User',
        'Dashboard',
        'Home Actions',
        'Astra Connect',
        'API & webhooks',
      ]),
    )
  })

  it('gates pipeline stages and fields layout', () => {
    expect(sectionFromSlug('pipeline-stages').condition).toBeTypeOf('function')
    expect(sectionFromSlug('fields-layout').condition).toBeTypeOf('function')
    expect(sectionFromSlug('profile').condition).toBeUndefined()
  })
})
