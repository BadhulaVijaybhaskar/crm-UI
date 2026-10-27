import { computed, ref, watch } from 'vue'
import { createListResource, createResource } from 'frappe-ui'

/**
 * Read-only conversations from Call Log + Communication (+ notes via feed).
 * No WhatsApp compose — Connect handles messaging.
 */
export function useConversations() {
  const channel = ref('all')
  const selectedId = ref(null)

  const callLogs = createListResource({
    doctype: 'CRM Call Log',
    fields: [
      'name',
      'creation',
      'type',
      'status',
      'duration',
      'from',
      'to',
      'caller',
      'receiver',
      'reference_doctype',
      'reference_docname',
      'outcome',
      'call_summary',
      'modified',
    ],
    orderBy: 'creation desc',
    pageLength: 40,
    auto: true,
    cache: 'astra-conversations-calls',
  })

  const emails = createListResource({
    doctype: 'Communication',
    fields: [
      'name',
      'creation',
      'subject',
      'sender',
      'recipients',
      'content',
      'communication_medium',
      'reference_doctype',
      'reference_name',
      'sent_or_received',
      'modified',
    ],
    filters: {
      communication_medium: 'Email',
      reference_doctype: ['in', ['CRM Lead', 'CRM Deal', 'Contact']],
    },
    orderBy: 'creation desc',
    pageLength: 40,
    auto: true,
    cache: 'astra-conversations-emails',
  })

  const notes = createListResource({
    doctype: 'FCRM Note',
    fields: [
      'name',
      'title',
      'content',
      'creation',
      'owner',
      'reference_doctype',
      'reference_docname',
      'modified',
    ],
    filters: {
      reference_doctype: ['in', ['CRM Lead', 'CRM Deal', 'Contact']],
    },
    orderBy: 'creation desc',
    pageLength: 40,
    auto: true,
    cache: 'astra-conversations-notes',
  })

  const threads = computed(() => {
    const rows = []

    for (const c of callLogs.data || []) {
      rows.push({
        id: `call-${c.name}`,
        channel: 'calls',
        kind: 'call',
        name: c.name,
        title: c.reference_docname || c.to || c.from || c.name,
        snippet: [c.type, c.status, c.outcome].filter(Boolean).join(' · '),
        creation: c.creation,
        reference_doctype: c.reference_doctype,
        reference_docname: c.reference_docname,
        raw: c,
      })
    }

    for (const e of emails.data || []) {
      rows.push({
        id: `email-${e.name}`,
        channel: 'emails',
        kind: 'email',
        name: e.name,
        title:
          e.reference_name ||
          e.sender ||
          e.subject ||
          e.name,
        snippet: e.subject || __('Email'),
        creation: e.creation,
        reference_doctype: e.reference_doctype,
        reference_docname: e.reference_name,
        raw: e,
      })
    }

    for (const n of notes.data || []) {
      rows.push({
        id: `note-${n.name}`,
        channel: 'notes',
        kind: 'note',
        name: n.name,
        title: n.reference_docname || n.title || n.name,
        snippet: n.title || __('Note'),
        creation: n.creation,
        reference_doctype: n.reference_doctype,
        reference_docname: n.reference_docname,
        raw: n,
      })
    }

    rows.sort((a, b) => String(b.creation).localeCompare(String(a.creation)))
    return rows
  })

  const filteredThreads = computed(() => {
    if (channel.value === 'all') return threads.value
    if (channel.value === 'calls')
      return threads.value.filter((t) => t.channel === 'calls')
    if (channel.value === 'emails')
      return threads.value.filter((t) => t.channel === 'emails')
    if (channel.value === 'whatsapp') return []
    return threads.value
  })

  const selected = computed(
    () =>
      filteredThreads.value.find((t) => t.id === selectedId.value) ||
      filteredThreads.value[0] ||
      null,
  )

  watch(filteredThreads, (list) => {
    if (!list.length) {
      selectedId.value = null
      return
    }
    if (!list.some((t) => t.id === selectedId.value)) {
      selectedId.value = list[0].id
    }
  })

  const recordActivities = createResource({
    url: 'crm.api.activities.get_activities',
    auto: false,
    makeParams: () => {
      const sel = selected.value
      if (!sel?.reference_doctype || !sel?.reference_docname) return null
      return {
        name: sel.reference_docname,
        doctype: sel.reference_doctype,
      }
    },
    transform: ([versions, calls, notesList, tasks, attachments]) => ({
      versions,
      calls,
      notes: notesList,
      tasks,
      attachments,
    }),
  })

  const contactPanel = createResource({
    url: 'frappe.client.get',
    auto: false,
    makeParams: () => {
      const sel = selected.value
      if (!sel?.reference_doctype || !sel?.reference_docname) return null
      return {
        doctype: sel.reference_doctype,
        name: sel.reference_docname,
      }
    },
  })

  watch(
    selected,
    (sel) => {
      if (!sel?.reference_doctype || !sel?.reference_docname) {
        recordActivities.reset?.()
        contactPanel.reset?.()
        return
      }
      recordActivities.reload()
      contactPanel.reload()
    },
    { immediate: true },
  )

  const conversationMessages = computed(() => {
    const sel = selected.value
    if (!sel) return []

    const payload = recordActivities.data
    const msgs = []

    if (payload) {
      for (const call of payload.calls || []) {
        msgs.push({
          id: `call-${call.name}`,
          kind:
            call.type === 'Incoming' || call.activity_type === 'incoming_call'
              ? 'incoming_call'
              : 'outgoing_call',
          creation: call.creation,
          data: call,
          owner: call.caller || call.owner,
        })
      }
      for (const a of payload.versions || []) {
        if (['communication', 'note', 'whatsapp'].includes(a.activity_type)) {
          msgs.push({
            id: `${a.activity_type}-${a.name || a.creation}`,
            kind: a.activity_type,
            creation: a.creation,
            data: a.data || a,
            owner: a.owner,
          })
        }
      }
      for (const n of payload.notes || []) {
        msgs.push({
          id: `note-${n.name}`,
          kind: 'note',
          creation: n.creation || n.modified,
          data: n,
          owner: n.owner,
        })
      }
    }

    if (msgs.length) {
      msgs.sort((a, b) => String(a.creation).localeCompare(String(b.creation)))
      return msgs
    }

    // Fallback: selected item only (no linked record timeline)
    if (sel.kind === 'call') {
      return [
        {
          id: sel.id,
          kind: sel.raw.type === 'Incoming' ? 'incoming_call' : 'outgoing_call',
          creation: sel.creation,
          data: sel.raw,
          owner: sel.raw.caller || sel.raw.owner,
        },
      ]
    }
    if (sel.kind === 'email') {
      return [
        {
          id: sel.id,
          kind: 'communication',
          creation: sel.creation,
          data: {
            subject: sel.raw.subject,
            content: sel.raw.content,
            sender: sel.raw.sender,
            sent_or_received: sel.raw.sent_or_received,
          },
          owner: sel.raw.sender,
        },
      ]
    }
    if (sel.kind === 'note') {
      return [
        {
          id: sel.id,
          kind: 'note',
          creation: sel.creation,
          data: { title: sel.raw.title, content: sel.raw.content },
          owner: sel.raw.owner,
        },
      ]
    }
    return []
  })

  const panelDoc = computed(() => contactPanel.data || null)

  const loading = computed(
    () => callLogs.loading || emails.loading || notes.loading,
  )

  return {
    channel,
    selectedId,
    threads: filteredThreads,
    selected,
    conversationMessages,
    panelDoc,
    contactPanel,
    recordActivities,
    loading,
    resources: { callLogs, emails, notes },
  }
}
