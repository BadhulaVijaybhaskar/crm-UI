/**
 * Format CRM Status Change Log rows for the record Stage history panel.
 * Reuses the existing child table (from, to, log_owner, from_date, to_date, duration).
 */

export function formatDurationSeconds(seconds) {
  const s = Number(seconds) || 0
  if (s <= 0) return ''
  const days = Math.floor(s / 86400)
  const hours = Math.floor((s % 86400) / 3600)
  const mins = Math.floor((s % 3600) / 60)
  const parts = []
  if (days) parts.push(`${days}d`)
  if (hours) parts.push(`${hours}h`)
  if (mins || !parts.length) parts.push(`${mins}m`)
  return parts.join(' ')
}

export function normalizeStageHistory(rows = []) {
  return (rows || [])
    .filter((row) => row && (row.from || row.to))
    .map((row) => ({
      from: row.from || '',
      to: row.to || '',
      by: row.log_owner || row.owner || '',
      at: row.to_date || row.from_date || '',
      duration: formatDurationSeconds(row.duration),
      open: !row.to,
    }))
    .sort((a, b) => {
      // Open (current) stage first, then newest closed moves
      if (a.open !== b.open) return a.open ? -1 : 1
      const ta = a.at ? new Date(a.at).getTime() : 0
      const tb = b.at ? new Date(b.at).getTime() : 0
      return tb - ta
    })
}
