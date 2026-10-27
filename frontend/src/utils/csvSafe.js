/** Mirror of crm.utils.csv_safe — keep in sync for client-side previews/tests. */

const FORMULA_PREFIX = /^[=+\-@]/

export function guardCsvCell(value) {
  if (value === null || value === undefined) return ''
  let text
  if (typeof value === 'boolean') text = value ? '1' : '0'
  else text = String(value)
  text = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  if (FORMULA_PREFIX.test(text)) return "'" + text
  return text
}

export function companyDomainFromWebsite(website) {
  if (!website) return ''
  let raw = String(website).trim().toLowerCase()
  if (!raw) return ''
  if (raw.includes('@') && !raw.includes('://') && !raw.startsWith('www.')) {
    return raw.split('@').pop()
  }
  if (!raw.includes('://')) raw = 'https://' + raw
  try {
    const host = new URL(raw).hostname || ''
    return host.replace(/^www\./, '')
  } catch {
    return ''
  }
}
