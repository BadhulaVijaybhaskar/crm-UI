/**
 * Astra Connect deep-links. Base URL and visibility come from boot
 * (Astra Connect Settings.enabled + connect_base_url). Never put secrets here.
 */

export const ASTRA_CONNECT_DEFAULT_URL = 'https://connect.astraconnect.io'

export const ASTRA_CONNECT_PATHS = Object.freeze({
  calls: '/calls',
  messages: '/messages',
  employees: '/employees',
  callsNew: '/calls/new',
  messagesNew: '/messages/new',
})

function bootValue(key) {
  if (typeof window === 'undefined') return undefined
  if (window[key] != null && window[key] !== '') return window[key]
  return window.boot?.[key]
}

/**
 * True only when Astra Connect Settings is enabled and connect_base_url is set.
 * Connect nav and Call/Message with AI must stay hidden otherwise.
 */
export function isAstraConnectConfigured() {
  const enabled = bootValue('astra_connect_enabled')
  if (!enabled) return false
  const url = String(bootValue('astra_connect_url') || '')
    .trim()
    .replace(/\/$/, '')
  return Boolean(url)
}

export function getAstraConnectBaseUrl() {
  const fromBoot = String(bootValue('astra_connect_url') || '')
    .trim()
    .replace(/\/$/, '')
  if (fromBoot) return fromBoot
  // Fallback for compose helpers when boot omitted URL; callers still gate on configured.
  return ASTRA_CONNECT_DEFAULT_URL
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
 * Open Connect compose for a CRM record. No-op when Connect is not configured.
 * @param {'calls' | 'messages'} kind
 * @param {{ recordType: string, recordId: string, phone?: string }} opts
 */
export function openConnectCompose(kind, { recordType, recordId, phone } = {}) {
  if (!isAstraConnectConfigured()) return null
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

/** Opens Connect in a new tab. Call only when isAstraConnectConfigured(). */
export function openAstraConnect(pathKeyOrPath) {
  if (!isAstraConnectConfigured()) return null
  const url = getAstraConnectUrl(pathKeyOrPath)
  window.open(url, '_blank', 'noopener,noreferrer')
  return url
}
