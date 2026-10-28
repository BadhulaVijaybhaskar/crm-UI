/**
 * page.route mocks for Frappe API calls. Fixture JSON only — never in prod.
 */
import fs from 'node:fs'
import path from 'node:path'
import { PATHS } from '../config.js'

function readJson(fixtureDir, name, fallback) {
  const p = path.join(PATHS.fixtures, fixtureDir, name)
  if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf8'))
  return fallback
}

function ok(message) {
  return { message }
}

function unwrap(payload, fallback) {
  if (payload == null) return fallback
  return payload.message !== undefined ? payload : ok(payload)
}

function methodFromUrl(url) {
  // /api/method/foo.bar.baz?…  or  /api/resource/…
  try {
    const u = new URL(url)
    const parts = u.pathname.split('/').filter(Boolean)
    if (parts[0] === 'api' && parts[1] === 'method') {
      return { kind: 'method', name: parts.slice(2).join('/'), search: u.searchParams }
    }
    if (parts[0] === 'api' && parts[1] === 'resource') {
      return {
        kind: 'resource',
        doctype: decodeURIComponent(parts[2] || ''),
        name: parts[3] ? decodeURIComponent(parts[3]) : null,
        search: u.searchParams,
      }
    }
  } catch {
    /* ignore */
  }
  return { kind: 'unknown' }
}

function postPayload(req) {
  try {
    return req.postDataJSON?.() || JSON.parse(req.postData() || '{}')
  } catch {
    return {}
  }
}

function emptyReportview() {
  return ok({ keys: [], values: [], user_info: {}, total_count: 0 })
}

/**
 * Pick list payload for a doctype from fixture files.
 * Soft-defaults to empty reportview when the fixture file is absent.
 */
function listForDoctype(fixture, doctype) {
  const d = (doctype || '').toLowerCase()
  if (d.includes('deal') || d === 'crm deal') {
    return unwrap(readJson(fixture, 'deals.json', null), emptyReportview())
  }
  if (d.includes('contact') && !d.includes('crm contacts')) {
    return unwrap(readJson(fixture, 'contacts.json', null), emptyReportview())
  }
  if (d.includes('organization') || d.includes('compan')) {
    return unwrap(
      readJson(fixture, 'organizations.json', null),
      emptyReportview(),
    )
  }
  if (d.includes('lead')) {
    return unwrap(readJson(fixture, 'leads.json', null), emptyReportview())
  }
  if (d.includes('task')) {
    return unwrap(readJson(fixture, 'tasks.json', null), ok([]))
  }
  if (d.includes('deal status') || d.includes('crm deal status')) {
    return unwrap(readJson(fixture, 'stages.json', null), ok([]))
  }
  return null
}

/**
 * Single-doc payload: prefer record.json, then entity-named files.
 */
function recordForDoctype(fixture, doctype, docname) {
  const record = readJson(fixture, 'record.json', null)
  if (record) {
    const doc = record.message || record
    if (!docname || !doc.name || doc.name === docname) {
      return unwrap(record, ok(doc))
    }
  }

  const d = (doctype || '').toLowerCase()
  const candidates = []
  if (d.includes('deal')) candidates.push('deal.json')
  if (d.includes('lead')) candidates.push('lead.json')
  if (d.includes('contact')) candidates.push('contact.json')
  if (d.includes('organization') || d.includes('compan')) {
    candidates.push('organization.json', 'company.json')
  }
  // Also try company.json for deal record side-loads
  if (d.includes('organization')) candidates.push('company.json')

  for (const file of candidates) {
    const payload = readJson(fixture, file, null)
    if (!payload) continue
    const doc = payload.message || payload
    if (!docname || !doc.name || doc.name === docname) {
      return unwrap(payload, ok(doc))
    }
  }

  // Side documents nested under contacts.json / deals.json message arrays
  if (d.includes('contact')) {
    const contacts = readJson(fixture, 'contacts.json', null)
    const list = contacts?.message
    if (Array.isArray(list)) {
      const hit = list.find((c) => c.name === docname)
      if (hit) return ok(hit)
    }
    if (list?.values && list?.keys) {
      const idx = list.keys.indexOf('name')
      const row = list.values.find((v) => v[idx] === docname)
      if (row) {
        const obj = {}
        list.keys.forEach((k, i) => {
          obj[k] = row[i]
        })
        return ok(obj)
      }
    }
  }

  return null
}

