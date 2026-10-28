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

export async function installParityMocks(page, { fixture = '04-leads-list' } = {}) {
  const users = readJson(fixture, 'users.json', { message: [] })
  const views = readJson(fixture, 'views.json', { message: [] })
  const leads = readJson(fixture, 'leads.json', { message: { data: [], total_count: 0 } })
  const meta = readJson(fixture, 'meta-lead.json', null)

  const userList = users.message || users
  const priya = Array.isArray(userList)
    ? userList[0]
    : userList.message?.[0]

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

    // POST body may carry method name for /api/method
    let method = parsed.name || ''
    if (req.method() === 'POST') {
      try {
        const post = req.postDataJSON?.() || JSON.parse(req.postData() || '{}')
        if (post.cmd) method = post.cmd
      } catch {
        /* plain */
      }
    }

    if (
      method.includes('get_users') ||
      url.includes('crm.api.session.get_users')
    ) {
      // transform expects [allUsers, crmUsers]
      body = ok([userList, userList])
    } else if (method.includes('get_user_info')) {
      body = ok(userList)
    } else if (method.includes('get_views') || url.includes('crm.api.views')) {
      body = views.message !== undefined ? views : ok(views)
    } else if (
      method.includes('get_unread_count') ||
      url.includes('notifications.get_unread_count')
    ) {
      body = ok(1)
    } else if (url.includes('notifications.get_notifications')) {
      body = ok([])
    } else if (method.includes('get_organizations')) {
      body = ok([])
    } else if (
      method.includes('getdoctype') ||
      url.includes('getdoctype')
    ) {
      body = meta || ok([[], []])
    } else if (
      method.includes('get_single_value') ||
      url.includes('get_single_value')
    ) {
      body = ok(1) // setup_completed
    } else if (
      method.includes('frappe.client.get_list') ||
      method.includes('frappe.desk.reportview.get')
    ) {
      body = leads.message !== undefined ? leads : ok(leads)
    } else if (url.includes('/api/resource/CRM Lead')) {
      body = leads.message !== undefined ? leads : ok(leads)
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

  return { priya }
}

export function sessionInitScript(email) {
  return `
(() => {
  document.cookie = 'user_id=${email}; path=/';
  document.cookie = 'system_user=yes; path=/';
  document.cookie = 'full_name=Priya%20Nair; path=/';
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
