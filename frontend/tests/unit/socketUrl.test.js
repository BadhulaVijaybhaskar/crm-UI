import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('socket.io-client', () => ({
  io: vi.fn(() => ({ on: vi.fn() })),
}))
vi.mock('frappe-ui', () => ({
  getCachedListResource: vi.fn(),
  getCachedResource: vi.fn(),
}))

describe('getSocketioUrl', () => {
  beforeEach(() => {
    window.site_name = 'crm.localhost'
    delete window.socketio_port
  })

  afterEach(() => {
    vi.resetModules()
    delete window.socketio_port
    delete window.site_name
  })

  it('uses same-origin by default (no socketio_port)', async () => {
    const { getSocketioUrl } = await import('../../src/socket.js')
    const url = getSocketioUrl()
    expect(url).toBe(`${window.location.origin}/crm.localhost`)
    expect(url).not.toMatch(/:9000\b/)
  })

  it('honours configured socketio_port', async () => {
    window.socketio_port = 9000
    const { getSocketioUrl } = await import('../../src/socket.js')
    const url = getSocketioUrl()
    expect(url).toBe(
      `${window.location.protocol}//${window.location.hostname}:9000/crm.localhost`,
    )
  })
})
