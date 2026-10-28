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
    delete window.astra_socketio_direct
  })

  afterEach(() => {
    vi.resetModules()
    delete window.socketio_port
    delete window.astra_socketio_direct
    delete window.site_name
  })

  it('uses same-origin by default even if socketio_port is set', async () => {
    // common_site_config always has socketio_port=9000; without the opt-in
    // flag we must still use same-origin /socket.io (nginx proxy).
    window.socketio_port = 9000
    const { getSocketioUrl } = await import('../../src/socket.js')
    const url = getSocketioUrl()
    expect(url).toBe(`${window.location.origin}/crm.localhost`)
    expect(url).not.toMatch(/:9000\b/)
  })

  it('honours socketio_port only with astra_socketio_direct opt-in', async () => {
    window.socketio_port = 9000
    window.astra_socketio_direct = 1
    const { getSocketioUrl } = await import('../../src/socket.js')
    const url = getSocketioUrl()
    expect(url).toBe(
      `${window.location.protocol}//${window.location.hostname}:9000/crm.localhost`,
    )
  })
})
