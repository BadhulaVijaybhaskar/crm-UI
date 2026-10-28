<template>
  <div class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg">
    <AstraPageHeader
      :title="__('Conversations')"
      :description="
        __('Every call, email and note per person, in one timeline. Showing your records.')
      "
    />

    <div
      class="grid min-h-0 flex-1 border-t border-crm-border"
      :class="
        selected
          ? 'lg:grid-cols-[330px_1fr_300px]'
          : 'lg:grid-cols-[330px_1fr]'
      "
    >
      <!-- Thread list -->
      <aside class="flex min-h-0 flex-col border-r border-crm-border bg-crm-card">
        <div class="border-b border-crm-border p-3">
          <AstraInput
            v-model="search"
            :placeholder="__('Search people and records')"
            @update:modelValue="onSearch"
          />
          <div class="mt-2 flex flex-wrap gap-1">
            <button
              v-for="chip in channelChips"
              :key="chip.value"
              type="button"
              class="inline-flex h-7 items-center rounded-full px-2.5 text-crm-meta font-semibold"
              :class="
                channel === chip.value
                  ? 'bg-crm-primary-soft text-crm-primary'
                  : 'bg-crm-muted text-crm-muted-fg'
              "
              @click="setChannel(chip.value)"
            >
              {{ chip.label }}
            </button>
          </div>
        </div>
        <div class="min-h-0 flex-1 overflow-y-auto">
          <div
            v-if="list.loading && !list.data"
            class="px-4 py-6 text-crm-body text-crm-muted-fg"
          >
            {{ __('Loading…') }}
          </div>
          <AstraEmptyState
            v-else-if="!(list.data?.items || []).length"
            :title="__('No conversations yet')"
            :body="
              __(
                'Calls, emails and notes on your leads and deals will appear here.',
              )
            "
          />
          <button
            v-for="item in list.data?.items || []"
            :key="item.id"
            type="button"
            class="grid w-full grid-cols-[30px_1fr] gap-2.5 border-b border-crm-border px-3.5 py-2.5 text-left hover:bg-crm-row-hover"
            :class="{
              'bg-crm-row-selected shadow-[inset_3px_0_0_var(--crm-primary)]':
                selected?.id === item.id,
            }"
            @click="selectThread(item)"
          >
            <AstraAvatar :name="item.title" size="md" />
            <div class="min-w-0">
              <div class="flex items-baseline justify-between gap-2">
                <span class="truncate text-crm-label font-semibold text-crm-fg">
                  {{ item.title }}
                </span>
                <span class="shrink-0 text-crm-micro text-crm-faint">
                  {{ formatTime(item.latest_at) }}
                </span>
              </div>
              <p class="m-0 truncate text-crm-meta text-crm-muted-fg">
                {{ item.subtitle }}
              </p>
              <p class="m-0 mt-0.5 truncate text-crm-caption text-crm-muted-fg">
                {{ item.latest_preview }}
              </p>
              <div class="mt-1.5 flex flex-wrap gap-1">
                <span
                  v-for="ch in item.channels"
                  :key="ch"
                  class="inline-flex h-[18px] items-center rounded px-1.5 text-[10.5px] font-semibold"
                  :class="channelTagClass(ch)"
                >
                  {{ channelLabel(ch) }}
                </span>
              </div>
            </div>
          </button>
        </div>
      </aside>

      <!-- Timeline -->
      <section class="flex min-h-0 flex-col bg-crm-bg">
        <template v-if="selected">
          <header
            class="flex items-start justify-between gap-3 border-b border-crm-border bg-crm-card px-5 py-3"
          >
            <div class="min-w-0">
              <h2 class="m-0 text-crm-dialog font-semibold text-crm-fg">
                {{ thread.data?.meta?.title || selected.title }}
              </h2>
              <p class="m-0 mt-0.5 truncate text-crm-body text-crm-muted-fg">
                {{ thread.data?.meta?.subtitle || selected.subtitle }}
              </p>
            </div>
            <AstraBadge :label="__('Read-only')" tone="mute" />
          </header>

          <div class="min-h-0 flex-1 overflow-y-auto px-5 py-4">
            <div
              v-if="thread.loading && !thread.data"
              class="text-crm-body text-crm-muted-fg"
            >
              {{ __('Loading…') }}
            </div>
            <template v-else>
              <template
                v-for="(group, gi) in groupedEvents"
                :key="group.day"
              >
                <p
                  class="mb-2.5 mt-1 pl-[42px] text-[11px] font-bold uppercase tracking-[0.06em] text-crm-faint"
                  :class="{ 'mt-4': gi > 0 }"
                >
                  {{ group.day }}
                </p>
                <article
                  v-for="(event, ei) in group.events"
                  :key="event.name"
                  class="relative grid grid-cols-[30px_1fr] gap-3 pb-3.5"
                >
                  <div class="relative">
                    <span
                      class="grid size-[30px] place-items-center rounded-lg"
                      :class="eventIconClass(event.channel)"
                    >
                      <component
                        :is="eventIcon(event.channel)"
                        class="size-3.5"
                        aria-hidden="true"
                      />
                    </span>
                    <span
                      v-if="ei < group.events.length - 1 || gi < groupedEvents.length - 1"
                      class="absolute left-[14px] top-[30px] bottom-[-14px] w-[1.5px] bg-crm-border"
                      aria-hidden="true"
                    />
                  </div>
                  <div class="min-w-0">
                    <div class="flex min-h-[30px] items-center gap-2 text-crm-label">
                      <span class="font-semibold text-crm-fg">
                        {{ eventHeading(event) }}
                      </span>
                      <span class="ml-auto text-crm-meta text-crm-faint">
                        {{ formatTime(event.creation) }}
                      </span>
                    </div>
                    <div
                      class="rounded-lg border border-crm-border bg-crm-card px-3 py-2.5 text-crm-label"
                      :class="{
                        'border-crm-warning-soft bg-crm-warning-soft/40':
                          event.channel === 'note',
                      }"
                    >
                      <p class="m-0 whitespace-pre-wrap text-crm-fg">
                        {{ eventBody(event) }}
                      </p>
                      <p
                        v-if="event.channel === 'call' && event.data?.call_summary"
                        class="m-0 mt-1 text-crm-muted-fg"
                      >
                        {{ event.data.call_summary }}
                      </p>
                      <a
                        v-if="
                          event.channel === 'call' &&
                          connectReady &&
                          event.data?.recording_url
                        "
                        :href="event.data.recording_url"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="mt-2 inline-flex items-center gap-1 text-crm-meta font-semibold text-crm-primary hover:underline"
                      >
                        {{ __('Recording & transcript in Astra Connect') }}
                        <LucideExternalLink class="size-3" aria-hidden="true" />
                      </a>
                    </div>
                  </div>
                </article>
              </template>
              <AstraEmptyState
                v-if="!(thread.data?.events || []).length"
                :title="__('No activity in this thread')"
                :body="__('Activity on this record will show up here.')"
              />
            </template>
          </div>

          <footer
            class="flex flex-wrap items-center justify-between gap-2 border-t border-crm-border bg-crm-muted px-5 py-2.5"
          >
            <p class="m-0 text-crm-caption text-crm-muted-fg">
              {{
                __(
                  'Read-only — replies and WhatsApp open in Astra Connect',
                )
              }}
            </p>
            <AstraButton
              v-if="connectReady"
              variant="primary"
              size="sm"
              :label="__('Open in Astra Connect')"
              @click="openReply"
            />
          </footer>
        </template>
        <AstraEmptyState
          v-else
          :title="__('Select a conversation')"
          :body="__('Pick someone on the left to see their timeline.')"
        />
      </section>

      <!-- Detail -->
      <aside
        v-if="selected && thread.data"
        class="hidden min-h-0 overflow-y-auto border-l border-crm-border bg-crm-card lg:block"
      >
        <div class="border-b border-crm-border px-4 py-3">
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <p class="m-0 text-crm-caps font-bold uppercase tracking-crm-caps text-crm-faint">
                {{ __('Linked record') }}
              </p>
              <p class="m-0 mt-1 truncate text-crm-label font-semibold text-crm-fg">
                {{ linkedRecordTitle }}
              </p>
              <p
                v-if="thread.data.meta?.status"
                class="m-0 mt-0.5 text-crm-meta text-crm-muted-fg"
              >
                {{ thread.data.meta.status }}
                <span v-if="thread.data.meta.value != null">
                  · {{ formatCompactCurrency(thread.data.meta.value) }}
                </span>
              </p>
            </div>
            <router-link
              v-if="thread.data.meta?.route"
              :to="thread.data.meta.route"
              class="shrink-0 text-crm-meta font-semibold text-crm-primary hover:underline"
            >
              {{ __('Open record') }}
            </router-link>
          </div>
          <p
            v-if="thread.data.next_task"
            class="mt-3 rounded-lg bg-crm-primary-soft px-2.5 py-2 text-crm-meta font-semibold text-crm-primary"
          >
            {{ thread.data.next_task.title }}
            <span v-if="thread.data.next_task.due_date" class="font-normal">
              · {{ __('due') }}
              {{ formatDate(thread.data.next_task.due_date, 'D MMM') }}
            </span>
          </p>
        </div>
        <AstraSidePanelSection :title="__('Contact')" :entries="contactEntries" />
        <AstraSidePanelSection
          :title="__('In this thread')"
          :entries="threadCountEntries"
        />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { createResource, usePageMeta } from 'frappe-ui'
