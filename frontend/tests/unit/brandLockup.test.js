import { describe, expect, it } from 'vitest'
import { existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const BRAND = join(HERE, '../../src/assets/brand')
const INDEX = join(BRAND, 'index.js')

describe('Astra CRM nav lockup assets', () => {
  it('exports sized on-dark lockup and mark (no placeholder)', () => {
    const src = readFileSync(INDEX, 'utf8')
    expect(src).toMatch(/ASTRA_NAV_LOCKUP/)
    expect(src).toMatch(/ASTRA_NAV_MARK/)
    expect(src).toMatch(/astra-crm-nav-lockup/)
    expect(src).not.toMatch(/placeholder|brand-mark square/i)
  })

  it('ships 1x and 2x lockup PNGs for light and dark nav', () => {
    for (const name of [
      'astra-crm-lockup@1x.png',
      'astra-crm-lockup@2x.png',
      'astra-crm-lockup-on-dark@1x.png',
      'astra-crm-lockup-on-dark@2x.png',
      'astra-crm-nav-lockup.png',
      'astra-crm-nav-mark.png',
    ]) {
      expect(existsSync(join(BRAND, name)), name).toBe(true)
    }
  })
})
