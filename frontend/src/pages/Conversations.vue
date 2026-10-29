<template>
  <div
    class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg [text-rendering:geometricPrecision]"
  >
    <header class="flex shrink-0 items-center gap-3 px-crm-page-x pb-3.5 pt-[19px]">
      <div class="min-w-0">
        <h1
          class="m-0 text-[20px] font-semibold leading-[1.45] tracking-[-0.015em] text-crm-fg"
        >
          {{ __('Conversations') }}
        </h1>
        <p
          class="relative top-px m-0 -mt-px text-[13px] leading-[1.45] tracking-[-0.005em] text-crm-muted-fg"
        >
          {{
            __(
              'Every call, email and note per person, in one timeline. Showing your records.',
            )
          }}
        </p>
      </div>
    </header>

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
        <div class="shrink-0 px-3.5 pb-2 pt-2.5">
          <label
            class="flex h-8 items-center gap-2 rounded-crm-control border border-crm-border-strong bg-crm-card px-[11px]"
          >
            <LucideSearch class="size-3.5 shrink-0 text-crm-faint" aria-hidden="true" />
            <input
              v-model="search"
              type="search"
              class="min-w-0 flex-1 border-0 bg-transparent p-0 text-[12.5px] text-crm-fg outline-none placeholder:text-crm-faint"
              :placeholder="__('Search people and records')"
              :aria-label="__('Search people and records')"
              @input="onSearch"
            />
          </label>
          <div
            class="mt-2.5 flex h-[34px] items-center gap-0.5 rounded-crm-panel border border-crm-border bg-crm-muted p-[3px]"
            role="tablist"
          >
            <button
              v-for="chip in channelChips"
              :key="chip.value"
              type="button"
              role="tab"
              :aria-selected="channel === chip.value"
              class="inline-flex h-7 flex-1 items-center justify-center rounded-crm-control px-2.5 pb-1 text-[12.5px]"
              :class="
                channel === chip.value
                  ? 'border border-crm-border bg-crm-card font-semibold text-crm-fg'
                  : 'font-medium text-crm-muted-fg'
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
            class="grid h-[103.6px] w-full grid-cols-[26px_1fr] gap-3.5 border-t border-crm-border px-3.5 text-left"
            :class="[
              'pt-[11px]',
              selected?.id === item.id
                ? 'bg-crm-row-selected shadow-[inset_3px_0_0_var(--crm-primary)]'
                : 'hover:bg-crm-row-hover',
            ]"
            @click="selectThread(item)"
          >
            <span
              class="mt-px flex size-[26px] items-center justify-center rounded-full bg-crm-primary-soft text-[10px] font-bold text-crm-primary"
              aria-hidden="true"
            >
              {{ initialsFrom(item.title) }}
            </span>
            <div class="min-w-0 leading-[1.45]">
              <div class="flex items-baseline justify-between gap-2">
                <b class="truncate text-[13px] font-semibold text-crm-fg">
                  {{ item.title }}
                </b>
                <span class="shrink-0 text-[11.5px] text-crm-faint">
                  {{ listTimeLabel(item.latest_at) }}
                </span>
              </div>
              <p class="m-0 mt-[3px] truncate text-[12px] text-crm-muted-fg">
                {{ item.subtitle }}
              </p>
              <p class="m-0 mt-px truncate text-[12px] text-crm-fg">
                {{ previewLine(item) }}
              </p>
              <div class="mt-[3px] flex flex-wrap gap-1">
                <span
                  v-for="ch in item.channels"
                  :key="ch"
                  class="inline-flex h-5 items-center gap-1 rounded-[5px] px-1.5 text-[10.5px] font-semibold"
                  :class="channelTagClass(ch)"
                >
                  <component :is="eventIcon(ch)" class="size-3" aria-hidden="true" />
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
            class="flex h-[62px] shrink-0 items-center gap-2.5 border-b border-crm-border bg-crm-card pl-[18px] pr-5 pt-0.5"
          >
            <span
              class="flex size-7 shrink-0 items-center justify-center rounded-full bg-crm-primary-soft text-[10px] font-bold text-crm-primary"
              aria-hidden="true"
            >
              {{ initialsFrom(thread.data?.meta?.title || selected.title) }}
            </span>
            <div class="min-w-0 leading-[1.45]">
              <h2 class="m-0 truncate text-[14px] font-semibold text-crm-fg">
                {{ thread.data?.meta?.title || selected.title }}
              </h2>
              <p class="m-0 truncate text-[12.5px] text-crm-muted-fg">
                {{ thread.data?.meta?.subtitle || selected.subtitle }}
              </p>
            </div>
            <div class="flex-1" />
            <AstraBadge :label="__('Read-only')" tone="mute" />
          </header>

          <div class="min-h-0 flex-1 overflow-y-auto px-5 pb-4 pt-4">
            <div
              v-if="thread.loading && !thread.data"
              class="text-crm-body text-crm-muted-fg"
            >
              {{ __('Loading…') }}
            </div>
            <template v-else>
              <template v-for="group in groupedEvents" :key="group.day">
                <p
                  class="m-0 mb-3 text-center text-[11px] font-bold uppercase leading-[1.45] tracking-[0.06em] text-crm-faint"
                >
                  {{ group.day }}
                </p>
                <article
                  v-for="event in group.events"
                  :key="event.name"
                  class="mb-[13px] rounded-crm-card border px-3 py-2.5 text-[12.5px] leading-[1.45]"
                  :class="[
                    isOutgoing(event)
                      ? 'ml-auto w-fit max-w-full border-crm-border bg-crm-primary-soft'
                      : 'w-full border-crm-border bg-crm-card',
                    event.channel !== 'call' && (isOutgoing(event) ? '!pb-[8px]' : '!pb-[7px]'),
                  ]"
                >
                  <div class="mb-[5.5px] flex items-center gap-2">
                    <span
                      class="inline-flex h-[18px] items-center gap-1 rounded-[5px] px-1.5 text-[10.5px] font-semibold"
                      :class="channelTagClass(event.channel)"
                    >
                      <component
                        :is="eventChipIcon(event)"
                        class="size-3"
                        aria-hidden="true"
                      />
                      {{ eventChipLabel(event) }}
                    </span>
                    <span class="text-[12px] text-crm-muted-fg">
                      {{ eventMeta(event) }}
                    </span>
                  </div>
                  <p
                    v-if="event.channel === 'call'"
                    class="m-0 pt-0.5 font-semibold text-crm-fg"
                  >
                    {{ __('Outcome') }} · {{ eventBody(event) }}
                  </p>
                  <p
                    v-else
                    class="m-0 whitespace-pre-wrap text-crm-fg"
                    :class="isOutgoing(event) ? 'pt-[2px]' : 'pt-[3px]'"
                  >
                    {{ eventBody(event) }}
                  </p>
                  <p
                    v-if="event.channel === 'call' && event.data?.call_summary"
                    class="m-0 pt-px text-crm-muted-fg"
                  >
                    {{ event.data.call_summary }}
                  </p>
                  <a
                    v-if="
                      event.channel === 'call' &&
                      connectReady &&
                      (event.data?.recording_url || event.data?.has_recording)
                    "
                    :href="event.data.recording_url || undefined"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="mt-1.5 flex w-fit items-center gap-1.5 text-[12.5px] font-semibold text-crm-primary hover:underline"
                  >
                    <LucidePlay class="size-3.5" aria-hidden="true" />
                    {{ __('Recording & transcript in Astra Connect') }}
                    <LucideExternalLink class="size-3.5" aria-hidden="true" />
                  </a>
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
            class="flex h-[55px] shrink-0 items-center gap-3 border-t border-crm-border bg-crm-card px-5"
          >
            <LucideEye class="size-3.5 shrink-0 text-crm-faint" aria-hidden="true" />
            <p class="m-0 max-w-[290px] text-[12px] leading-[1.45] text-crm-muted-fg">
              {{ __('Read-only · replies and WhatsApp open in Astra Connect') }}
            </p>
            <div class="flex-1" />
            <AstraButton
              v-if="connectReady"
              size="sm"
              :label="__('Open in Astra Connect')"
              @click="openReply"
            >
              <template #prefix>
                <LucideExternalLink class="size-3.5" aria-hidden="true" />
              </template>
            </AstraButton>
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
        <div class="border-b border-crm-border px-4 pb-[10px] pt-3">
          <div class="flex items-center justify-between gap-2">
            <p class="m-0 text-[12.5px] font-semibold text-crm-fg">
              {{ __('Linked record') }}
            </p>
            <router-link
              v-if="thread.data.meta?.route"
              :to="thread.data.meta.route"
              class="shrink-0 text-[12.5px] font-semibold text-crm-primary hover:underline"
            >
              {{ __('Open record') }}
            </router-link>
          </div>
          <p class="m-0 mt-3.5 truncate text-[13.2px] font-semibold text-crm-fg">
            {{ linkedRecordTitle }}
          </p>
          <div v-if="thread.data.meta?.status" class="mt-1.5 flex items-center gap-2">
            <span
              class="inline-flex h-[22px] items-center gap-1.5 rounded-crm-chip bg-crm-neutral-soft px-2 text-[11.5px] font-semibold text-crm-fg"
            >
              <i
                class="block size-1.5 rounded-[2px]"
                :style="{ background: `var(--crm-${stageToken(thread.data.meta.status)})` }"
              />
              {{ thread.data.meta.status }}
            </span>
            <b
              v-if="thread.data.meta.value != null"
              class="text-[13px] font-semibold text-crm-fg"
            >
              {{ valueLabel }}
            </b>
          </div>
          <p v-if="nextStepLabel" class="m-0 mt-[9px] text-[12px] text-crm-muted-fg">
            {{ nextStepLabel }}
          </p>
        </div>
        <section class="border-b border-crm-border px-4 pb-3 pt-3.5">
          <h3 class="m-0 text-[12.5px] font-semibold text-crm-fg">{{ __('Contact') }}</h3>
          <dl
            class="m-0 mt-[13px] grid grid-cols-[116px_1fr] gap-x-3 gap-y-2 text-[12.5px] leading-[18px]"
          >
            <template v-for="entry in contactEntries" :key="entry.label">
              <dt class="text-crm-muted-fg">{{ entry.label }}</dt>
              <dd class="m-0 truncate font-medium text-crm-fg">{{ entry.value }}</dd>
            </template>
          </dl>
        </section>
        <section class="px-4 pb-3.5 pt-3.5">
          <h3 class="m-0 text-[12.5px] font-semibold text-crm-fg">
            {{ __('In this thread') }}
          </h3>
          <dl
            class="m-0 mt-2.5 grid grid-cols-[116px_1fr] gap-x-3 gap-y-2 text-[12.5px] leading-[18px]"
          >
            <template v-for="entry in threadCountEntries" :key="entry.label">
              <dt class="text-crm-muted-fg">{{ entry.label }}</dt>
              <dd class="m-0 truncate font-medium text-crm-fg">{{ entry.value }}</dd>
            </template>
          </dl>
        </section>
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
import LucideEye from '~icons/lucide/eye'
import LucidePlay from '~icons/lucide/play'
import LucideSearch from '~icons/lucide/search'
import LucideArrowUpRight from '~icons/lucide/arrow-up-right'
import LucideArrowDownLeft from '~icons/lucide/arrow-down-left'
import { AstraBadge, AstraButton, AstraEmptyState } from '@/components/astra'
import { initialsFrom, stageToken } from '@/components/astra/format'
import { usersStore } from '@/stores/users'
import { formatDate, sanitizeHTML } from '@/utils'
import {
  isAstraConnectConfigured,
  openConnectCompose,
} from '@/utils/astraConnect'
import { getSettings } from '@/stores/settings'
import { ASTRA_FAVICON } from '@/assets/brand'

