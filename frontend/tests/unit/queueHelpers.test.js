import { describe, expect, it } from 'vitest'
import {
  buildOwnerScope,
  buildTaskAssigneeScope,
  isTaskOverdue,
  queueCallAction,
  taskDueReason,
} from '@/components/astra/workqueue/queueHelpers'

describe('taskDueReason / isTaskOverdue', () => {
  it('says No due date when due_date is missing', () => {
    expect(taskDueReason(null, { todayDate: '2026-10-27' })).toBe(
      'No due date',
    )
    expect(taskDueReason('', { todayDate: '2026-10-27' })).toBe('No due date')
    expect(taskDueReason(undefined, { dayStart: '2026-10-27 00:00:00' })).toBe(
      'No due date',
    )
  })

  it('labels overdue vs due today using day start, not date-only compare', () => {
    expect(
      taskDueReason('2026-10-26 18:00:00', {
        dayStart: '2026-10-27 00:00:00',
        todayDate: '2026-10-27',
      }),
    ).toBe('Missed deadline')
    expect(
      taskDueReason('2026-10-27 18:00:00', {
        dayStart: '2026-10-27 00:00:00',
        todayDate: '2026-10-27',
      }),
    ).toBe('Due today')
    expect(isTaskOverdue('2026-10-27 18:00:00', '2026-10-27 00:00:00')).toBe(
      false,
    )
    expect(isTaskOverdue('2026-10-26 23:00:00', '2026-10-27 00:00:00')).toBe(
      true,
    )
  })
})

describe('buildOwnerScope / buildTaskAssigneeScope', () => {
  it('does not scope managers', () => {
    expect(
      buildOwnerScope({
        isManager: true,
        user: 'sales@example.com',
        doctype: 'CRM Lead',
        ownerField: 'lead_owner',
      }),
    ).toEqual({ filters: {} })
    expect(
      buildTaskAssigneeScope({ isManager: true, user: 'sales@example.com' }),
    ).toEqual({ filters: {} })
  })

  it('scopes non-managers to owner/_assign orFilters', () => {
    const scope = buildOwnerScope({
      isManager: false,
      user: 'rep@example.com',
      doctype: 'CRM Deal',
      ownerField: 'deal_owner',
    })
    expect(scope.filters).toEqual({})
    expect(scope.orFilters).toEqual([
      ['CRM Deal', 'deal_owner', '=', 'rep@example.com'],
      ['CRM Deal', '_assign', 'like', '%rep@example.com%'],
    ])

    const tasks = buildTaskAssigneeScope({
      isManager: false,
      user: 'rep@example.com',
    })
    expect(tasks.orFilters[0]).toEqual([
      'CRM Task',
      'assigned_to',
      '=',
      'rep@example.com',
    ])
  })
})

describe('queueCallAction', () => {
  it('only returns call when phone and telephony are enabled', () => {
    expect(queueCallAction({ phone: '999', telephonyEnabled: true })).toBe(
      'call',
    )
    expect(queueCallAction({ phone: '999', telephonyEnabled: false })).toBe(
      'open',
    )
    expect(queueCallAction({ phone: null, telephonyEnabled: true })).toBe(
      'open',
    )
  })
})
