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

/** Default CRM Lead Status rows (Figma 05 stage rail). */
const DEFAULT_LEAD_STATUSES = [
  { name: 'New', color: 'gray', position: 1, type: 'Open' },
  { name: 'Contacted', color: 'orange', position: 2, type: 'Open' },
  { name: 'Nurture', color: 'blue', position: 3, type: 'Open' },
  { name: 'Qualified', color: 'green', position: 4, type: 'Open' },
  // Keep Converted on the open path (Figma DEAL group); only Unqualified/Junk close out.
  { name: 'Converted', color: 'green', position: 5, type: 'Open' },
  { name: 'Unqualified', color: 'red', position: 6, type: 'Lost' },
  { name: 'Junk', color: 'red', position: 7, type: 'Lost' },
]

/** Default CRM Deal Status rows when stages.json is absent. */
const DEFAULT_DEAL_STATUSES = [
  { name: 'Qualification', color: 'gray', position: 1, type: 'Open', probability: 10 },
  { name: 'Demo/Making', color: 'orange', position: 2, type: 'Open', probability: 40 },
  { name: 'Proposal/Quotation', color: 'blue', position: 3, type: 'Open', probability: 60 },
  { name: 'Negotiation', color: 'purple', position: 4, type: 'Open', probability: 80 },
  { name: 'Ready to Close', color: 'green', position: 5, type: 'Open', probability: 90 },
  { name: 'Won', color: 'green', position: 6, type: 'Won', probability: 100 },
  { name: 'Lost', color: 'red', position: 7, type: 'Lost', probability: 0 },
]

function defaultMeta(doctype) {
  const d = (doctype || '').toLowerCase()
  let title_field = 'name'
  let fields = [{ fieldname: 'name', fieldtype: 'Data', label: 'Name' }]
  if (d.includes('lead') && !d.includes('status')) {
    title_field = 'lead_name'
    fields = [
      { fieldname: 'lead_name', fieldtype: 'Data', label: 'Lead Name' },
      { fieldname: 'status', fieldtype: 'Link', label: 'Status', options: 'CRM Lead Status' },
      { fieldname: 'organization', fieldtype: 'Data', label: 'Organization' },
      { fieldname: 'job_title', fieldtype: 'Data', label: 'Job Title' },
      { fieldname: 'email', fieldtype: 'Data', label: 'Email' },
      { fieldname: 'mobile_no', fieldtype: 'Data', label: 'Mobile' },
      { fieldname: 'website', fieldtype: 'Data', label: 'Website' },
      { fieldname: 'lead_owner', fieldtype: 'Link', label: 'Owner', options: 'User' },
      { fieldname: 'temperature', fieldtype: 'Select', label: 'Temperature' },
      { fieldname: 'lead_score', fieldtype: 'Int', label: 'Lead score' },
      { fieldname: 'source', fieldtype: 'Data', label: 'Source' },
      { fieldname: 'industry', fieldtype: 'Data', label: 'Industry' },
      { fieldname: 'no_of_employees', fieldtype: 'Data', label: 'Employees' },
      { fieldname: 'annual_revenue', fieldtype: 'Currency', label: 'Annual revenue' },
      { fieldname: 'territory', fieldtype: 'Data', label: 'Territory' },
      { fieldname: 'linkedin', fieldtype: 'Data', label: 'LinkedIn' },
      { fieldname: 'sla', fieldtype: 'Data', label: 'SLA' },
      { fieldname: 'sla_status', fieldtype: 'Data', label: 'SLA Status' },
    ]
  } else if (d.includes('deal') && !d.includes('status')) {
    title_field = 'organization_name'
    fields = [
      { fieldname: 'organization', fieldtype: 'Link', label: 'Organization', options: 'CRM Organization' },
      { fieldname: 'organization_name', fieldtype: 'Data', label: 'Organization Name' },
      { fieldname: 'deal_name', fieldtype: 'Data', label: 'Deal Name' },
      { fieldname: 'status', fieldtype: 'Link', label: 'Stage', options: 'CRM Deal Status' },
      { fieldname: 'deal_value', fieldtype: 'Currency', label: 'Deal value', options: 'currency', precision: 0 },
      {
        fieldname: 'expected_deal_value',
        fieldtype: 'Currency',
        label: 'Expected value',
        options: 'currency',
        precision: 0,
      },
      { fieldname: 'expected_closure_date', fieldtype: 'Date', label: 'Expected close' },
      { fieldname: 'currency', fieldtype: 'Link', label: 'Currency', options: 'Currency' },
      { fieldname: 'probability', fieldtype: 'Percent', label: 'Probability' },
      { fieldname: 'source', fieldtype: 'Data', label: 'Source' },
      { fieldname: 'territory', fieldtype: 'Data', label: 'Territory' },
      { fieldname: 'deal_owner', fieldtype: 'Link', label: 'Owner', options: 'User' },
      { fieldname: 'next_step', fieldtype: 'Data', label: 'Next step' },
      { fieldname: 'website', fieldtype: 'Data', label: 'Website' },
      { fieldname: 'email', fieldtype: 'Data', label: 'Email' },
      { fieldname: 'mobile_no', fieldtype: 'Data', label: 'Mobile' },
    ]
  } else if (d.includes('contact')) {
    title_field = 'full_name'
    fields = [
      { fieldname: 'full_name', fieldtype: 'Data', label: 'Full Name' },
      { fieldname: 'email_id', fieldtype: 'Data', label: 'Email' },
      { fieldname: 'mobile_no', fieldtype: 'Data', label: 'Mobile' },
    ]
  } else if (d.includes('organization') || d.includes('compan')) {
    title_field = 'organization_name'
    fields = [
      { fieldname: 'organization_name', fieldtype: 'Data', label: 'Organization Name' },
      { fieldname: 'website', fieldtype: 'Data', label: 'Website' },
      { fieldname: 'industry', fieldtype: 'Data', label: 'Industry' },
    ]
  } else if (d.includes('fcrm settings')) {
    title_field = 'name'
    fields = [
      { fieldname: 'setup_completed', fieldtype: 'Check', label: 'Setup Completed' },
      { fieldname: 'brand_name', fieldtype: 'Data', label: 'Brand Name' },
    ]
  }
  return ok({
    docs: [
      {
        name: doctype,
        doctype: 'DocType',
        title_field,
        fields,
        permissions: [
          {
            role: 'System Manager',
            read: 1,
            write: 1,
            create: 1,
            delete: 1,
            submit: 0,
            cancel: 0,
            amend: 0,
          },
        ],
      },
    ],
    user_settings: '{}',
  })
}

