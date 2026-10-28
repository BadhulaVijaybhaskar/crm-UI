import { describe, expect, it } from 'vitest'
import router from '@/router'

describe('Astra activity routes', () => {
  it('exposes Work Queue and Conversations for the shell nav', () => {
    const names = router.getRoutes().map((r) => r.name)
    expect(names).toContain('Work Queue')
    expect(names).toContain('Conversations')
    expect(names).toContain('Dashboard')
    expect(names).toContain('Tasks')
    expect(names).toContain('Notes')
    expect(names).toContain('Call Logs')
  })

  it('uses stable paths the shell agent can link', () => {
    const byName = Object.fromEntries(
      router.getRoutes().map((r) => [r.name, r.path]),
    )
    expect(byName['Work Queue']).toBe('/work-queue')
    expect(byName.Conversations).toBe('/conversations')
    expect(byName.Dashboard).toBe('/dashboard')
  })
})
