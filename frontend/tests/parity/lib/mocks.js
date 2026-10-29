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

function slugify(doctype) {
  return String(doctype || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

function parseBody(req) {
  if (req.method() !== 'POST') return {}
  const raw = req.postData() || ''
  if (!raw) return {}
  try {
    return JSON.parse(raw)
  } catch {
    try {
      return Object.fromEntries(new URLSearchParams(raw))
    } catch {
      return {}
    }
  }
}

function pick(obj, ...keys) {
  for (const k of keys) {
    if (obj?.[k] != null) return obj[k]
  }
  return undefined
}

/** CRM Lead fixture 04 stores reportview-style keys/values; expand to dict rows. */
function leadRows(leads) {
  const payload = leads?.message ?? leads
  if (!payload?.keys || !payload?.values) return []
  return payload.values.map((vals) =>
    Object.fromEntries(payload.keys.map((k, i) => [k, vals[i]])),
  )
}

/**
 * Rows + metadata for a doctype list, from fixtures/<id>/list-<slug>.json
 * (activity screens) or leads.json (04).
 */
function loadList(fixtureDir, doctype, leads) {
  const fromFile = readJson(fixtureDir, `list-${slugify(doctype)}.json`, null)
  if (fromFile) return fromFile
  if (doctype === 'CRM Lead' && leads) {
    const rows = leadRows(leads)
    const payload = leads?.message ?? leads
    return {
      doctype,
      rows,
      total_count: payload?.total_count ?? rows.length,
      columns: [
        { label: 'Name', type: 'Data', key: 'lead_name', width: '12rem' },
        { label: 'Organization', type: 'Data', key: 'organization', width: '12rem' },
        { label: 'Status', type: 'Select', key: 'status', width: '9rem' },
        { label: 'Temperature', type: 'Select', key: 'temperature', width: '8rem' },
        { label: 'Score', type: 'Int', key: 'score', width: '6rem' },
        { label: 'Source', type: 'Link', key: 'source', width: '8rem' },
        { label: 'Owner', type: 'Link', key: 'lead_owner', width: '8rem' },
        { label: 'Created', type: 'Datetime', key: 'creation', width: '8rem' },
      ],
    }
  }
  return null
}

function getDataResponse(list, views) {
  const rows = list.rows || []
  const keys = [...new Set(rows.flatMap((r) => Object.keys(r)))]
  return ok({
    data: rows,
    columns: list.columns || [],
    rows: keys,
    fields: [],
    column_field: null,
    title_field: list.title_field || null,
    kanban_columns: [],
    kanban_fields: [],
    group_by_field: null,
    page_length: 20,
    page_length_count: 20,
    is_default: true,
    views: views?.message ?? views ?? [],
    total_count: list.total_count ?? rows.length,
    row_count: rows.length,
    form_script: null,
    list_script: null,
    view_type: 'list',
    ...(list.extra || {}),
  })
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
  const home = readJson(fixture, 'home.json', null)
  const workQueue = readJson(fixture, 'work-queue.json', null)
  const workQueueDetail = readJson(fixture, 'work-queue-detail.json', {})
  const taskBoard = readJson(fixture, 'task-board.json', null)
  const taskDetail = readJson(fixture, 'task-detail.json', {})
  const notesBoard = readJson(fixture, 'notes-board.json', null)
  const noteDetail = readJson(fixture, 'note-detail.json', {})
  const callLogBoard = readJson(fixture, 'call-log-board.json', null)
  const callLogDetail = readJson(fixture, 'call-log-detail.json', {})
  const conversations = readJson(fixture, 'conversations.json', null)
  const conversationThreads = readJson(fixture, 'conversation-thread.json', {})
  const hasLeads = fs.existsSync(path.join(PATHS.fixtures, fixture, 'leads.json'))

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
    const postBody = parseBody(req)
    const listDoctype =
      pick(postBody, 'doctype') ||
      new URL(url).searchParams.get('doctype') ||
      parsed.doctype ||
      ''
    const list = listDoctype
      ? loadList(fixture, listDoctype, hasLeads ? leads : null)
      : null
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

    if (home && url.includes('crm.api.home.get_home_summary')) {
      body = home
    } else if (workQueue && url.includes('work_queue.get_work_queue_count')) {
      const c = workQueue.message.counts || {}
      body = ok({
        count: c.all ?? 0,
        follow_ups: c.follow_ups ?? 0,
        quiet_leads: c.quiet_leads ?? 0,
        updated_at: workQueue.message.updated_at,
      })
    } else if (workQueue && url.includes('work_queue.get_work_queue_detail')) {
      const key = `${postBody.reference_doctype}::${postBody.reference_docname}`
      body = workQueueDetail[key] || ok(null)
    } else if (workQueue && url.includes('work_queue.get_work_queue')) {
      body = workQueue
    } else if (taskBoard && url.includes('task_board.get_task_board')) {
      body = taskBoard
    } else if (taskBoard && url.includes('task_board.get_task_detail')) {
      body = taskDetail[postBody.name] || ok(null)
    } else if (notesBoard && url.includes('notes_page.get_notes')) {
      body = notesBoard
    } else if (notesBoard && url.includes('notes_page.get_note')) {
      body = noteDetail[postBody.name] || ok(null)
    } else if (callLogBoard && url.includes('call_log_board.get_call_logs')) {
      body = callLogBoard
    } else if (callLogBoard && url.includes('call_log_board.get_call_log_detail')) {
      body = callLogDetail[postBody.name] || ok(null)
    } else if (
      conversations &&
      url.includes('conversations.get_conversation_thread')
    ) {
      const key = `${postBody.reference_doctype}::${postBody.reference_docname}`
      body = conversationThreads[key] || ok(null)
    } else if (conversations && url.includes('conversations.get_conversations')) {
      body = conversations
    } else if (list && url.includes('crm.api.doc.get_data')) {
      body = getDataResponse(list, views)
    } else if (
      list &&
      (method.includes('frappe.client.get_list') ||
        method.includes('frappe.desk.reportview.get') ||
        url.includes(`/api/resource/${listDoctype}`))
    ) {
      body = ok(list.rows || [])
    } else if (
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
      body = ok(fixture === 'm1-home' ? 0 : 1)
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

    if (process.env.PARITY_DEBUG_API) {
      console.log('[parity:api]', req.method(), url.replace(/^https?:\/\/[^/]+/, ''))
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

export function sessionInitScript(email, fullName = 'Priya Nair') {
  return `
(() => {
  document.cookie = 'user_id=${email}; path=/';
  document.cookie = 'system_user=yes; path=/';
  document.cookie = 'full_name=${encodeURIComponent(fullName)}; path=/';
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
  try { localStorage.setItem('theme', t); } catch (e) {}
  const apply = () => {
    const root = document.documentElement;
    if (!root) return;
    root.setAttribute('data-theme', t);
    root.classList.toggle('dark', t === 'dark');
  };
  apply();
  document.addEventListener('DOMContentLoaded', apply);
})();
`
}
