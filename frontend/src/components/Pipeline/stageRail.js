import { stageToken } from '@/components/astra/format'

const CLOSE_TYPES = new Set(['Won', 'Lost'])

export function stageMarkerColor(name) {
  const token = stageToken(name)
  if (token === 'success') return 'var(--crm-success)'
  if (token === 'danger') return 'var(--crm-danger)'
  return `var(--crm-${token})`
}

export function pipelineStages(rows, allowed) {
  const list = Array.isArray(rows) ? rows : []
  const names = Array.isArray(allowed) ? allowed.filter(Boolean) : []
  const filtered = names.length
    ? list.filter((row) => names.includes(row.name))
    : list
  return filtered
    .filter((row) => row && row.name)
    .map((row) => ({
      name: row.name,
      label: row.label || row.name,
      type: row.type || '',
    }))
}

export function stageState(stage, index, currentIndex) {
  const current = index === currentIndex
  if (current && stage?.type === 'Won') return 'won'
  if (current && stage?.type === 'Lost') return 'lost'
  if (current) return 'current'
  if (currentIndex >= 0 && index < currentIndex) return 'done'
  return 'todo'
}

export function isCloseStage(stage) {
  return CLOSE_TYPES.has(stage?.type)
}

export function stageEnteredOn(rows) {
  const dates = {}
  for (const row of rows || []) {
    if (!row) continue
    if (row.to && (row.to_date || row.from_date)) {
      dates[row.to] = row.to_date || row.from_date
    }
    if (!row.to && row.from && row.from_date && !dates[row.from]) {
      dates[row.from] = row.from_date
    }
  }
  return dates
}

export function openStageStart(rows, stageName) {
  if (!stageName) return ''
  const open = [...(rows || [])]
    .reverse()
    .find((row) => row && !row.to && row.from === stageName)
  return open?.from_date || ''
}

export function daysSince(iso, now = Date.now()) {
  if (!iso) return null
  const start = new Date(iso).getTime()
  if (Number.isNaN(start)) return null
  return Math.max(0, Math.floor((now - start) / 86400000))
}