const { brand } = getSettings()
const { getUser } = usersStore()
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
    const base = meta.organization || meta.title || selected.value.title
    return meta.deal_title ? `${base} · ${meta.deal_title}` : base
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
  const owner = meta.owner_name || (meta.owner && getUser(meta.owner)?.full_name) || meta.owner
  if (owner) rows.push({ label: __('Owner'), value: owner })
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

function listTimeLabel(ts) {
  if (!ts) return ''
  const d = formatDate(ts, 'YYYY-MM-DD')
  const today = formatDate(new Date(), 'YYYY-MM-DD')
  if (d === today) {
    const time = formatDate(ts, 'HH:mm')
    return time === '00:00' ? __('Today') : time
  }
  const yesterday = formatDate(new Date(Date.now() - 86400000), 'YYYY-MM-DD')
  if (d === yesterday) return __('Yesterday')
  return formatDate(ts, 'D MMM')
}

function previewLine(item) {
  const label = channelLabel(item.latest_channel)
  return item.latest_preview ? `${label} · ${item.latest_preview}` : label
}

function isOutgoing(event) {
  if (event.channel === 'call') return true
  if (event.channel === 'note') return true
  const dir = (event.data?.direction || event.data?.type || '').toLowerCase()
  return dir === 'outgoing'
}

