/**
 * Compact INR display for Home KPIs (e.g. ₹38.4 L, ₹2.1 Cr).
 * Falls back to Intl currency for other codes / small values.
 */
import { formatCurrency } from '@/utils/numberFormat.js'

export function formatCompactCurrency(
  value,
  currency = window.sysdefaults?.currency || 'INR',
) {
  const n = Number(value) || 0
  const code = currency || 'INR'
  if (code === 'INR' && Math.abs(n) >= 10000000) {
    return `₹${trimNum(n / 10000000)} Cr`
  }
  if (code === 'INR' && Math.abs(n) >= 100000) {
    return `₹${trimNum(n / 100000)} L`
  }
  if (code === 'INR' && Math.abs(n) >= 1000) {
    return `₹${trimNum(n / 1000)} K`
  }
  return formatCurrency(n, '', code, Math.abs(n) >= 100 ? 0 : 2)
}

function trimNum(n) {
  const rounded = Math.round(n * 10) / 10
  return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1)
}
