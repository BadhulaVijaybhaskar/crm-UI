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
    expect(sectionFromSlug('pipeline-stages')?.label).toBe('Pipeline Stages')
    expect(sectionFromSlug('fields-layout')?.label).toBe('Fields Layout')
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
        'Dashboard',
        'Defaults',
        'Brand',
        'Home Actions',
        'Users',
        'Invite User',
        'Sales Hierarchy',
        'Pipeline Stages',
        'Fields Layout',
        'Workflow Automations',
        'Assignment Rules',
        'SLA Policies',
        'Forms',
        'Enrichment',
        'Accounts',
        'Templates',
        'Astra Connect',
        'API & webhooks',
        'Telephony',
        'WhatsApp',
        'ERP',
        'Lead Syncing',
      ]),
    )
  })

  it('gates pipeline stages and fields layout', () => {
    expect(sectionFromSlug('pipeline-stages').condition).toBeTypeOf('function')
    expect(sectionFromSlug('fields-layout').condition).toBeTypeOf('function')
    expect(sectionFromSlug('profile').condition).toBeUndefined()
  })
})
