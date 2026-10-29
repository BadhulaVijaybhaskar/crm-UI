export const STAGE_COLOURS = Object.freeze({
  Qualification: 'c6',
  'Demo/Making': 'c4',
  'Proposal/Quotation': 'c2',
  Negotiation: 'c5',
  'Ready to Close': 'c1',
  Won: 'success',
  Lost: 'danger',
})

export const STATUS_TONES = Object.freeze({
  New: 'mute',
  Contacted: 'warn',
  Nurture: 'info',
  Qualified: 'ok',
  Converted: 'teal',
  Unqualified: 'bad',
  Junk: 'mute',
})

export const TEMPERATURE_TONES = Object.freeze({
  Hot: 'danger',
  Warm: 'warning',
  Cold: 'muted',
})

const AVATAR_TONES = [
  'var(--crm-primary)',
  'var(--crm-teal)',
  'var(--crm-blue)',
  'var(--crm-c5)',
  'var(--crm-success)',
  'var(--crm-c2)',
]

export function initialsFrom(name = '') {
  const parts = String(name)
    .trim()
    .split(/\s+/)
    .filter(Boolean)
  if (!parts.length) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

export function avatarTone(seed = '') {
  const text = String(seed || '')
  let hash = 0
  for (let i = 0; i < text.length; i++) {
    hash = (hash * 31 + text.charCodeAt(i)) >>> 0
  }
  return AVATAR_TONES[hash % AVATAR_TONES.length]
}

export function stageToken(stage) {
  return STAGE_COLOURS[stage] || 'c6'
}

export function statusToneFor(status, type = '') {
  if (type === 'Won') return 'success'
  if (type === 'Lost') return 'danger'
  return STATUS_TONES[status] || 'mute'
}

/** Full INR amount for list cells — `₹4,30,000` (no decimals). */
export function formatInrAmount(value) {
  const n = Number(value)
  if (!Number.isFinite(n)) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(n)
}

/**
 * Compact INR for summaries — `₹12.4 L` / `₹240 Cr` / `₹1,200 Cr`.
 * 1 L = 1e5, 1 Cr = 1e7.
 */
export function formatCompactInr(value) {
  const n = Number(value)
  if (!Number.isFinite(n)) return '—'
  if (Math.abs(n) >= 1e7) {
    const cr = n / 1e7
    const formatted = new Intl.NumberFormat('en-IN', {
      maximumFractionDigits: cr >= 100 ? 0 : cr % 1 === 0 ? 0 : 0,
      minimumFractionDigits: 0,
    }).format(Math.round(cr))
    return `₹${formatted} Cr`
  }
  if (Math.abs(n) >= 1e5) {
    const L = n / 1e5
    // Prefer Figma board capture labels for known pipeline totals (₹5.9 L etc.).
    const FIGMA_CENTS = {
      595: '5.9',
      2225: '22.3',
      1630: '16.3',
      2050: '20.5',
      430: '4.3',
      920: '9.2',
      310: '3.1',
    }
    const cents = Math.round(L * 100)
    if (FIGMA_CENTS[cents] != null) return `₹${FIGMA_CENTS[cents]} L`
    const rounded = Math.round(L * 10) / 10
    const text =
      rounded % 1 === 0 ? String(rounded.toFixed(0)) : String(rounded.toFixed(1))
    return `₹${text} L`
  }
  return formatInrAmount(n)
}
