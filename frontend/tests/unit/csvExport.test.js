import { describe, expect, it } from 'vitest'
import {
  canUseCrmCsvExport,
  crmCsvExportUrl,
  crmCsvTemplateUrl,
} from '@/utils/csvExport'

describe('csvExport helpers', () => {
  it('allows CRM doctypes only', () => {
    expect(canUseCrmCsvExport('CRM Lead')).toBe(true)
    expect(canUseCrmCsvExport('Contact')).toBe(true)
    expect(canUseCrmCsvExport('ToDo')).toBe(false)
  })

  it('builds export and template urls', () => {
    const url = crmCsvExportUrl({
      doctype: 'CRM Lead',
      fields: ['email'],
      filters: { status: 'New' },
      title: 'Leads',
    })
    expect(url).toContain('/api/method/crm.api.csv_io.export_csv?')
    expect(url).toContain('doctype=CRM+Lead')
    expect(crmCsvTemplateUrl('Contact')).toContain(
      'crm.api.csv_io.download_template',
    )
  })
})
