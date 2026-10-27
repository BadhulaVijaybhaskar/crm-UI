import { describe, expect, it } from 'vitest'

/**
 * Mirrors UserDropdown.visibleApps rules so the policy is unit-tested
 * without mounting Vue (same branch as the component).
 */
function visibleApps(data, { isAdmin }) {
  if (!isAdmin) return []
  return [
    {
      name: 'frappe',
      title: 'Admin',
      route: '/desk',
    },
    ...(data || [])
      .filter((app) => app.name !== 'crm')
      .map((app) => ({
        name: app.name,
        title: app.title,
        route: app.route,
      })),
  ]
}

describe('app switcher visibility', () => {
  const siblingApps = [
    { name: 'crm', title: 'Astra CRM', route: '/crm' },
    { name: 'whatsapp', title: 'WhatsApp', route: '/whatsapp' },
  ]

  it('hides Desk and other apps for non-admins', () => {
    expect(visibleApps(siblingApps, { isAdmin: false })).toEqual([])
  })

  it('shows Desk as Admin for admins, excluding crm itself', () => {
    const apps = visibleApps(siblingApps, { isAdmin: true })
    expect(apps.map((a) => a.name)).toEqual(['frappe', 'whatsapp'])
    expect(apps[0].title).toBe('Admin')
  })
})
