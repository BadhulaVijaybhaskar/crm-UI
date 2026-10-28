/**
 * Format KPI values for tile display.
 */

export function formatKpiValue(value, format = 'number', currency = '₹') {
  const n = Number(value)
  if (!Number.isFinite(n)) return '—'

  if (format === 'percent') {
    return `${trimNum(n)}%`
  }

  if (format === 'currency' || format === 'currency_lakh') {
    const abs = Math.abs(n)
    if (abs >= 10_000_000) return `${currency}${trimNum(n / 10_000_000)} Cr`
    if (abs >= 100_000) return `${currency}${trimNum(n / 100_000)} L`
    if (abs >= 1_000) return `${currency}${trimNum(n / 1_000)}k`
    return `${currency}${trimNum(n)}`
  }

  if (Math.abs(n) >= 1000) return trimNum(n)
  return trimNum(n)
}

export function formatDelta(deltaPct) {
  if (deltaPct == null || !Number.isFinite(Number(deltaPct))) return null
  const n = Number(deltaPct)
  const sign = n > 0 ? '▲' : n < 0 ? '▼' : '•'
  return {
    text: `${sign} ${trimNum(Math.abs(n))}%`,
    direction: n > 0 ? 'up' : n < 0 ? 'down' : 'flat',
  }
}

function trimNum(n) {
  const rounded = Math.round(n * 10) / 10
  return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1)
}
