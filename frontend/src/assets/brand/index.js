/**
 * Bundled brand assets. Prefer these over absolute `/assets/crm/images/...`
 * URLs so Vite's `/assets/crm/frontend/` base resolves in production builds.
 * Copies also live under `crm/public/images/` for website/login CSS.
 */
import astraLogo from './astra-crm-logo.png'
import astraLogoOnDark from './astra-crm-logo-on-dark.png'
import astraMark from './astra-crm-mark.png'
import astraFavicon from './favicon-32.png'

export const ASTRA_LOGO = astraLogo
export const ASTRA_LOGO_ON_DARK = astraLogoOnDark
export const ASTRA_MARK = astraMark
export const ASTRA_FAVICON = astraFavicon
