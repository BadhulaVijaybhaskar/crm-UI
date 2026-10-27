import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ASTRA_CONNECT_DEFAULT_URL,
  getAstraConnectBaseUrl,
  getAstraConnectUrl,
  isAstraConnectConfigured,
  openAstraConnect,
  openConnectCompose,
} from '@/utils/astraConnect'

describe('astraConnect helpers', () => {
  afterEach(() => {
    delete window.astra_connect_url
    delete window.astra_connect_enabled
    delete window.boot
    delete window.site_name
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

  it('builds Call/Message with AI compose URLs with query params', () => {
    window.astra_connect_enabled = true
    window.astra_connect_url = 'https://connect.example.test'
    window.boot = {
      astra_connect_enabled: true,
      astra_connect_url: 'https://connect.example.test',
      site_name: 'crm.example.test',
    }
    const open = vi.spyOn(window, 'open').mockImplementation(() => null)
    const url = openConnectCompose('calls', {
      recordType: 'CRM Lead',
      recordId: 'CRM-LEAD-0001',
      phone: '+14155550100',
    })
    expect(url).toContain('https://connect.example.test/calls/new?')
    expect(url).toContain('crm_site=crm.example.test')
    expect(url).toContain('record_type=CRM+Lead')
    expect(url).toContain('record_id=CRM-LEAD-0001')
    expect(url).toContain('phone=%2B14155550100')
    expect(open).toHaveBeenCalledWith(
      url,
      '_blank',
      'noopener,noreferrer',
    )
  })

  it('does not embed secrets in compose URLs', () => {
    window.astra_connect_enabled = true
    window.astra_connect_url = 'https://connect.example.test'
    window.boot = {
      astra_connect_enabled: true,
      astra_connect_url: 'https://connect.example.test',
      site_name: 'crm.example.test',
      astra_connect_webhook_secret: 'should-never-appear',
    }
    const open = vi.spyOn(window, 'open').mockImplementation(() => null)
    const url = openConnectCompose('messages', {
      recordType: 'Contact',
      recordId: 'CONT-1',
    })
    expect(url).not.toMatch(/secret|token|password|hmac/i)
    expect(url).toContain('/messages/new?')
    expect(open).toHaveBeenCalled()
  })

  it('skips compose when Connect is not configured', () => {
    const open = vi.spyOn(window, 'open').mockImplementation(() => null)
    expect(
      openConnectCompose('calls', {
        recordType: 'CRM Lead',
        recordId: 'X',
      }),
    ).toBeNull()
    expect(open).not.toHaveBeenCalled()
  })
})
