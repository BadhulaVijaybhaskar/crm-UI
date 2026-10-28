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
  return STATUS_TONES[status] || 'primary'
}

export function stageSegments(statuses = [], currentName = '') {
  const rows = (statuses || []).filter((status) => status?.name)
  const currentIndex = rows.findIndex((status) => status.name === currentName)
  return rows.map((status, index) => {
    const type = status.type || ''
    let bar = 'bg-crm-neutral-soft'
    if (type === 'Won') bar = 'bg-crm-success'
    else if (type === 'Lost') {
      bar = index === currentIndex ? 'bg-crm-danger' : 'bg-crm-border-strong'
    } else if (currentIndex >= 0 && index < currentIndex) bar = 'bg-crm-primary'
    else if (index === currentIndex) bar = 'bg-crm-primary shadow-crm-selected'
    return {
      name: status.name,
      current: index === currentIndex,
      bar,
      type,
    }
  })
}

export function pipelineSegments(allStatuses = [], currentName = '', allowedNames = []) {
  const allowed = new Set(allowedNames || [])
  const rows = (allStatuses || []).filter(
    (status) => status?.name && (!allowed.size || allowed.has(status.name)),
  )
  const current = rows.find((status) => status.name === currentName)
  const closed = current?.type === 'Won' || current?.type === 'Lost'
  const open = rows.filter((status) => status.type !== 'Won' && status.type !== 'Lost')
  const source = open.length ? open : rows
  const segments = stageSegments(source, closed ? '' : currentName)
  if (!closed) return segments
  return segments.map((segment) => ({
    ...segment,
    current: false,
    bar: current.type === 'Lost' ? 'bg-crm-border-strong' : 'bg-crm-primary',
  }))
}