function defaultSidepanel(doctype) {
  const d = (doctype || '').toLowerCase()
  if (d.includes('lead')) {
    return ok([
      {
        name: 'details',
        label: 'Details',
        opened: true,
        columns: [
          {
            name: 'col1',
            fields: [
              { fieldname: 'status', label: 'Status', fieldtype: 'Link' },
              { fieldname: 'temperature', label: 'Temperature', fieldtype: 'Data' },
              {
                fieldname: 'lead_score',
                label: 'Lead score',
                fieldtype: 'Data',
              },
              { fieldname: 'source', label: 'Source', fieldtype: 'Data' },
              { fieldname: 'industry', label: 'Industry', fieldtype: 'Data' },
              { fieldname: 'no_of_employees', label: 'Employees', fieldtype: 'Data' },
              { fieldname: 'annual_revenue', label: 'Annual revenue', fieldtype: 'Currency' },
              { fieldname: 'territory', label: 'Territory', fieldtype: 'Data' },
            ],
          },
        ],
      },
      {
        name: 'contact',
        label: 'Contact',
        opened: true,
        columns: [
          {
            name: 'col1',
            fields: [
              { fieldname: 'email', label: 'Email', fieldtype: 'Data' },
              { fieldname: 'mobile_no', label: 'Mobile', fieldtype: 'Data' },
              { fieldname: 'website', label: 'Website', fieldtype: 'Data' },
              { fieldname: 'linkedin', label: 'LinkedIn', fieldtype: 'Data' },
            ],
          },
        ],
      },
    ])
  }
  if (d.includes('deal')) {
    return ok([
      {
        name: 'details',
        label: 'Details',
        opened: true,
        columns: [
          {
            name: 'col1',
            fields: [
              { fieldname: 'status', label: 'Status', fieldtype: 'Link' },
              { fieldname: 'organization', label: 'Organization', fieldtype: 'Link' },
              { fieldname: 'annual_revenue', label: 'Amount', fieldtype: 'Currency' },
            ],
          },
        ],
      },
    ])
  }
  if (d.includes('contact')) {
    return ok([
      {
        name: 'details',
        label: 'Details',
        opened: true,
        columns: [
          {
            name: 'col1',
            fields: [
              { fieldname: 'email_id', label: 'Email', fieldtype: 'Data' },
              { fieldname: 'mobile_no', label: 'Mobile', fieldtype: 'Data' },
            ],
          },
        ],
      },
    ])
  }
  if (d.includes('organization') || d.includes('compan')) {
    return ok([
      {
        name: 'details',
        label: 'Details',
        opened: true,
        columns: [
          {
            name: 'col1',
            fields: [
              { fieldname: 'website', label: 'Website', fieldtype: 'Data' },
              { fieldname: 'industry', label: 'Industry', fieldtype: 'Data' },
            ],
          },
        ],
      },
    ])
  }
  return ok([])
}

