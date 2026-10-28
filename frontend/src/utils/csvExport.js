/** Permission-aware, formula-safe CSV export via crm.api.csv_io. */

const EXPORTABLE = new Set([
  'CRM Lead',
  'Contact',
  'CRM Deal',
  'CRM Organization',
])

export function canUseCrmCsvExport(doctype) {
  return EXPORTABLE.has(doctype)
}

export function crmCsvExportUrl({
  doctype,
  fields,
  filters,
  orderBy,
  limit,
  title,
}) {
  const params = new URLSearchParams()
  params.set('doctype', doctype)
  if (fields) params.set('fields', JSON.stringify(fields))
  if (filters) params.set('filters', JSON.stringify(filters))
  if (orderBy) params.set('order_by', orderBy)
  if (limit) params.set('limit', String(limit))
  if (title) params.set('title', title)
  return `/api/method/crm.api.csv_io.export_csv?${params.toString()}`
}

export function crmCsvTemplateUrl(doctype) {
  const params = new URLSearchParams({ doctype })
  return `/api/method/crm.api.csv_io.download_template?${params.toString()}`
}
