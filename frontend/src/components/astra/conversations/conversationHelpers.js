/**
 * Pure Conversations helpers — WA field name, titles, permission filtering.
 */

/** WA Message uses reference_docname (not reference_name). */
export function waMessageReference(doc) {
  if (!doc) return null
  return doc.reference_docname || null
}

export function buildParentTitleMap({
  leads = [],
  deals = [],
  contacts = [],
} = {}) {
  const map = {}
  for (const l of leads) {
    if (!l?.name) continue
    map[`CRM Lead:${l.name}`] =
      [l.lead_name, l.organization].filter(Boolean).join(' · ') || l.name
  }
  for (const d of deals) {
    if (!d?.name) continue
    map[`CRM Deal:${d.name}`] = d.organization || d.name
  }
  for (const c of contacts) {
    if (!c?.name) continue
    map[`Contact:${c.name}`] =
      c.full_name ||
      [c.first_name, c.last_name].filter(Boolean).join(' ') ||
      c.name
  }
  return map
}

export function buildReadableParentSets({
  leads = [],
  deals = [],
  contacts = [],
} = {}) {
  return {
    'CRM Lead': new Set(leads.map((r) => r.name).filter(Boolean)),
    'CRM Deal': new Set(deals.map((r) => r.name).filter(Boolean)),
    Contact: new Set(contacts.map((r) => r.name).filter(Boolean)),
  }
}

/**
 * Keep threads whose parent the user can read (or that have no parent).
 * Never list a parent that would 403 on get / get_activities.
 */
export function filterThreadsByReadableParents(threads = [], readableSets = {}) {
  return threads.filter((t) => {
    if (!t?.reference_doctype || !t?.reference_docname) return true
    const set = readableSets[t.reference_doctype]
    if (!set) return false
    return set.has(t.reference_docname)
  })
}

export function threadDisplayTitle(
  { reference_doctype, reference_docname, fallback } = {},
  titleMap = {},
) {
  if (reference_doctype && reference_docname) {
    const key = `${reference_doctype}:${reference_docname}`
    if (titleMap[key]) return titleMap[key]
  }
  return fallback || reference_docname || ''
}
