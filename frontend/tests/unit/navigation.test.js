import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  getNavigationItems,
  isNavItemAvailable,
  navigationItems,
} from '@/utils/navigation'

vi.mock('@/router', () => {
  const routes = new Set([
    'Dashboard',
    'Activities',
    'Conversations',
    'Leads',
    'Deals',
    'Contacts',
    'Organizations',
    'Tasks',
    'Notes',
    'Call Logs',
    'Reports',
  ])
  return {
    default: {
      hasRoute: (name) => routes.has(name),
    },
  }
})

describe('navigationItems', () => {
  afterEach(() => {
    delete window.astra_connect_enabled
    delete window.astra_connect_url
    delete window.boot
  })

  it('keeps the Astra CRM sidebar registry order (SHELL_SPEC / Figma v1)', () => {
    const labels = navigationItems.map((item) => item.label)
    expect(labels).toEqual([
      'Home',
      'Work queue',
      'Conversations',
      'Leads',
      'Deals',
      'Contacts',
      'Companies',
      'Tasks',
      'Notes',
      'Call logs',
      'Reports',
      'AI Calling',
      'Messages',
      'AI Employees',
      'Settings',
    ])
  })

  it('points Home at the Dashboard route', () => {
    const home = navigationItems.find((item) => item.label === 'Home')
    expect(home.route).toBe('Dashboard')
  })

  it('does not hard-code Figma example counts', () => {
    for (const item of navigationItems) {
      expect(item.count, `${item.label} must not ship a static count`).toBeUndefined()
    }
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

  it('shows Work queue and Conversations when their routes exist', () => {
    const labels = getNavigationItems().map((item) => item.label)
    expect(labels).toContain('Work queue')
    expect(labels).toContain('Conversations')
    expect(labels).toContain('Home')
    expect(labels).toContain('Notes')
    expect(labels).toContain('Call logs')
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

  it('includes Home on mobile (settings drawer + mobile menu)', () => {
    const mobileLabels = getNavigationItems({ mobile: true }).map(
      (item) => item.label,
    )
    expect(mobileLabels).toContain('Home')
    expect(mobileLabels).toContain('Leads')
    expect(mobileLabels).toContain('Companies')
    expect(mobileLabels).toContain('Settings')
  })

  it('rejects placeholder and not-ready items via isNavItemAvailable', () => {
    expect(isNavItemAvailable({ label: 'X', placeholder: true })).toBe(false)
    expect(isNavItemAvailable({ label: 'X', ready: false, route: 'Leads' })).toBe(
      false,
    )
    expect(isNavItemAvailable({ label: 'Leads', route: 'Leads' })).toBe(true)
    expect(
      isNavItemAvailable({ label: 'Missing', route: 'DoesNotExist' }),
    ).toBe(false)
  })

  it('uses icon components (no unicode glyph icons)', () => {
    for (const item of navigationItems) {
      expect(item.icon, `${item.label} needs an icon`).toBeTruthy()
      expect(typeof item.icon).not.toBe('string')
    }
  })
})
