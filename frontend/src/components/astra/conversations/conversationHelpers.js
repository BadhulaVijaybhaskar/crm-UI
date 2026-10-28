/**
 * Pure Conversations helpers — WA field name, titles, pagination fill.
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

/** Default page size / fill target for the conversations thread list. */
export const CONVERSATIONS_TARGET_VISIBLE = 40
/** Cap how many list pages we pull while filling the visible list. */
export const CONVERSATIONS_MAX_PAGES = 5

/**
 * Whether another list page should be fetched while filling the inbox.
 * Pure — used by useConversations and unit tests.
 */
export function shouldFetchNextConversationPage({
  visibleCount = 0,
  targetCount = CONVERSATIONS_TARGET_VISIBLE,
  hasNextPage = false,
  pagesFetched = 0,
  maxPages = CONVERSATIONS_MAX_PAGES,
  loading = false,
} = {}) {
  if (loading) return false
  if (visibleCount >= targetCount) return false
  if (!hasNextPage) return false
  if (pagesFetched >= maxPages) return false
  return true
}

/**
 * Pick which list resources still need another page to grow the visible list.
 * @returns {string[]} resource keys to advance
 */
export function conversationSourcesToAdvance(
  sources = [],
  {
    visibleCount = 0,
    targetCount = CONVERSATIONS_TARGET_VISIBLE,
    maxPages = CONVERSATIONS_MAX_PAGES,
  } = {},
) {
  if (visibleCount >= targetCount) return []
  return sources
    .filter(
      (s) =>
        s &&
        s.hasNextPage &&
        !s.loading &&
        (s.pagesFetched || 0) < maxPages,
    )
    .map((s) => s.key)
}
