/**
 * Pure helpers for Astra batch-1 UI. No invented metrics — format only.
 */

export function initialsFrom(name = '') {
  const parts = String(name)
    .trim()
    .split(/\s+/)
    .filter(Boolean)
  if (!parts.length) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

export function greetingFor(date = new Date()) {
  const hour = date.getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

export function formatShortDate(date = new Date(), locale) {
  try {
    return new Intl.DateTimeFormat(locale || undefined, {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    }).format(date)
  } catch {
    return String(date)
  }
}

export function formatTime(value) {
  if (!value) return ''
  const d = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  try {
    return new Intl.DateTimeFormat(undefined, {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(d)
  } catch {
    return String(value)
  }
}

/** Compact currency for KPI tiles (e.g. ₹3.2Cr). Returns empty string for null/NaN. */
export function formatCompactCurrency(amount, currency = 'INR') {
  const n = Number(amount)
  if (!Number.isFinite(n)) return ''
  const abs = Math.abs(n)
  const sign = n < 0 ? '-' : ''
  const symbol =
    currency === 'INR' || !currency
      ? '₹'
      : currency === 'USD'
        ? '$'
        : `${currency} `

  if (abs >= 1e7) return `${sign}${symbol}${(abs / 1e7).toFixed(1)}Cr`
  if (abs >= 1e5) return `${sign}${symbol}${(abs / 1e5).toFixed(1)}L`
  if (abs >= 1e3) return `${sign}${symbol}${(abs / 1e3).toFixed(1)}K`
  return `${sign}${symbol}${abs.toFixed(abs >= 100 ? 0 : 2)}`
}

export function formatDeltaPercent(delta) {
  const n = Number(delta)
  if (!Number.isFinite(n) || n === 0) return null
  const rounded = Math.round(n)
  return `${rounded > 0 ? '+' : ''}${rounded}%`
}

export function avatarTone(seed = '') {
  const tones = ['#1677ff', '#13b5a6', '#0e8bd6', '#64748b', '#d97706']
  let hash = 0
  const s = String(seed)
  for (let i = 0; i < s.length; i++) hash = (hash + s.charCodeAt(i) * (i + 1)) % 997
  return tones[hash % tones.length]
}

export function routeForReference(doctype, docname) {
  if (!doctype || !docname) return null
  if (doctype === 'CRM Lead') return { name: 'Lead', params: { leadId: docname } }
  if (doctype === 'CRM Deal') return { name: 'Deal', params: { dealId: docname } }
  if (doctype === 'Contact')
    return { name: 'Contact', params: { contactId: docname } }
  if (doctype === 'CRM Organization')
    return { name: 'Organization', params: { organizationId: docname } }
  return null
}
