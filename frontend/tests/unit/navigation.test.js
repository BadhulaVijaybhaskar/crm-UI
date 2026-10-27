import { getNavigationItems, navigationItems } from '@/utils/navigation'

describe('navigationItems', () => {
  it('keeps the Astra CRM sidebar order', () => {
    const labels = navigationItems.map((item) => item.label)
    expect(labels).toEqual([
      'Dashboard',
      'Leads',
      'Contacts',
      'Companies',
      'Deals',
      'Tasks',
      'AI Calling',
      'Messages',
      'AI Employees',
      'Activities',
      'Reports',
      'Settings',
    ])
  })

  it('does not surface WhatsApp inbox in the sidebar registry', () => {
    const labels = navigationItems.map((item) => item.label.toLowerCase())
    expect(labels.some((l) => l.includes('whatsapp'))).toBe(false)
    expect(labels.some((l) => l === 'inbox')).toBe(false)
  })

  it('marks Connect destinations as placeholders', () => {
    const connect = navigationItems.filter((item) => item.connect)
    expect(connect.map((item) => item.connect)).toEqual([
      'calls',
      'messages',
      'employees',
    ])
    expect(connect.every((item) => item.placeholder)).toBe(true)
  })

  it('uses unique keys for in-app routes and connect links', () => {
    const keys = navigationItems.map(
      (item) => item.route || item.connect || item.action,
    )
    expect(new Set(keys).size).toBe(keys.length)
  })

  it('omits desktop-only destinations on mobile', () => {
    const mobileLabels = getNavigationItems({ mobile: true }).map(
      (item) => item.label,
    )
    expect(mobileLabels).not.toContain('Dashboard')
    expect(mobileLabels).toContain('Leads')
    expect(mobileLabels).toContain('Companies')
  })
})