import LucidePhone from '~icons/lucide/phone'
import LucideMail from '~icons/lucide/mail'
import LucideStickyNote from '~icons/lucide/sticky-note'
import LucideMessageCircle from '~icons/lucide/message-circle'
import LucideExternalLink from '~icons/lucide/external-link'
import {
  AstraAvatar,
  AstraBadge,
  AstraButton,
  AstraEmptyState,
  AstraInput,
  AstraPageHeader,
  AstraSidePanelSection,
} from '@/components/astra'
import { formatCompactCurrency } from '@/utils/compactCurrency'
import { formatDate, sanitizeHTML } from '@/utils'
import {
  isAstraConnectConfigured,
  openConnectCompose,
} from '@/utils/astraConnect'
import { getSettings } from '@/stores/settings'
import { ASTRA_FAVICON } from '@/assets/brand'

const { brand } = getSettings()
const channel = ref('all')
const search = ref('')
const selected = ref(null)
let searchTimer = null

const list = createResource({
  url: 'crm.api.conversations.get_conversations',
  auto: true,
  cache: ['crm-conversations', channel],
  makeParams: () => ({
    channel: channel.value,
    search: search.value || null,
  }),
})

const thread = createResource({
  url: 'crm.api.conversations.get_conversation_thread',
  auto: false,
  makeParams: () => ({
    reference_doctype: selected.value?.reference_doctype,
    reference_docname: selected.value?.reference_docname,
  }),
})

