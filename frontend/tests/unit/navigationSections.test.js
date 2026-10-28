import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  getFooterNavItems,
  getNavigationSections,
} from '@/utils/navigation'

vi.mock('@/router', () => {
  const routes = new Set([
    'Dashboard',
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

describe('navigation sections', () => {
  afterEach(() => {
    delete window.astra_connect_enabled
    delete window.astra_connect_url
  })

  it('groups main / records / activity / insights for the shell', () => {
    const sections = getNavigationSections()
    const ids = sections.map((s) => s.id)
    expect(ids).toEqual(
      expect.arrayContaining(['main', 'records', 'activity', 'insights']),
    )
    const main = sections.find((s) => s.id === 'main')
    expect(main.views.map((v) => v.label)).toEqual(['Home'])
    const records = sections.find((s) => s.id === 'records')
    expect(records.views.map((v) => v.label)).toEqual([
      'Leads',
      'Deals',
      'Contacts',
      'Companies',
    ])
    const activity = sections.find((s) => s.id === 'activity')
    expect(activity.views.map((v) => v.label)).toEqual([
      'Tasks',
      'Notes',
      'Call logs',
    ])
  })

  it('pins Settings in the footer, not the scrolling list', () => {
    expect(getFooterNavItems().map((i) => i.label)).toEqual(['Settings'])
    expect(
      getNavigationSections()
        .flatMap((s) => s.views)
        .some((v) => v.label === 'Settings'),
    ).toBe(false)
  })

  it('shows Astra Connect section only when configured', () => {
    expect(getNavigationSections().some((s) => s.id === 'connect')).toBe(false)
    window.astra_connect_enabled = true
    window.astra_connect_url = 'https://connect.example.test'
    const connect = getNavigationSections().find((s) => s.id === 'connect')
    expect(connect.views.map((v) => v.label)).toEqual([
      'AI Calling',
      'Messages',
      'AI Employees',
    ])
  })
})
