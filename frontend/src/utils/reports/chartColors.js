/**
 * Chart / stage colours via shell-owned --crm-* CSS variables.
 * Do not hardcode hex here; tokens light up when the shell branch lands.
 */

export const CHART_COLOR_VARS = [
  'var(--crm-c1)',
  'var(--crm-c2)',
  'var(--crm-c3)',
  'var(--crm-c4)',
  'var(--crm-c5)',
  'var(--crm-c6)',
]

/** Stage label → token name from tokens.json stageColours */
export const STAGE_COLOR_TOKEN = Object.freeze({
  Qualification: 'c6',
  'Demo/Making': 'c4',
  'Proposal/Quotation': 'c2',
  Negotiation: 'c5',
  'Ready to Close': 'c1',
  Won: 'success',
  Lost: 'danger',
})

export function chartColor(index = 0) {
  return CHART_COLOR_VARS[index % CHART_COLOR_VARS.length]
}

export function stageColor(stage) {
  const token = STAGE_COLOR_TOKEN[stage]
  if (!token) return 'var(--crm-c6)'
  if (token === 'success') return 'var(--crm-success)'
  if (token === 'danger') return 'var(--crm-danger)'
  return `var(--crm-${token})`
}

export function astraPaletteSwatches() {
  return [
    { key: 'c1', css: 'var(--crm-c1)', label: 'Ocean' },
    { key: 'c2', css: 'var(--crm-c2)', label: 'Blue' },
    { key: 'c3', css: 'var(--crm-c3)', label: 'Teal' },
    { key: 'c4', css: 'var(--crm-c4)', label: 'Sky' },
    { key: 'c5', css: 'var(--crm-c5)', label: 'Gold' },
    { key: 'c6', css: 'var(--crm-c6)', label: 'Slate' },
  ]
}