const connectReady = computed(() => isAstraConnectConfigured())

const channelChips = computed(() => {
  const available = list.data?.available_channels || ['call', 'email', 'note']
  const chips = [{ value: 'all', label: __('All') }]
  const labels = {
    call: __('Calls'),
    email: __('Emails'),
    note: __('Notes'),
    whatsapp: __('WhatsApp'),
  }
  for (const ch of available) {
    chips.push({ value: ch, label: labels[ch] || ch })
  }
  return chips
})

const groupedEvents = computed(() => {
  const events = thread.data?.events || []
  const groups = []
  let current = null
  for (const event of events) {
    const day = dayLabel(event.creation)
    if (!current || current.day !== day) {
      current = { day, events: [] }
      groups.push(current)
    }
    current.events.push(event)
  }
  return groups
})

const linkedRecordTitle = computed(() => {
  const meta = thread.data?.meta || {}
  if (selected.value?.reference_doctype === 'CRM Deal') {
    return meta.organization || meta.title || selected.value.title
  }
  return meta.organization
    ? `${meta.title} · ${meta.organization}`
    : meta.title || selected.value?.title
})

const contactEntries = computed(() => {
  const meta = thread.data?.meta || {}
  const rows = []
  if (meta.email) rows.push({ label: __('Email'), value: meta.email })
  if (meta.mobile_no) rows.push({ label: __('Mobile'), value: meta.mobile_no })
  if (meta.owner) rows.push({ label: __('Owner'), value: meta.owner })
  return rows
})

