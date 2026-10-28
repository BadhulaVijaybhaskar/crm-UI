/**
 * Astra pipeline stage colour palette.
 * Keys are stored on CRM Lead/Deal Status.color and render via --crm-* vars
 * (shell owns the token CSS). Legacy named colours map to the closest token.
 */

export const ASTRA_STAGE_COLOURS = Object.freeze([
  'c1',
  'c2',
  'c3',
  'c4',
  'c5',
  'c6',
  'success',
  'danger',
  'warning',
  'teal',
  'blue',
])

/** Default stage name → token (from tokens.json stageColours). */
export const DEFAULT_STAGE_COLOUR_MAP = Object.freeze({
  Qualification: 'c6',
  'Demo/Making': 'c4',
  'Proposal/Quotation': 'c2',
  Negotiation: 'c5',
  'Ready to Close': 'c1',
  Won: 'success',
  Lost: 'danger',
})

const LEGACY_TO_ASTRA = Object.freeze({
  black: 'c6',
  gray: 'c6',
  grey: 'c6',
  blue: 'c2',
  green: 'success',
  red: 'danger',
  pink: 'danger',
  orange: 'c5',
  amber: 'warning',
  yellow: 'c5',
  cyan: 'c1',
  teal: 'teal',
  violet: 'c2',
  purple: 'c1',
})

/** Closest Tailwind ink class when --crm-* is not yet loaded (kanban chips). */
const ASTRA_TO_TAILWIND = Object.freeze({
  c1: 'cyan',
  c2: 'blue',
  c3: 'teal',
  c4: 'blue',
  c5: 'amber',
  c6: 'gray',
  success: 'green',
  danger: 'red',
  warning: 'amber',
  teal: 'teal',
  blue: 'blue',
})

export function isAstraStageColour(color) {
  return ASTRA_STAGE_COLOURS.includes(color)
}

export function toAstraStageColour(color, stageName) {
  if (!color && stageName && DEFAULT_STAGE_COLOUR_MAP[stageName]) {
    return DEFAULT_STAGE_COLOUR_MAP[stageName]
  }
  if (isAstraStageColour(color)) return color
  if (color && LEGACY_TO_ASTRA[color]) return LEGACY_TO_ASTRA[color]
  return 'c6'
}

/** CSS custom property name, e.g. c1 → --crm-c1 */
export function stageColourVarName(color, stageName) {
  const key = toAstraStageColour(color, stageName)
  return `--crm-${key}`
}

export function stageColourCssVar(color, stageName) {
  return `var(${stageColourVarName(color, stageName)})`
}

export function stageColourStyle(color, stageName) {
  return { backgroundColor: stageColourCssVar(color, stageName) }
}

/** Tailwind colour stem for IndicatorIcon / parseColor fallback. */
export function stageColourTailwindStem(color, stageName) {
  const key = toAstraStageColour(color, stageName)
  return ASTRA_TO_TAILWIND[key] || 'gray'
}
