import { describe, expect, it } from 'vitest'
import {
  getNavigationItems,
  NAV_FEATURE_READY,
  navigationItems,
  navItemKey,
  resolveActiveNavKey,
} from '@/utils/navigation'
import { isExclusiveActive } from '@/utils/navActive'
import router from '@/router'

const ASTRA_ROUTES = ['Activities', 'Work Queue', 'Conversations']

describe('Astra nav routes and exclusive active state', () => {
  it('registers Work Queue and Conversations routes that resolve', () => {
    expect(NAV_FEATURE_READY.WorkQueue).toBe(true)
    expect(NAV_FEATURE_READY.Conversations).toBe(true)
    expect(router.hasRoute('Activities')).toBe(true)
    expect(router.hasRoute('Work Queue')).toBe(true)
    expect(router.hasRoute('Conversations')).toBe(true)

    for (const routeName of ASTRA_ROUTES) {
      const item = navigationItems.find((i) => i.route === routeName)
      expect(item, `${routeName} missing from navigationItems`).toBeTruthy()
      expect(router.resolve({ name: routeName }).name).toBe(routeName)
    }
  })

  it('gives each Astra page a unique nav key that matches only its route', () => {
    const items = getNavigationItems()
    const keys = items.map(navItemKey)
    expect(new Set(keys).size).toBe(keys.length)

    for (const routeName of ASTRA_ROUTES) {
      const active = resolveActiveNavKey({ name: routeName }, items)
      expect(active).toBe(routeName)
      expect(isExclusiveActive(active, ASTRA_ROUTES)).toBe(true)
      for (const other of ASTRA_ROUTES) {
        if (other === routeName) continue
        expect(active).not.toBe(other)
      }
    }
  })

  it('does not co-highlight Astra pages with each other or Leads', () => {
    const items = getNavigationItems()
    const activities = resolveActiveNavKey({ name: 'Activities' }, items)
    const workQueue = resolveActiveNavKey({ name: 'Work Queue' }, items)
    const conversations = resolveActiveNavKey({ name: 'Conversations' }, items)
    const leads = resolveActiveNavKey({ name: 'Leads' }, items)

    expect(new Set([activities, workQueue, conversations, leads]).size).toBe(4)
    expect(activities).toBe('Activities')
    expect(workQueue).toBe('Work Queue')
    expect(conversations).toBe('Conversations')
    expect(leads).toBe('Leads')
  })
})
