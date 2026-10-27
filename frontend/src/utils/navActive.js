/**
 * Pure nav active-key helpers (mirrors AppSidebar highlight rules).
 * One route name → at most one active key; Astra pages never co-highlight.
 */

export function navItemKey(item) {
  if (!item) return null
  if (item.connect) return `connect:${item.connect}`
  if (item.action) return String(item.action)
  if (item.route) return item.route
  return null
}

/**
 * Resolve which sidebar key is active for a vue-router location.
 * @param {{ name?: string, query?: { view?: string } }} route
 * @param {Array<{ route?: string, connect?: string, action?: string }>} items
 */
export function resolveActiveNavKey(route, items = []) {
  if (!route?.name) return null
  const view = route.query?.view
  const key = view || route.name

  const routeItems = items.filter((i) => i.route)
  const known = routeItems.some(
    (link) => link.route === key || link.route === route.name,
  )
  if (!known && key !== 'Notifications') return null

  // Saved views use the view name as key; plain pages use the route name.
  if (view) {
    const plain = routeItems.find((link) => link.route === route.name)
    // Custom view query on a list page — key is the view id, not the page.
    if (plain) return key
  }

  const match = routeItems.find((link) => link.route === route.name)
  return match ? match.route : key === 'Notifications' ? key : null
}

/** True when exactly one of `keys` equals `active`. */
export function isExclusiveActive(active, keys) {
  if (active == null) return false
  return keys.filter((k) => k === active).length === 1
}
