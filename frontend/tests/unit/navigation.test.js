import { afterEach, describe, expect, it } from 'vitest'
import {
  getNavigationItems,
  isNavItemAvailable,
  NAV_FEATURE_READY,
  navigationItems,
} from '@/utils/navigation'

describe('navigationItems', () => {
  afterEach(() => {
    delete window.astra_connect_enabled
    delete window.astra_connect_url
    delete window.boot
  })

  it('keeps the Astra CRM sidebar registry order', () => {
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

  it('fails if any nav item is a placeholder / Soon stub', () => {
    for (const item of navigationItems) {
      expect(item.placeholder, `${item.label} must not be a placeholder`).toBeFalsy()
      expect(String(item.label)).not.toMatch(/soon|placeholder/i)
    }
    for (const item of getNavigationItems()) {
      expect(item.placeholder, `${item.label} surfaced as placeholder`).toBeFalsy()
    }
  })

  it('shows Activities and Reports when ready', () => {
    expect(NAV_FEATURE_READY.Activities).toBe(true)
    expect(NAV_FEATURE_READY.Reports).toBe(true)
    const labels = getNavigationItems().map((item) => item.label)
    expect(labels).toContain('Activities')
    expect(labels).toContain('Reports')
  })

  it('hides Connect destinations until Settings is enabled with a base URL', () => {
    expect(
      getNavigationItems()
        .filter((item) => item.connect)
        .map((item) => item.connect),
    ).toEqual([])

    window.astra_connect_enabled = true
    window.astra_connect_url = 'https://connect.example.test'
    expect(
      getNavigationItems()
        .filter((item) => item.connect)
        .map((item) => item.connect),
    ).toEqual(['calls', 'messages', 'employees'])
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

  it('rejects placeholder and not-ready items via isNavItemAvailable', () => {
    expect(isNavItemAvailable({ label: 'X', placeholder: true })).toBe(false)
    expect(isNavItemAvailable({ label: 'X', ready: false, route: 'Leads' })).toBe(
      false,
    )
    expect(isNavItemAvailable({ label: 'Leads', route: 'Leads' })).toBe(true)
  })
})
