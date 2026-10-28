import { describe, expect, it } from 'vitest'
import {
  formatDurationSeconds,
  normalizeStageHistory,
} from '../../src/utils/stageHistory'

describe('stageHistory helpers (CRM-07)', () => {
  it('formats duration seconds', () => {
    expect(formatDurationSeconds(0)).toBe('')
    expect(formatDurationSeconds(90)).toBe('1m')
    expect(formatDurationSeconds(3661)).toBe('1h 1m')
  })

  it('normalizes status_change_log rows newest first', () => {
    const rows = [
      {
        from: 'New',
        to: 'Contacted',
        log_owner: 'sales@example.com',
        from_date: '2026-01-01 10:00:00',
        to_date: '2026-01-01 11:00:00',
        duration: 3600,
      },
      {
        from: 'Contacted',
        to: '',
        log_owner: 'sales@example.com',
        from_date: '2026-01-01 11:00:00',
        to_date: '',
        duration: 0,
      },
    ]
    const out = normalizeStageHistory(rows)
    expect(out[0].open).toBe(true)
    expect(out[0].from).toBe('Contacted')
    expect(out[1].from).toBe('New')
    expect(out[1].to).toBe('Contacted')
    expect(out[1].duration).toBe('1h')
    expect(out[1].by).toBe('sales@example.com')
  })
})
