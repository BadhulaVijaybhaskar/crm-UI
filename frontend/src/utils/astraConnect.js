/**
 * Astra Connect deep-links (placeholders until secure SSO between apps exists).
 * Base URL comes from boot (`astra_connect_url` ← Astra Connect Settings / site config).
 * Never put webhook secrets or other credentials in the frontend.
 */

export const ASTRA_CONNECT_DEFAULT_URL = 'https://connect.astraconnect.io'

export const ASTRA_CONNECT_PATHS = Object.freeze({
  calls: '/calls',
  messages: '/messages',
  employees: '/employees',
  callsNew: '/calls/new',
  messagesNew: '/messages/new',
})

export function getAstraConnectBaseUrl() {
  const fromBoot =
    (typeof window !== 'undefined' && window.astra_connect_url) ||
    (typeof window !== 'undefined' && window.boot?.astra_connect_url)
  const raw = (fromBoot || ASTRA_CONNECT_DEFAULT_URL).trim().replace(/\/$/, '')
  return raw || ASTRA_CONNECT_DEFAULT_URL
}

function getCrmSite() {
  if (typeof window === 'undefined') return ''
  return (
    window.boot?.site_name ||
    window.site_name ||
    window.location?.hostname ||
    ''
  )
}

/** @param {'calls' | 'messages' | 'employees' | string} pathKeyOrPath */
export function getAstraConnectUrl(pathKeyOrPath) {
  const path =
    ASTRA_CONNECT_PATHS[pathKeyOrPath] ||
    (String(pathKeyOrPath).startsWith('/')
      ? pathKeyOrPath
      : `/${pathKeyOrPath}`)
  return `${getAstraConnectBaseUrl()}${path}`
}

/**
 * PLACEHOLDER until SSO: open Connect compose for a CRM record.
 * @param {'calls' | 'messages'} kind
 * @param {{ recordType: string, recordId: string, phone?: string }} opts
 */
export function openConnectCompose(kind, { recordType, recordId, phone } = {}) {
  const path = kind === 'messages' ? '/messages/new' : '/calls/new'
  const params = new URLSearchParams()
  params.set('crm_site', getCrmSite())
  if (recordType) params.set('record_type', recordType)
  if (recordId) params.set('record_id', recordId)
  if (phone) params.set('phone', phone)
  const url = `${getAstraConnectBaseUrl()}${path}?${params.toString()}`
  window.open(url, '_blank', 'noopener,noreferrer')
  return url
}

/** Placeholder until SSO deep-link; always opens a new tab for now. */
export function openAstraConnect(pathKeyOrPath) {
  const url = getAstraConnectUrl(pathKeyOrPath)
  window.open(url, '_blank', 'noopener,noreferrer')
  return url
}
