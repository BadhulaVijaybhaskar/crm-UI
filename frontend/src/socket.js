import { io } from 'socket.io-client'
import { getCachedListResource, getCachedResource } from 'frappe-ui'

/**
 * Socket.IO URL for realtime.
 *
 * Default: same-origin (`/socket.io` via the site nginx/proxy) so CSP
 * `connect-src 'self'` allows the connection on every /crm page.
 *
 * Only when `window.socketio_port` is explicitly set (site/boot config) do we
 * dial a cross-port absolute URL — the app CSP then adds that origin.
 */
export function getSocketioUrl() {
  const siteName = window.site_name || ''
  const configured = window.socketio_port
  if (configured !== undefined && configured !== null && configured !== '') {
    const host = window.location.hostname
    const protocol = window.location.protocol === 'https:' ? 'https' : 'http'
    return `${protocol}://${host}:${configured}/${siteName}`
  }
  // Same-origin — proxy terminates /socket.io (and /{site}) on this host.
  return `${window.location.origin}/${siteName}`
}

export function initSocket() {
  const url = getSocketioUrl()

  let socket = io(url, {
    withCredentials: true,
    // Retry for good, with growing random gaps, so open tabs don't all
    // reconnect at the same moment while the server is slow.
    reconnectionDelay: 2000,
    reconnectionDelayMax: 30000,
    randomizationFactor: 0.5,
  })
  socket.on('refetch_resource', (data) => {
    if (data.cache_key) {
      let resource =
        getCachedResource(data.cache_key) ||
        getCachedListResource(data.cache_key)
      if (resource) {
        resource.reload()
      }
    }
  })
  return socket
}
