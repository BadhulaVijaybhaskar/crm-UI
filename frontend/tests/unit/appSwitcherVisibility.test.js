import { describe, expect, it } from 'vitest'

/**
 * Mirrors UserDropdown.visibleApps rules so the policy is unit-tested
 * without mounting Vue (same branch as the component).
 */
const VENDOR_APP_NAMES = new Set([
  'frappe',
  'erpnext',
  'insights',
  'hrms',
  'lms',
  'wiki',
  'builder',
  'helpdesk',
  'telephony',
])

function visibleApps(data, { isAdmin }) {
  if (!isAdmin) return []
  return [
    {
      name: 'admin',
      title: 'Admin',
      route: '/desk',
      logo: 'astra-mark',
    },
    ...(data || [])
      .filter((app) => app.name !== 'crm' && !VENDOR_APP_NAMES.has(app.name))
      .filter((app) => {
        const blob = `${app.name || ''} ${app.title || ''} ${app.logo || ''}`
        return !/frappe|erpnext|framework\.png/i.test(blob)
      })
      .map((app) => ({
        name: app.name,
        title: app.title,
        route: app.route,
        logo: 'astra-mark',
      })),
  ]
}

describe('app switcher visibility', () => {
  const siblingApps = [
    { name: 'crm', title: 'Astra CRM', route: '/crm' },
    { name: 'whatsapp', title: 'WhatsApp', route: '/whatsapp' },
    {
      name: 'erpnext',
      title: 'ERPNext',
      route: '/app/erpnext',
      logo: '/assets/frappe/images/framework.png',
    },
  ]

  it('hides Desk and other apps for non-admins', () => {
    expect(visibleApps(siblingApps, { isAdmin: false })).toEqual([])
  })

  it('shows Admin with Astra mark and filters vendor apps', () => {
    const apps = visibleApps(siblingApps, { isAdmin: true })
    expect(apps.map((a) => a.name)).toEqual(['admin', 'whatsapp'])
    expect(apps[0].title).toBe('Admin')
    expect(apps[0].logo).toBe('astra-mark')
    expect(apps.every((a) => a.logo !== '/assets/frappe/images/framework.png')).toBe(
      true,
    )
  })
})
