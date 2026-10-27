import { describe, expect, it } from 'vitest'

// Mirror of crm.utils.sanitize.sanitize_html for client-side notes preview.
function sanitizeHtml(html) {
  if (!html) return ''
  const doc = new DOMParser().parseFromString(String(html), 'text/html')
  doc.querySelectorAll('script,style,iframe,object,embed,link,meta').forEach((n) => n.remove())
  const allowed = new Set([
    'A',
    'B',
    'BLOCKQUOTE',
    'BR',
    'CODE',
    'DIV',
    'EM',
    'H1',
    'H2',
    'H3',
    'H4',
    'H5',
    'H6',
    'HR',
    'I',
    'LI',
    'OL',
    'P',
    'PRE',
    'SPAN',
    'STRONG',
    'U',
    'UL',
  ])
  doc.body.querySelectorAll('*').forEach((el) => {
    if (!allowed.has(el.tagName)) {
      el.replaceWith(...el.childNodes)
      return
    }
    ;[...el.attributes].forEach((attr) => {
      const name = attr.name.toLowerCase()
      if (name.startsWith('on')) el.removeAttribute(attr.name)
      if (name === 'href' && /^\s*javascript:/i.test(attr.value)) {
        el.removeAttribute(attr.name)
      }
    })
  })
  return doc.body.innerHTML
}

describe('sanitizeHtml mirror', () => {
  it('strips script and event handlers', () => {
    const out = sanitizeHtml(
      '<p>Hi<script>alert(1)</script></p><img src=x onerror=alert(1)><a href="javascript:alert(1)">x</a>',
    )
    expect(out).not.toContain('<script')
    expect(out).not.toContain('onerror')
    expect(out).not.toContain('javascript:')
  })

  it('keeps basic formatting', () => {
    const out = sanitizeHtml('<p><strong>Bold</strong> and <em>italic</em></p>')
    expect(out).toContain('<strong>Bold</strong>')
    expect(out).toContain('<em>italic</em>')
  })
})
