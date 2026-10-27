import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ASTRA_CONNECT_DEFAULT_URL,
  getAstraConnectBaseUrl,
  getAstraConnectUrl,
  openAstraConnect,
} from '@/utils/astraConnect'

describe('astraConnect', () => {
  afterEach(() => {
    delete window.astra_connect_url
    delete window.boot
    vi.restoreAllMocks()
  })

  it('defaults to the production Connect base URL', () => {
    expect(getAstraConnectBaseUrl()).toBe(ASTRA_CONNECT_DEFAULT_URL)
  })

  it('reads astra_connect_url from site boot', () => {
    window.astra_connect_url = 'https://connect.example.test/'
    expect(getAstraConnectBaseUrl()).toBe('https://connect.example.test')
    expect(getAstraConnectUrl('calls')).toBe(
      'https://connect.example.test/calls',
    )
  })

  it('opens Connect paths in a new tab (SSO placeholder)', () => {
    const open = vi.spyOn(window, 'open').mockReturnValue(null)
    openAstraConnect('messages')
    expect(open).toHaveBeenCalledWith(
      `${ASTRA_CONNECT_DEFAULT_URL}/messages`,
      '_blank',
      'noopener,noreferrer',
    )
  })
})
