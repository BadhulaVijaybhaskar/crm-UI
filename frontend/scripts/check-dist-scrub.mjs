#!/usr/bin/env node
/**
 * Fails if production frontend output still contains repo/vendor URLs,
 * sourceMappingURL, or vendor tokens in filenames users can see.
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const ROOTS = [
  path.resolve(HERE, '../dist'),
  path.resolve(HERE, '../../crm/public/frontend'),
  path.resolve(HERE, '../../crm/www'),
]

const CONTENT_RE =
  /github\.com|gitlab\.|frappe\.io|sourceMappingURL|frappecloud\.com|pulse\.m\.frappe\.cloud|Welcome to Frappe(?: CRM)?|docs\.frappe\.io/i
const NAME_RE = /frappe|erpnext/i
const TEXT_EXT = /\.(js|css|html|webmanifest|json|txt|map)$/i
// Soft checks that should not appear as user-facing defaults after scrub
const SOFT_VENDOR_RE = /"Frappe CRM"|'Frappe CRM'|erpnext\.example\.com/i

function walk(dir, out = []) {
  if (!fs.existsSync(dir)) return out
  for (const name of fs.readdirSync(dir)) {
    if (name === 'node_modules' || name === '.git') continue
    const full = path.join(dir, name)
    const st = fs.statSync(full)
    if (st.isDirectory()) walk(full, out)
    else out.push(full)
  }
  return out
}

const hits = []
let scanned = 0

for (const root of ROOTS) {
  if (!fs.existsSync(root)) continue
  for (const file of walk(root)) {
    scanned++
    const base = path.basename(file)
    if (NAME_RE.test(base) && !base.endsWith('.py')) {
      // Allow nothing under public frontend / www with vendor filenames
      if (
        file.includes(`${path.sep}public${path.sep}frontend${path.sep}`) ||
        file.includes(`${path.sep}www${path.sep}`) ||
        file.includes(`${path.sep}dist${path.sep}`)
      ) {
        hits.push(`filename: ${file}`)
      }
    }
    if (file.endsWith('.map')) {
      hits.push(`sourcemap file: ${file}`)
      continue
    }
    if (!TEXT_EXT.test(file)) continue
    // Skip non-served test fixtures under www if any
    const text = fs.readFileSync(file, 'utf8')
    if (CONTENT_RE.test(text)) {
      const m = text.match(CONTENT_RE)
      hits.push(`content (${m?.[0]}): ${file}`)
    } else if (SOFT_VENDOR_RE.test(text)) {
      const m = text.match(SOFT_VENDOR_RE)
      hits.push(`vendor string (${m?.[0]}): ${file}`)
    }
  }
}

if (!scanned) {
  console.error(
    'check-dist-scrub: no build output found. Run `yarn build` first.',
  )
  process.exit(1)
}

if (hits.length) {
  console.error('check-dist-scrub: forbidden strings/files in production output:')
  for (const h of hits.slice(0, 50)) console.error(' -', h)
  if (hits.length > 50) console.error(` ... and ${hits.length - 50} more`)
  process.exit(1)
}

console.log(`check-dist-scrub: ok (${scanned} files scanned)`)