function eventChipIcon(event) {
  if (event.channel === 'call') {
    return (event.data?.type || '').toLowerCase() === 'incoming'
      ? LucideArrowDownLeft
      : LucideArrowUpRight
  }
  return eventIcon(event.channel)
}

function eventChipLabel(event) {
  if (event.channel === 'call') {
    const type = (event.data?.type || '').toLowerCase() === 'incoming' ? __('Incoming') : __('Outgoing')
    return `${type} ${__('call')}`
  }
  return channelLabel(event.channel)
}

function eventMeta(event) {
  const time = formatTime(event.creation)
  if (event.channel === 'whatsapp') {
    const outgoing = isOutgoing(event)
    return outgoing
      ? [__('Outgoing'), event.data?.sender_name, time].filter(Boolean).join(' · ')
      : [__('Incoming'), time].join(' · ')
  }
  if (event.channel === 'call') {
    const who = event.data?.caller?.label || event.data?.caller
    return [typeof who === 'string' ? who : '', time, event.data?.duration_label]
      .filter(Boolean)
      .join(' · ')
  }
  if (event.channel === 'note') {
    return [event.data?.owner_name, time].filter(Boolean).join(' · ')
  }
  return [event.data?.subject, time].filter(Boolean).join(' · ')
}

const valueLabel = computed(() => {
  const meta = thread.data?.meta || {}
  if (meta.value == null) return ''
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: window.sysdefaults?.currency || 'INR',
    maximumFractionDigits: 0,
  }).format(meta.value)
})

const nextStepLabel = computed(() => {
  const task = thread.data?.next_task
  if (!task?.title) return ''
  let due = ''
  if (task.due_date) {
    const same = formatDate(task.due_date, 'YYYY-MM-DD') === formatDate(new Date(), 'YYYY-MM-DD')
    due = same ? __('due today') : `${__('due')} ${formatDate(task.due_date, 'D MMM')}`
  }
  return [__('Next step'), task.title, due].filter(Boolean).join(' · ')
})

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
