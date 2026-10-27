import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const FRONTEND = join(HERE, '../..')

describe('page meta and PWA branding', () => {
  it('index.html uses Astra titles/meta with no vendor generator or repo URLs', () => {
    const html = readFileSync(join(FRONTEND, 'index.html'), 'utf8')
    expect(html).toMatch(/<title>Astra CRM<\/title>/)
    expect(html).toMatch(/application-name" content="Astra CRM"/)
    expect(html).toMatch(/og:title" content="Astra CRM"/)
    expect(html).not.toMatch(/generator|github\.com|gitlab\.|frappe\.io/i)
  })

  it('vite PWA manifest is Astra-branded without vendor tokens', () => {
    const conf = readFileSync(join(FRONTEND, 'vite.config.js'), 'utf8')
    expect(conf).toMatch(/name:\s*'Astra CRM'/)
    expect(conf).toMatch(/short_name:\s*'Astra CRM'/)
    expect(conf).toMatch(/sourcemap:\s*false/)
    expect(conf).toMatch(/legalComments:\s*'none'/)
    expect(conf).toMatch(/astraProductionScrub/)
  })
})
