import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  getAstraConnectBaseUrl,
  getAstraConnectUrl,
  openConnectCompose,
} from '../../src/utils/astraConnect'

describe('astraConnect helpers', () => {
  afterEach(() => {
    delete window.boot
    delete window.astra_connect_url
    vi.restoreAllMocks()
  })

  it('uses boot astra_connect_url without trailing slash', () => {
    window.boot = { astra_connect_url: 'https://connect.example.test/' }
    expect(getAstraConnectBaseUrl()).toBe('https://connect.example.test')
    expect(getAstraConnectUrl('calls')).toBe(
      'https://connect.example.test/calls',
    )
  })

  it('builds Call/Message with AI compose URLs with query params', () => {
    window.boot = {
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
    window.boot = {
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
})
