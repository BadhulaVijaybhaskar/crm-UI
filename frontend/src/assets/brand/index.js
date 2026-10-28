/**
 * Bundled brand assets. Prefer these over absolute `/assets/crm/images/...`
 * URLs so Vite's `/assets/crm/frontend/` base resolves in production builds.
 * Copies also live under `crm/public/images/` for website/login CSS.
 *
 * Nav uses the on-dark lockup (white wordmark) and mark; sized @1x/@2x PNGs
 * keep the rail crisp without shipping the multi-megabyte masters.
 */
import astraLogo from './astra-crm-logo.png'
import astraLogoOnDark from './astra-crm-logo-on-dark.png'
import astraMark from './astra-crm-mark.png'
import astraFavicon from './favicon-32.png'
import astraNavLockup from './astra-crm-nav-lockup.png'
import astraNavMark from './astra-crm-nav-mark.png'
import astraLockup1x from './astra-crm-lockup@1x.png'
import astraLockup2x from './astra-crm-lockup@2x.png'
import astraLockupOnDark1x from './astra-crm-lockup-on-dark@1x.png'
import astraLockupOnDark2x from './astra-crm-lockup-on-dark@2x.png'
import astraMark1x from './astra-crm-mark@1x.png'
import astraMark2x from './astra-crm-mark@2x.png'

export const ASTRA_LOGO = astraLogo
export const ASTRA_LOGO_ON_DARK = astraLogoOnDark
export const ASTRA_MARK = astraMark
export const ASTRA_FAVICON = astraFavicon

/** Dark-nav lockup (displayed at 24px height). */
export const ASTRA_NAV_LOCKUP = astraNavLockup
export const ASTRA_NAV_LOCKUP_SRCSET = `${astraLockupOnDark1x} 1x, ${astraLockupOnDark2x} 2x`

/** Collapsed-nav mark (displayed at 28px). */
export const ASTRA_NAV_MARK = astraNavMark
export const ASTRA_NAV_MARK_SRCSET = `${astraMark1x} 1x, ${astraMark2x} 2x`

/** Light-surface lockup srcset (login form pane). */
export const ASTRA_LOCKUP_SRCSET = `${astraLockup1x} 1x, ${astraLockup2x} 2x`
