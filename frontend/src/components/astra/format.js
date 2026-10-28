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