function sessionFullName(email) {
  if (email === 'rohan.mehta@example.com') return 'Rohan Mehta'
  if (email === 'sara.khan@example.com') return 'Sara Khan'
  if (email === 'priya.nair@example.com') return 'Priya Nair'
  return email?.split('@')[0] || 'User'
}

export async function installParityMocks(page, { fixture = '04-leads-list' } = {}) {
  const users = readJson(fixture, 'users.json', { message: [] })
  const views = readJson(fixture, 'views.json', { message: [] })
  const leads = readJson(fixture, 'leads.json', null)
  const deals = readJson(fixture, 'deals.json', null)
  const contacts = readJson(fixture, 'contacts.json', null)
  const organizations = readJson(fixture, 'organizations.json', null)
  const stages = readJson(fixture, 'stages.json', null)
  const activities = readJson(fixture, 'activities.json', null)
  const tasks = readJson(fixture, 'tasks.json', null)
  const conversations = readJson(fixture, 'conversations.json', null)
  const meta = readJson(fixture, 'meta-lead.json', null)
  const metaDeal = readJson(fixture, 'meta-deal.json', null)
  const metaContact = readJson(fixture, 'meta-contact.json', null)
  const metaOrg = readJson(fixture, 'meta-organization.json', null)

  const userList = users.message || users
  const sessionUser = Array.isArray(userList) ? userList[0] : userList?.[0]

  await page.route('**/*', async (route) => {
    const req = route.request()
    const url = req.url()

    // Let static assets + document through
    if (
      !url.includes('/api/') &&
      !url.includes('/socket.io') &&
      !url.includes('frappe.client')
    ) {
      return route.continue()
    }

    if (url.includes('/socket.io')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ok: true }),
      })
    }

    const parsed = methodFromUrl(url)
    let body = ok(null)
    const post = req.method() === 'POST' ? postPayload(req) : {}

    // POST body may carry method name for /api/method
    let method = parsed.name || ''
    if (post.cmd) method = post.cmd

    const doctype =
      post.doctype ||
      post.doc?.doctype ||
      parsed.doctype ||
      post.filters?.doctype ||
      ''

    if (
      method.includes('get_users') ||
      url.includes('crm.api.session.get_users')
    ) {
      // transform expects [allUsers, crmUsers]
      body = ok([userList, userList])
    } else if (method.includes('get_user_info')) {
      body = ok(userList)
    } else if (method.includes('get_views') || url.includes('crm.api.views')) {
      body = unwrap(views, ok([]))
    } else if (
      method.includes('get_unread_count') ||
      url.includes('notifications.get_unread_count')
    ) {
      body = ok(1)
    } else if (url.includes('notifications.get_notifications')) {
      body = ok([])
    } else if (method.includes('get_organizations')) {
      body = organizations
        ? unwrap(organizations, ok([]))
        : ok([])
    } else if (
      method.includes('getdoctype') ||
      url.includes('getdoctype')
    ) {
      const dt = (post.doctype || doctype || '').toLowerCase()
      if (dt.includes('deal') && metaDeal) body = metaDeal
      else if (dt.includes('contact') && metaContact) body = metaContact
      else if (
        (dt.includes('organization') || dt.includes('compan')) &&
        metaOrg
      ) {
        body = metaOrg
      } else body = meta || ok([[], []])
    } else if (
      method.includes('get_single_value') ||
      url.includes('get_single_value')
    ) {
      body = ok(1) // setup_completed
    } else if (
      method.includes('frappe.client.get') &&
      !method.includes('get_list') &&
      !method.includes('get_count') &&
      !method.includes('get_value') &&
      !method.includes('get_single')
    ) {
      // frappe.client.get / getdoc — single document
      const name = post.name || parsed.name
      const dt = post.doctype || doctype
      body =
        recordForDoctype(fixture, dt, name) ||
        ok({ name, doctype: dt })
    } else if (
      method.includes('frappe.client.get_list') ||
      method.includes('frappe.desk.reportview.get') ||
      method.includes('frappe.desk.reportview.get_count')
    ) {
      if (method.includes('get_count')) {
        const list = listForDoctype(fixture, doctype)
        const total =
          list?.message?.total_count ??
          (Array.isArray(list?.message) ? list.message.length : 0)
        body = ok(total)
      } else {
        body =
          listForDoctype(fixture, doctype) ||
          (leads ? unwrap(leads, emptyReportview()) : emptyReportview())
      }
    } else if (
      method.includes('get_activities') ||
      method.includes('get_events') ||
      url.includes('activities')
    ) {
      body = activities ? unwrap(activities, ok([])) : ok([])
    } else if (method.includes('get_tasks') || url.includes('CRM Task')) {
      body = tasks ? unwrap(tasks, ok([])) : ok([])
    } else if (
      parsed.kind === 'resource' &&
      parsed.name
    ) {
      // /api/resource/<Doctype>/<name>
      body =
        recordForDoctype(fixture, parsed.doctype, parsed.name) ||
        ok({ name: parsed.name, doctype: parsed.doctype })
    } else if (parsed.kind === 'resource') {
      // /api/resource/<Doctype> list
      const list = listForDoctype(fixture, parsed.doctype)
      if (list) body = list
      else if (parsed.doctype?.toLowerCase().includes('deal status') && stages) {
        body = unwrap(stages, ok([]))
      } else if (
        parsed.doctype?.toLowerCase().includes('deal status') ||
        parsed.doctype === 'CRM Deal Status'
      ) {
        body = stages ? unwrap(stages, ok([])) : ok([])
      } else {
        body = emptyReportview()
      }
    } else if (url.includes('/api/resource/CRM Lead')) {
      body = leads ? unwrap(leads, emptyReportview()) : emptyReportview()
    } else if (url.includes('/api/resource/CRM Deal')) {
      body = deals ? unwrap(deals, emptyReportview()) : emptyReportview()
    } else if (
      url.includes('/api/resource/Contact') ||
      url.includes('/api/resource/CRM%20Contact')
    ) {
      body = contacts ? unwrap(contacts, emptyReportview()) : emptyReportview()
    } else if (url.includes('/api/resource/CRM Organization')) {
      body = organizations
        ? unwrap(organizations, emptyReportview())
        : emptyReportview()
    } else if (
      url.includes('/api/resource/CRM Deal Status') ||
      method.includes('CRM Deal Status')
    ) {
      body = stages ? unwrap(stages, ok([])) : ok([])
    } else if (conversations && method.includes('conversation')) {
      body = unwrap(conversations, ok([]))
    } else if (
      method.includes('crm.api.') ||
      method.includes('frappe.') ||
      parsed.kind === 'method' ||
      parsed.kind === 'resource'
    ) {
      // Soft default — keep the shell alive
      body = ok([])
    } else {
      return route.continue()
    }

    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: { 'X-Frappe-CSRF-Token': 'parity-csrf-token' },
      body: JSON.stringify(body),
    })
  })

  return { sessionUser, priya: sessionUser }
}

export function sessionInitScript(email) {
  const fullName = sessionFullName(email)
  const encoded = encodeURIComponent(fullName)
  return `
(() => {
  document.cookie = 'user_id=${email}; path=/';
  document.cookie = 'system_user=yes; path=/';
  document.cookie = 'full_name=${encoded}; path=/';
  document.cookie = 'user_image=; path=/';
  try {
    localStorage.setItem('isSidebarCollapsed', 'false');
    localStorage.setItem('crm_setup_completed', '1');
    localStorage.setItem('onboardingStatus', JSON.stringify({
      '${email}': { frappecrm_onboarding_status: [{ name: 'done', completed: true }] }
    }));
  } catch (e) {}
})();
`
}

export function themeInitScript(theme) {
  return `
(() => {
  const t = ${JSON.stringify(theme)};
  document.documentElement.setAttribute('data-theme', t);
  if (t === 'dark') document.documentElement.classList.add('dark');
  else document.documentElement.classList.remove('dark');
  try {
    localStorage.setItem('color-scheme', t);
    localStorage.setItem('frappe-ui:color-scheme', t);
  } catch (e) {}
})();
`
}
