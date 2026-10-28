import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const FRONTEND = join(HERE, '../..')

function read(...parts) {
  return readFileSync(join(FRONTEND, ...parts), 'utf8')
}

describe('Astra CRM official tokens', () => {
  const css = read('src/astra-crm-tokens.css')
  const tokens = JSON.parse(read('tokens.json'))
  const indexCss = read('src/index.css')
  const tailwind = read('tailwind.config.js')
  const astraTw = read('tailwind.astra.js')

  it('imports official tokens after astra-theme.css', () => {
    const themeAt = indexCss.indexOf("astra-theme.css")
    const tokensAt = indexCss.indexOf("astra-crm-tokens.css")
    expect(themeAt).toBeGreaterThan(-1)
    expect(tokensAt).toBeGreaterThan(themeAt)
  })

  it('keeps the frappe-ui remapping block commented off', () => {
    expect(css).toMatch(/OPTIONAL: align stock UI-kit/)
    const optional = css.slice(css.indexOf('OPTIONAL: align stock UI-kit'))
    expect(optional).toMatch(/^\/\*/)
    expect(optional).not.toMatch(/\*\/\s*:root\s*\{/)
  })

  it('defines light and dark via data-theme', () => {
    expect(css).toMatch(/\[data-theme='dark'\]/)
    expect(css).toMatch(/html\.dark/)
    expect(css).toMatch(/--crm-primary:\s*#0a7393/i)
    expect(css).toMatch(/--crm-primary:\s*#3fbad9/i)
  })

  it('matches tokens.json primary colours', () => {
    expect(tokens.color.light.primary.toLowerCase()).toBe('#0a7393')
    expect(tokens.color.dark.primary.toLowerCase()).toBe('#3fbad9')
    expect(tokens.color.light.nav.toLowerCase()).toBe('#07161f')
    expect(tokens.color.dark.nav.toLowerCase()).toBe('#050f15')
    expect(tokens.stageColours.Negotiation).toBe('c5')
  })

  it('wires tailwind.astra.js into the Tailwind config', () => {
    expect(tailwind).toMatch(/tailwind\.astra\.js/)
    expect(tailwind).toMatch(/extend:\s*astra\.extend/)
    expect(astraTw).toMatch(/colors:\s*\{\s*crm:/)
    expect(astraTw).toMatch(/'crm-nav':\s*'240px'/)
  })

  it('keeps Plus Jakarta Sans as the app font', () => {
    const theme = read('src/astra-theme.css')
    expect(theme).toMatch(/Plus Jakarta Sans/)
    expect(theme).toMatch(/--font-sans/)
  })
})
