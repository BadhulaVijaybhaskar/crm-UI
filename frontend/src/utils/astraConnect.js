/**
 * Astra Connect deep-links (placeholders until secure SSO is built).
 * Base URL comes from site config `astra_connect_url`, defaulting to production.
 */
export const ASTRA_CONNECT_DEFAULT_URL = 'https://connect.astraconnect.io'

export const ASTRA_CONNECT_PATHS = Object.freeze({
  calls: '/calls',
  messages: '/messages',
  employees: '/employees',
})

export function getAstraConnectBaseUrl() {
  const fromBoot =
    (typeof window !== 'undefined' && window.astra_connect_url) ||
    (typeof window !== 'undefined' && window.boot?.astra_connect_url)
  const raw = (fromBoot || ASTRA_CONNECT_DEFAULT_URL).trim().replace(/\/$/, '')
  return raw || ASTRA_CONNECT_DEFAULT_URL
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

/** Placeholder until SSO deep-link; always opens a new tab for now. */
export function openAstraConnect(pathKeyOrPath) {
  const url = getAstraConnectUrl(pathKeyOrPath)
  window.open(url, '_blank', 'noopener,noreferrer')
  return url
}
