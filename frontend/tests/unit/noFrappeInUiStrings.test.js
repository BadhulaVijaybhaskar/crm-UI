import { describe, expect, it } from 'vitest'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const SRC_ROOT = join(HERE, '../../src')

const EXCLUDED_PATHS = [
  // Legal notices page may mention licence obligations; content is guarded
  // separately in legalNotices.test.js (no vendor/repo strings allowed there).
  /pages\/LegalNotices\.vue$/,
]

const TRANSLATE_CALL =
  /(?:^|[^\w$])__\(\s*(["'`])((?:\\.|(?!\1)[\s\S])*?)\1/g

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name)
    const st = statSync(path)
    if (st.isDirectory()) walk(path, out)
    else if (/\.(vue|js|ts|tsx|jsx)$/.test(name)) out.push(path)
  }
  return out
}

function stripComments(source) {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/(^|[^:])\/\/.*$/gm, '$1')
    .replace(/<!--[\s\S]*?-->/g, '')
}

function templateSection(source) {
  const match = source.match(/<template\b[^>]*>([\s\S]*?)<\/template>/i)
  return match ? match[1] : ''
}

function isExcluded(path) {
  const rel = relative(SRC_ROOT, path).replaceAll('\\', '/')
  return EXCLUDED_PATHS.some((re) => re.test(rel))
}

function findHits(path, source) {
  const hits = []
  const cleaned = stripComments(source)
  const rel = relative(SRC_ROOT, path).replaceAll('\\', '/')

  if (path.endsWith('.vue')) {
    const tmpl = templateSection(cleaned)
    // Ignore component/tag names and attribute bindings that are identifiers,
    // but flag plain text / attribute string values containing Frappe.
    const textChunks = tmpl
      .replace(/<\/?[A-Za-z][\w.-]*\b[^>]*>/g, ' ')
      .replace(/\{\{[\s\S]*?\}\}/g, (expr) => {
        // Keep string literals inside mustaches
        let kept = ''
        const re = /(["'`])((?:\\.|(?!\1)[\s\S])*?)\1/g
        let m
        while ((m = re.exec(expr))) kept += ` ${m[2]} `
        return kept
      })
    if (/frappe/i.test(textChunks)) {
      hits.push(`${rel} <template> text`)
    }
  }

  let match
  TRANSLATE_CALL.lastIndex = 0
  while ((match = TRANSLATE_CALL.exec(cleaned))) {
    if (/frappe/i.test(match[2])) {
      hits.push(`${rel} __('${match[2].slice(0, 80)}')`)
    }
  }

  return hits
}

describe('no Frappe in user-facing frontend strings', () => {
  it('does not mention Frappe outside Legal notices / imports', () => {
    const files = walk(SRC_ROOT).filter((p) => !isExcluded(p))
    const hits = files.flatMap((p) => findHits(p, readFileSync(p, 'utf8')))
    expect(hits, hits.join('\n')).toEqual([])
  })
})
