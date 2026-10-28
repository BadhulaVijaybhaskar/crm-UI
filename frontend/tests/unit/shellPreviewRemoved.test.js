import { describe, expect, it } from 'vitest'
import { existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const FRONTEND = join(HERE, '../..')

describe('shell preview mock HTML', () => {
  it('does not ship astra-shell-preview.html', () => {
    expect(existsSync(join(FRONTEND, 'astra-shell-preview.html'))).toBe(false)
  })

  it('does not leave other static shell/login mock HTML in frontend/', () => {
    const suspects = [
      'astra-shell-preview.html',
      'shell-preview.html',
      'login-preview.html',
      'public/astra-shell-preview.html',
    ]
    for (const rel of suspects) {
      expect(existsSync(join(FRONTEND, rel)), rel).toBe(false)
    }
  })
})
