/**
 * White-label stub — this deployment does not offer upstream cloud billing.
 * Intentionally contains no vendor hostnames or method paths so the SPA scrub
 * stays clean.
 */

export const currentSiteInfo = {
  data: null,
  loading: false,
  fetch() {
    return Promise.resolve(null)
  },
}

export const confirmLoginToFrappeCloud = () => {
  // no-op
}

export const loginToFrappeCloud = () => {
  // no-op
}
