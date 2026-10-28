/**
 * Production scrub: no source maps, no vendor chunk filenames, no repo/vendor
 * URLs left in served JS/CSS/HTML/SW. LICENSE files in the repo stay untouched.
 */
import fs from 'node:fs'
import path from 'node:path'

const FORBIDDEN_URL =
  /https?:\/\/[^\s"'`)]*(?:github\.com|gitlab\.[\w.-]+|frappe\.io)[^\s"'`)]*/gi

const VENDOR_IN_NAME = /frappe|erpnext|frappe-?ui/i

function sanitizeName(name) {
  return (
    String(name || 'chunk')
      .replace(/frappe-?ui/gi, 'ui-lib')
      .replace(/frappe[_-]*/gi, '')
      .replace(/erpnext/gi, 'erp')
      .replace(/[^a-zA-Z0-9._-]+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^[-.]+|[-.]+$/g, '') || 'chunk'
  )
}

function scrubText(text) {
  return String(text)
    .replace(/\/\/# sourceMappingURL=.*$/gm, '')
    .replace(/\/\*# sourceMappingURL=.*?\*\//gs, '')
    .replace(FORBIDDEN_URL, '')
    // Signup / onboarding vendor strings that leak into guest-visible bundles
    .replace(/https?:\/\/(?:www\.)?frappecloud\.com[^\s"'`]*/gi, '')
    .replace(/frappecloud\.com/gi, '')
    .replace(/pulse\.m\.frappe\.cloud/gi, '')
    .replace(/Welcome to Frappe CRM/g, 'Welcome to Astra CRM')
    .replace(/Welcome to Frappe/g, 'Welcome to Astra CRM')
    .replace(/"Frappe CRM"/g, '"Astra CRM"')
    .replace(/'Frappe CRM'/g, "'Astra CRM'")
    .replace(/https:\/\/docs\.frappe\.io\/crm/gi, '')
    .replace(/erpnext\.example\.com/gi, 'erp.example.com')
}

function walkFiles(dir, out = []) {
  if (!fs.existsSync(dir)) return out
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name)
    const st = fs.statSync(full)
    if (st.isDirectory()) walkFiles(full, out)
    else out.push(full)
  }
  return out
}

export function astraProductionScrub() {
  return {
    name: 'astra-production-scrub',
    apply: 'build',
    enforce: 'post',
    config() {
      return {
        build: {
          sourcemap: false,
          rollupOptions: {
            output: {
              chunkFileNames: (info) =>
                `assets/${sanitizeName(info.name)}-[hash].js`,
              entryFileNames: 'assets/[name]-[hash].js',
              assetFileNames: (info) => {
                const raw = info.name || 'asset'
                const ext = path.extname(raw).slice(1) || 'bin'
                const base = sanitizeName(path.basename(raw, path.extname(raw)))
                return `assets/${base}-[hash].${ext}`
              },
            },
          },
        },
        esbuild: {
          legalComments: 'none',
        },
      }
    },
    generateBundle(_options, bundle) {
      for (const fileName of Object.keys(bundle)) {
        const item = bundle[fileName]
        if (fileName.endsWith('.map')) {
          delete bundle[fileName]
          continue
        }
        if (item.type === 'chunk' && typeof item.code === 'string') {
          item.code = scrubText(item.code)
          if (item.map) item.map = null
        }
        if (item.type === 'asset' && typeof item.source === 'string') {
          if (
            fileName.endsWith('.js') ||
            fileName.endsWith('.css') ||
            fileName.endsWith('.html') ||
            fileName.endsWith('.webmanifest')
          ) {
            item.source = scrubText(item.source)
          }
        }
        // Rename emitted files that still carry vendor tokens
        if (VENDOR_IN_NAME.test(fileName)) {
          const next = fileName
            .split('/')
            .map((part) =>
              VENDOR_IN_NAME.test(part)
                ? part.replace(VENDOR_IN_NAME, (m) =>
                    /ui/i.test(m) ? 'ui-lib' : 'app',
                  )
                : part,
            )
            .join('/')
          if (next !== fileName && !bundle[next]) {
            bundle[next] = item
            delete bundle[fileName]
            if (item.fileName) item.fileName = next
          }
        }
      }
    },
    writeBundle(options) {
      const outDir = options.dir
      if (!outDir) return
      for (const file of walkFiles(outDir)) {
        if (file.endsWith('.map')) {
          fs.unlinkSync(file)
          continue
        }
        if (!/\.(js|css|html|webmanifest)$/i.test(file)) continue
        const before = fs.readFileSync(file, 'utf8')
        const after = scrubText(before)
        if (after !== before) fs.writeFileSync(file, after)
      }
    },
  }
}
