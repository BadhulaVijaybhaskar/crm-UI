import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ASTRA_CONNECT_DEFAULT_URL,
  getAstraConnectBaseUrl,
  getAstraConnectUrl,
  isAstraConnectConfigured,
  openAstraConnect,
} from '@/utils/astraConnect'

describe('astraConnect', () => {
  afterEach(() => {
    delete window.astra_connect_url
    delete window.astra_connect_enabled
    delete window.boot
    vi.restoreAllMocks()
  })

  it('is not configured without enabled Settings + base URL', () => {
    expect(isAstraConnectConfigured()).toBe(false)
    window.astra_connect_url = 'https://connect.example.test'
    expect(isAstraConnectConfigured()).toBe(false)
    window.astra_connect_enabled = true
    expect(isAstraConnectConfigured()).toBe(true)
  })

  it('defaults getAstraConnectBaseUrl when boot has no URL', () => {
    expect(getAstraConnectBaseUrl()).toBe(ASTRA_CONNECT_DEFAULT_URL)
  })

  it('reads astra_connect_url from site boot', () => {
    window.astra_connect_url = 'https://connect.example.test/'
    expect(getAstraConnectBaseUrl()).toBe('https://connect.example.test')
    expect(getAstraConnectUrl('calls')).toBe(
      'https://connect.example.test/calls',
    )
  })

  it('opens Connect paths only when configured', () => {
    const open = vi.spyOn(window, 'open').mockReturnValue(null)
    expect(openAstraConnect('messages')).toBeNull()
    expect(open).not.toHaveBeenCalled()

    window.astra_connect_enabled = true
    window.astra_connect_url = 'https://connect.example.test'
    openAstraConnect('messages')
    expect(open).toHaveBeenCalledWith(
      'https://connect.example.test/messages',
      '_blank',
      'noopener,noreferrer',
    )
  })
})