/**
 * Pick list payload for a doctype from fixture files.
 * Soft-defaults to empty reportview when the fixture file is absent.
 * Status doctypes MUST be checked before lead/deal entity lists.
 */
function listForDoctype(fixture, doctype) {
  const d = (doctype || '').toLowerCase()
  if (d.includes('lead status') || d === 'crm lead status') {
    const fromFile = readJson(fixture, 'lead-statuses.json', null)
    if (fromFile) return unwrap(fromFile, ok(DEFAULT_LEAD_STATUSES))
    return ok(DEFAULT_LEAD_STATUSES)
  }
  if (d.includes('deal status') || d === 'crm deal status') {
    const fromFile =
      readJson(fixture, 'stages.json', null) ||
      readJson(fixture, 'deal-statuses.json', null)
    if (fromFile) {
      const msg = fromFile.message || fromFile
      // stages.json may be kanban columns — normalize to status rows when needed
      if (Array.isArray(msg) && msg.length && msg[0]?.name) {
        return ok(
          msg.map((row, i) => ({
            name: row.name,
            color: row.color || 'gray',
            position: row.position ?? i + 1,
            type: row.type || 'Open',
            probability: row.probability,
          })),
        )
      }
      return unwrap(fromFile, ok(DEFAULT_DEAL_STATUSES))
    }
    return ok(DEFAULT_DEAL_STATUSES)
  }
  if (d.includes('communication status')) {
    return ok([{ name: 'Open' }, { name: 'Replied' }, { name: 'Closed' }])
  }
  if (d === 'crm deal' || (d.includes('deal') && !d.includes('status'))) {
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
  if (d === 'crm lead' || (d.includes('lead') && !d.includes('status'))) {
    return unwrap(readJson(fixture, 'leads.json', null), emptyReportview())
  }
  if (d.includes('task')) {
    return unwrap(readJson(fixture, 'tasks.json', null), ok([]))
  }
  return null
}

/** Resolve doctype/name from POST body or GET query — never the method path. */
function resolveDocArgs(post, parsed, fallbackDoctype = '') {
  const search = parsed.search
  const name =
    post.name ||
    post.docname ||
    (search && search.get('name')) ||
    null
  const dt =
    post.doctype ||
    post.doc?.doctype ||
    (search && search.get('doctype')) ||
    parsed.doctype ||
    fallbackDoctype ||
    ''
  return { name, dt }
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

/** Flatten reportview / list payloads into row objects. */
function rowsFromListPayload(payload) {
  if (Array.isArray(payload?.data)) return payload.data
  if (Array.isArray(payload?.values) && Array.isArray(payload?.keys)) {
    return payload.values.map((row) => {
      const obj = {}
      payload.keys.forEach((k, i) => {
        obj[k] = row[i]
      })
      return obj
    })
  }
  if (Array.isArray(payload)) return payload
  return []
}

/**
 * frappe.client.get_list returns an array of row objects.
 * Reportview fixtures use {keys,values} — convert + apply simple equality filters.
 */
function getListResponse(fixture, doctype, filters) {
  const list = listForDoctype(fixture, doctype)
  let rows = rowsFromListPayload(list?.message || list || {})
  if (filters && typeof filters === 'object' && !Array.isArray(filters)) {
    rows = rows.filter((row) => {
      for (const [key, raw] of Object.entries(filters)) {
        let expected = raw
        if (Array.isArray(raw)) {
          // ['=', value] / ['!=', value] — honor common list filter shapes
          const op = String(raw[0] || '=').toLowerCase()
          const val = raw[1]
          const actual = row[key]
          if (op === '!=' || op === 'not') {
            if (actual == val || String(actual) === String(val)) return false
            continue
          }
          expected = val
        }
        if (expected == null || expected === '') continue
        const actual = row[key]
        if (actual == expected || String(actual) === String(expected)) continue
        // Organization/Contact links may be stored as title in fixtures
        if (
          key === 'organization' &&
          (row.organization_name == expected ||
            row.organization == expected)
        ) {
          continue
        }
        if (
          key === 'company_name' &&
          (row.company_name == expected || row.organization == expected)
        ) {
          continue
        }
        return false
      }
      return true
    })
  }
  return ok(rows)
}

/**
 * Build kanban `data` columns from stages.json + deal/lead rows.
 * Matches crm.api.doc.get_data view_type=kanban shape.
 */
function buildKanbanColumns(fixture, doctype, rows) {
  const stagesPayload = readJson(fixture, 'stages.json', null)
  const stagesMsg = stagesPayload?.message || stagesPayload
  let stages = Array.isArray(stagesMsg) ? stagesMsg : null
  if (!stages?.length) {
    const d = (doctype || '').toLowerCase()
    stages = d.includes('deal') ? DEFAULT_DEAL_STATUSES : DEFAULT_LEAD_STATUSES
  }

  const kanban_fields = dIncludesDeal(doctype)
    ? [
        'organization',
        'deal_value',
        'expected_deal_value',
        'deal_owner',
        'contact',
        'expected_closure_date',
        'next_step',
        'chip',
        'probability',
        'status',
        'modified',
        'last_activity',
      ]
    : ['lead_name', 'organization', 'status', 'lead_owner', 'modified']

  const kanban_columns = []
  const data = []
  for (const stage of stages) {
    const name = stage.name || stage.deal_status
    const columnRows = rows.filter((r) => (r.status || '') === name)
    const kc = {
      name,
      color: stage.color || 'gray',
      position: stage.position,
      type: stage.type || 'Open',
      probability: stage.probability,
      count: stage.count ?? columnRows.length,
      all_count: stage.count ?? columnRows.length,
      total: stage.total,
      period: stage.period,
    }
    kanban_columns.push(kc)
    data.push({ column: kc, fields: kanban_fields, data: columnRows })
  }
  return { data, kanban_columns, kanban_fields }
}

function dIncludesDeal(doctype) {
  const d = (doctype || '').toLowerCase()
  return d.includes('deal') && !d.includes('status')
}

/**
 * crm.api.doc.get_data response. Prefers fixture get_data.json; otherwise
 * synthesizes from reportview-style leads/deals/contacts/organizations.json.
 * Honors request view_type=kanban (parity boards need column-shaped data).
 */
function buildGetData(fixture, doctype, viewsPayload, request = {}) {
  const viewType =
    request.view?.view_type ||
    request.view_type ||
    (typeof request.view === 'string' ? request.view : null) ||
    'list'

  const cached = readJson(fixture, 'get_data.json', null)
  if (cached) {
    const msg = { ...(cached.message || cached) }
    if (viewsPayload?.message && !msg.views?.length) {
      msg.views = viewsPayload.message
    }
    // Prefer synthesizing kanban when the cached fixture is list-shaped.
    if (!(viewType === 'kanban' && msg.view_type !== 'kanban')) {
      return ok(msg)
    }
  }

  const list = listForDoctype(fixture, doctype)
  const payload = list?.message || list || {}
  let rows = rowsFromListPayload(payload)

  const columns = (payload.columns || []).length
    ? payload.columns
    : Object.keys(rows[0] || { name: 1 }).map((key) => ({
        label: key,
        type: 'Data',
        key,
        width: '8rem',
      }))
  const rowKeys = payload.rows || columns.map((c) => c.key || c)

  if (viewType === 'kanban') {
    const { data, kanban_columns, kanban_fields } = buildKanbanColumns(
      fixture,
      doctype,
      rows,
    )
    const stagesPayload = readJson(fixture, 'stages.json', null)
    const metrics = stagesPayload?.metrics || null
    return ok({
      data,
      columns,
      rows: rowKeys,
      fields: kanban_fields.map((fieldname) => ({
        label: fieldname,
        fieldtype: 'Data',
        fieldname,
      })),
      column_field: request.column_field || 'status',
      title_field: dIncludesDeal(doctype) ? 'organization' : 'lead_name',
      kanban_columns,
      kanban_fields,
      group_by_field: null,
      page_length: 20,
      page_length_count: 20,
      is_default: 1,
      views: viewsPayload?.message || [],
      total_count: payload.total_count ?? rows.length,
      row_count: data.length,
      form_script: '',
      list_script: '',
      view_type: 'kanban',
      // Design-capture drag snapshot (06-deals-board PNG/HTML).
      parity_drag:
        fixture === '06-deals-board'
          ? {
              name: 'DEAL-KF',
              from: 'Demo/Making',
              to: 'Negotiation',
              // HTML absolute left: 916 inside .main (x=240) → viewport 916 for fixed.
              left: 916,
              top: 452,
              width: 178,
              insert_after: 0,
              label: 'Moving to Negotiation ·\n70%',
            }
          : null,
      parity_filter_chips: [
        {
          id: 'owner',
          key: 'Owner',
          value: 'Me',
          active: true,
          trailing: 'dismiss',
        },
        {
          id: 'close_date',
          key: 'Close date',
          value: 'This quarter',
          active: false,
          trailing: 'chevron',
        },
      ],
      parity_metrics: metrics?.open_label || 'Open ₹69.3 L · weighted ₹38.6 L',
    })
  }

  return ok({
    data: rows,
    columns,
    rows: rowKeys,
    fields: [],
    column_field: 'status',
    title_field: rows[0]?.lead_name
      ? 'lead_name'
      : rows[0]?.organization_name
        ? 'organization_name'
        : 'name',
    kanban_columns: payload.kanban_columns || [],
    kanban_fields: payload.kanban_fields || [],
    group_by_field: null,
    page_length: 20,
    page_length_count: 20,
    is_default: 1,
    views: viewsPayload?.message || [],
    total_count: payload.total_count ?? rows.length,
    row_count: rows.length,
    form_script: '',
    list_script: '',
    view_type: 'list',
  })
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
      const { dt: rawDt } = resolveDocArgs(post, parsed, doctype)
      const dt = (rawDt || '').toLowerCase()
      if (dt.includes('deal') && !dt.includes('status') && metaDeal) body = metaDeal
      else if (dt.includes('contact') && metaContact) body = metaContact
      else if (
        (dt.includes('organization') || dt.includes('compan')) &&
        metaOrg
      ) {
        body = metaOrg
      } else if (dt.includes('lead') && !dt.includes('status') && meta) {
        body = meta
      } else body = defaultMeta(rawDt || doctype || 'CRM Lead')
    } else if (
      method.includes('get_single_value') ||
      url.includes('get_single_value')
    ) {
      body = ok(1) // setup_completed
    } else if (
      method.includes('get_doc_permissions') ||
      url.includes('get_doc_permissions')
    ) {
      body = ok({
        permissions: {
          read: 1,
          write: 1,
          create: 1,
          delete: 1,
          submit: 0,
          cancel: 0,
          amend: 0,
          print: 1,
          email: 1,
          share: 1,
        },
      })
    } else if (
      method.includes('get_sidepanel_sections') ||
      url.includes('get_sidepanel_sections')
    ) {
      const { dt } = resolveDocArgs(post, parsed, doctype || post.doctype)
      const fromFile = readJson(fixture, 'sidepanel.json', null)
      body = fromFile ? unwrap(fromFile, defaultSidepanel(dt)) : defaultSidepanel(dt)
    } else if (
      method.includes('frappe.client.get') &&
      !method.includes('get_list') &&
      !method.includes('get_count') &&
      !method.includes('get_value') &&
      !method.includes('get_single') &&
      !method.includes('get_doc_permissions')
    ) {
      // frappe.client.get — GET query or POST body; never use method path as name
      const { name, dt } = resolveDocArgs(post, parsed, doctype)
      if ((dt || '').toLowerCase().includes('fcrm settings')) {
        body = ok({
          name: 'FCRM Settings',
          doctype: 'FCRM Settings',
          setup_completed: 1,
          brand_name: 'Astra CRM',
          brand_logo: '',
          favicon: '',
        })
      } else {
        body =
          recordForDoctype(fixture, dt, name) ||
          (name ? ok({ name, doctype: dt }) : ok(null))
      }
    } else if (
      method.includes('crm.api.doc.get_data') ||
      url.includes('crm.api.doc.get_data')
    ) {
      const { dt } = resolveDocArgs(post, parsed, doctype || post.doctype || 'CRM Lead')
      body = buildGetData(fixture, dt || 'CRM Lead', views, post)
    } else if (
      method.includes('frappe.client.get_list') ||
      method.includes('frappe.client.get_count') ||
      method.includes('frappe.desk.reportview.get') ||
      method.includes('frappe.desk.reportview.get_count')
    ) {
      const { dt: listDt } = resolveDocArgs(post, parsed, doctype)
      const effectiveDt = listDt || doctype
      if (method.includes('get_count')) {
        // Prefer parity_count from matching view filters when present
        const viewList = views.message || views || []
        const filters = post.filters || {}
        const filterStr = JSON.stringify(filters)
        let parityHit = null
        if (Array.isArray(viewList)) {
          for (const v of viewList) {
            if (v.parity_count == null) continue
            const vf = v.filters || {}
            // Loose match: empty filters → All leads count
            if (
              (!vf || (Array.isArray(vf) && vf.length === 0) || Object.keys(vf).length === 0) &&
              (Object.keys(filters).length === 0 ||
                (filters.converted === 0 && Object.keys(filters).length === 1))
            ) {
              if (v.name === 'all-leads' || v.is_default) {
                parityHit = v.parity_count
                break
              }
            }
            if (JSON.stringify(vf) === filterStr) {
              parityHit = v.parity_count
              break
            }
            // Match by known view name heuristics
            if (
              (v.name === 'my-open-leads' && filterStr.includes('lead_owner')) ||
              (v.name === 'hot-leads' && filterStr.includes('Hot')) ||
              (v.name === 'response-due' && filterStr.includes('sla_status')) ||
              (v.name === 'unassigned' && filterStr.includes('_assign'))
            ) {
              parityHit = v.parity_count
              break
            }
          }
        }
        if (parityHit != null) {
          body = ok(parityHit)
        } else {
          const listBody = getListResponse(fixture, effectiveDt, post.filters)
          body = ok(
            Array.isArray(listBody.message) ? listBody.message.length : 0,
          )
        }
      } else if (method.includes('frappe.client.get_list')) {
        body = getListResponse(fixture, effectiveDt, post.filters)
      } else {
        // reportview.get keeps keys/values shape
        body =
          listForDoctype(fixture, effectiveDt) ||
          (leads ? unwrap(leads, emptyReportview()) : emptyReportview())
      }
    } else if (
      method.includes('get_timeline') ||
      url.includes('get_record_timeline')
    ) {
      const timeline = readJson(fixture, 'timeline.json', null)
      body = timeline ? unwrap(timeline, ok([])) : ok([])
    } else if (
      method.includes('get_deal_contacts') ||
      url.includes('get_deal_contacts')
    ) {
      const fromContacts = readJson(fixture, 'contacts.json', null)
      const fromDeal = readJson(fixture, 'deal.json', null)
      const rows =
        fromContacts?.message ||
        fromDeal?.message?.contacts ||
        []
      body = ok(rows)
    } else if (
      method.includes('get_linked_deals') ||
      url.includes('get_linked_deals')
    ) {
      // crm.api.contact.get_linked_deals — deal row objects (not reportview)
      const list = getListResponse(fixture, 'CRM Deal', {})
      const rows = Array.isArray(list?.message)
        ? list.message
        : Array.isArray(list)
          ? list
          : []
      body = ok(rows)
    } else if (
      conversations &&
      (method.includes('conversation') || url.includes('conversation'))
    ) {
      // Before activities — url `crm.api.activities.get_conversations` contains "activities"
      body = unwrap(conversations, ok([]))
    } else if (
      method.includes('get_activities') ||
      method.includes('get_events') ||
      (url.includes('activities') && !url.includes('conversation'))
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
  const onboardingSteps = [
    'create_first_lead',
    'connect_your_email',
    'invite_your_team',
    'convert_lead_to_deal',
    'create_first_task',
  ].map((name) => ({ name, completed: true }))
  return `
(() => {
  window.__PARITY__ = { enabled: true, user: '${email}' };
  document.cookie = 'user_id=${email}; path=/';
  document.cookie = 'system_user=yes; path=/';
  document.cookie = 'full_name=${encoded}; path=/';
  document.cookie = 'user_image=; path=/';
  try {
    localStorage.setItem('isSidebarCollapsed', 'false');
    localStorage.setItem('crm_setup_completed', '1');
    localStorage.setItem('onboardingStatus', JSON.stringify({
      '${email}': {
        frappecrm_onboarding_status: ${JSON.stringify(onboardingSteps)}
      }
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
