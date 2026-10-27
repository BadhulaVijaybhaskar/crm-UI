/**
 * Pure Work queue helpers — due labels, owner scope, call-action gating.
 */

/**
 * Reason line for a task in the queue / My day list.
 * Never labels a missing due date as "Due today".
 */
export function taskDueReason(dueDate, { dayStart, todayDate } = {}) {
  if (dueDate == null || dueDate === '') return 'No due date'
  const due = String(dueDate)
  const start = dayStart || (todayDate ? `${todayDate} 00:00:00` : null)
  if (start && due < start) return 'Missed deadline'
  const dueDay = due.slice(0, 10)
  if (todayDate && dueDay < todayDate) return 'Missed deadline'
  return 'Due today'
}

export function isTaskOverdue(dueDate, dayStart) {
  if (dueDate == null || dueDate === '' || !dayStart) return false
  return String(dueDate) < String(dayStart)
}

/**
 * Scope list filters to the current user unless they are a manager/admin.
 * Uses owner field and `_assign` (JSON assignee list) via orFilters.
 *
 * @returns {{ filters: Record<string, unknown>, orFilters?: string[][] }}
 */
export function buildOwnerScope({
  isManager = false,
  user = null,
  doctype,
  ownerField,
} = {}) {
  if (isManager || !user || !doctype || !ownerField) {
    return { filters: {} }
  }
  return {
    filters: {},
    orFilters: [
      [doctype, ownerField, '=', user],
      [doctype, '_assign', 'like', `%${user}%`],
    ],
  }
}

/** Tasks use assigned_to (Link) — still include _assign for ToDo assignees. */
export function buildTaskAssigneeScope({ isManager = false, user = null } = {}) {
  return buildOwnerScope({
    isManager,
    user,
    doctype: 'CRM Task',
    ownerField: 'assigned_to',
  })
}

/**
 * Queue row call action only when telephony is configured.
 * Otherwise fall back to open (never a dead Call button).
 */
export function queueCallAction({ phone, telephonyEnabled = false } = {}) {
  if (phone && telephonyEnabled) return 'call'
  return 'open'
}