const threadCountEntries = computed(() => {
  const counts = thread.data?.channel_counts || {}
  const rows = []
  if (counts.call) rows.push({ label: __('Calls'), value: String(counts.call) })
  if (counts.email) rows.push({ label: __('Emails'), value: String(counts.email) })
  if (counts.note) rows.push({ label: __('Notes'), value: String(counts.note) })
  if (counts.whatsapp) {
    rows.push({
      label: __('WhatsApp'),
      value: `${counts.whatsapp} · ${__('via Astra Connect')}`,
    })
  }
  return rows
})

watch(
  () => list.data?.items,
  (items) => {
    if (!items?.length) {
      selected.value = null
      return
    }
    if (!selected.value || !items.find((i) => i.id === selected.value.id)) {
      selectThread(items[0])
    }
  },
)

function setChannel(value) {
  channel.value = value
  list.reload()
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => list.reload(), 250)
}

function selectThread(item) {
  selected.value = item
  thread.reload()
}

function channelLabel(ch) {
  return (
    {
      call: __('Call'),
      email: __('Email'),
      note: __('Note'),
      whatsapp: __('WhatsApp'),
    }[ch] || ch
  )
}

function channelTagClass(ch) {
  return (
    {
      call: 'bg-crm-teal-soft text-crm-teal',
      email: 'bg-crm-blue-soft text-crm-blue',
      note: 'bg-crm-warning-soft text-crm-warning',
      whatsapp: 'bg-crm-success-soft text-crm-success',
    }[ch] || 'bg-crm-neutral-soft text-crm-muted-fg'
  )
}

function eventIcon(ch) {
  return (
    {
      call: LucidePhone,
      email: LucideMail,
      note: LucideStickyNote,
      whatsapp: LucideMessageCircle,
    }[ch] || LucideStickyNote
  )
}

function eventIconClass(ch) {
  return (
    {
      call: 'bg-crm-teal-soft text-crm-teal',
      email: 'bg-crm-blue-soft text-crm-blue',
      note: 'bg-crm-warning-soft text-crm-warning',
      whatsapp: 'bg-crm-success-soft text-crm-success',
    }[ch] || 'bg-crm-neutral-soft text-crm-muted-fg'
  )
}

function eventHeading(event) {
  if (event.channel === 'call') {
    const type = event.data?.type || ''
    const status = event.data?.status || ''
    return [type, __('call'), status ? `· ${status}` : ''].filter(Boolean).join(' ')
  }
  if (event.channel === 'email') {
    return event.data?.subject || __('Email')
  }
  if (event.channel === 'note') {
    return event.data?.title || __('Note')
  }
  if (event.channel === 'whatsapp') {
    const dir = (event.data?.direction || '').toLowerCase()
    return dir === 'incoming' ? __('WhatsApp · Incoming') : __('WhatsApp · Outgoing')
  }
  return channelLabel(event.channel)
}

function eventBody(event) {
  if (event.channel === 'call') {
    return (
      event.data?.outcome ||
      event.preview ||
      [event.data?.type, event.data?.status].filter(Boolean).join(' · ')
    )
  }
  if (event.channel === 'email') {
    return strip(event.data?.content || event.preview)
  }
  if (event.channel === 'note') {
    return strip(event.data?.content || event.preview)
  }
  if (event.channel === 'whatsapp') {
    return event.data?.message || event.preview
  }
  return event.preview || ''
}

function strip(html) {
  if (!html) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = sanitizeHTML(html)
  return (tmp.textContent || '').trim()
}

function dayLabel(ts) {
  if (!ts) return ''
  const d = formatDate(ts, 'YYYY-MM-DD')
  const today = formatDate(new Date(), 'YYYY-MM-DD')
  const yesterday = formatDate(
    new Date(Date.now() - 86400000),
    'YYYY-MM-DD',
  )
  if (d === today) return __('Today')
  if (d === yesterday) return __('Yesterday')
  return formatDate(ts, 'D MMM YYYY').toUpperCase()
}

function formatTime(ts) {
  if (!ts) return ''
  return formatDate(ts, 'HH:mm')
}

function openReply() {
  if (!selected.value || !connectReady.value) return
  openConnectCompose('messages', {
    recordType: selected.value.reference_doctype,
    recordId: selected.value.reference_docname,
    phone: thread.data?.meta?.mobile_no || selected.value.mobile_no,
  })
}

usePageMeta(() => ({
  title: __('Conversations'),
  icon: brand?.favicon || ASTRA_FAVICON,
}))
</script>
