<template>
  <div class="astra-bento flex h-full min-h-0 flex-col overflow-hidden">
    <div class="grid min-h-0 flex-1 grid-cols-1 gap-3 overflow-hidden p-3 lg:grid-cols-12">
      <!-- Conversations list -->
      <AstraCard
        class="flex min-h-0 flex-col overflow-hidden lg:col-span-3"
        :title="__('Conversations')"
        flush
      >
        <div class="border-b border-[var(--astra-border)] px-4 pb-3 pt-4">
          <h2 class="astra-card__title">{{ __('Conversations') }}</h2>
          <div
            class="mt-3 flex flex-wrap gap-1.5"
            role="tablist"
            :aria-label="__('Conversation channel filters')"
          >
            <button
              v-for="pill in channelPills"
              :key="pill.value"
              type="button"
              role="tab"
              class="astra-pill"
              :class="{ 'astra-pill--active': channel === pill.value }"
              :aria-selected="channel === pill.value"
              @click="channel = pill.value"
            >
              {{ __(pill.label) }}
            </button>
          </div>
        </div>

        <div class="min-h-0 flex-1 overflow-y-auto px-2 py-2">
          <div v-if="loading" class="astra-muted px-2 py-3 text-sm">
            {{ __('Loading…') }}
          </div>
          <AstraEmptyState
            v-else-if="!threads.length"
            class="px-2 py-3"
            :title="__('No conversations yet')"
            :body="__(
              'Call logs, emails and notes linked to leads, deals or contacts will appear here.',
            )"
          />
          <ul v-else role="list" class="flex flex-col gap-1">
            <li v-for="thread in threads" :key="thread.id">
              <button
                type="button"
                class="flex w-full items-start gap-2.5 rounded-[12px] px-2 py-2.5 text-left transition-colors duration-150"
                :class="
                  selected?.id === thread.id
                    ? 'bg-[color-mix(in_srgb,var(--astra-primary)_10%,transparent)] ring-1 ring-[var(--astra-primary)]/40'
                    : 'hover:bg-[color-mix(in_srgb,var(--astra-muted)_8%,transparent)]'
                "
                :aria-current="selected?.id === thread.id ? 'true' : undefined"
                @click="selectedId = thread.id"
              >
                <AstraAvatar :name="thread.title" :seed="thread.id" size="sm" />
                <div class="min-w-0 flex-1">
                  <div class="flex items-baseline justify-between gap-2">
                    <p class="truncate text-sm font-semibold text-[var(--astra-text)]">
                      {{ thread.title }}
                    </p>
                    <span class="astra-muted shrink-0 text-[11px]">
                      {{ formatTime(thread.creation) }}
                    </span>
                  </div>
                  <p class="astra-muted mt-0.5 truncate text-xs">
                    <span class="font-medium">{{ channelLabel(thread.channel) }}</span>
                    · {{ thread.snippet }}
                  </p>
                </div>
              </button>
            </li>
          </ul>
        </div>
      </AstraCard>

      <!-- Conversation -->
      <AstraCard
        class="flex min-h-0 flex-col overflow-hidden lg:col-span-6"
        flush
      >
        <div class="border-b border-[var(--astra-border)] px-4 py-3">
          <h2 class="text-base font-bold text-[var(--astra-text)]">
            {{ conversationTitle }}
          </h2>
          <p class="astra-muted text-xs">
            {{ __('Read-only · calls, emails and notes') }}
          </p>
        </div>

        <div class="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-4">
          <AstraEmptyState
            v-if="!selected"
            :title="__('Select a conversation')"
            :body="__('Choose a thread from Conversations to review the history.')"
          />
          <template v-else>
            <div
              v-for="msg in conversationMessages"
              :key="msg.id"
              class="flex"
              :class="isOutgoing(msg) ? 'justify-end' : 'justify-start'"
            >
              <div
                v-if="isCall(msg)"
                class="w-full max-w-xl rounded-[12px] border border-[var(--astra-border)] bg-[color-mix(in_srgb,var(--astra-card)_100%,transparent)] p-3"
              >
                <div class="flex flex-wrap items-center gap-2">
                  <span class="text-sm font-semibold text-[var(--astra-text)]">
                    {{ callHeading(msg) }}
                  </span>
                  <span
                    v-if="msg.data?.outcome || msg.data?.qualified"
                    class="astra-badge astra-badge--success"
                  >
                    {{ msg.data.outcome || (msg.data.qualified ? __('Qualified') : '') }}
                  </span>
                </div>
                <p
                  v-if="msg.data?.call_summary || msg.data?.summary"
                  class="astra-muted mt-2 text-xs leading-relaxed"
                >
                  {{ msg.data.call_summary || msg.data.summary }}
                </p>
                <p class="astra-muted mt-2 text-[11px]">
                  {{ formatTime(msg.creation) }}
                </p>
              </div>
              <div
                v-else-if="msg.kind === 'whatsapp'"
                class="w-full max-w-xl rounded-[12px] border border-[var(--astra-border)] p-3"
              >
                <p class="text-xs font-semibold text-[var(--astra-text)]">
                  {{ __('WhatsApp') }} · {{ __('Read-only') }}
                </p>
                <p class="mt-1 text-sm text-[var(--astra-text)]">
                  {{ msg.data?.text || msg.data?.content || '' }}
                </p>
                <button
                  v-if="connectConfigured"
                  type="button"
                  class="astra-btn astra-btn--teal mt-2"
                  @click="openConnectMessages"
                >
                  {{ __('Open in Astra Connect') }}
                </button>
              </div>
              <div
                v-else
                class="max-w-[85%] rounded-[14px] px-3 py-2 text-sm"
                :class="
                  isOutgoing(msg)
                    ? 'bg-[var(--astra-teal)] text-white'
                    : 'border border-[var(--astra-border)] bg-[var(--astra-card)] text-[var(--astra-text)]'
                "
              >
                <p v-if="msg.data?.subject" class="mb-1 text-xs font-semibold opacity-90">
                  {{ msg.data.subject }}
                </p>
                <p class="whitespace-pre-wrap break-words leading-relaxed">
                  {{ messageBody(msg) }}
                </p>
                <p
                  class="mt-1 text-[11px]"
                  :class="isOutgoing(msg) ? 'text-white/80' : 'astra-muted'"
                >
                  {{ formatTime(msg.creation) }}
                </p>
              </div>
            </div>
          </template>
        </div>

        <div class="border-t border-[var(--astra-border)] px-4 py-3">
          <p class="astra-muted text-xs">
            {{
              __(
                'Replies and WhatsApp compose open in Astra Connect. This view does not send messages.',
              )
            }}
          </p>
        </div>
      </AstraCard>

      <!-- Contact panel -->
      <AstraCard class="min-h-0 overflow-y-auto lg:col-span-3" flush>
        <div class="px-4 py-5">
          <AstraEmptyState
            v-if="!selected"
            :title="__('No contact selected')"
            :body="__('Pick a thread to see the linked lead, deal or contact.')"
          />
          <template v-else-if="panelDoc">
            <div class="flex flex-col items-start gap-3">
              <AstraAvatar
                :name="panelTitle"
                :seed="panelDoc.name"
                size="lg"
                :aria-label="panelTitle"
              />
              <div>
                <h3 class="text-lg font-bold text-[var(--astra-text)]">
                  {{ panelTitle }}
                </h3>
                <p v-if="panelSubtitle" class="astra-muted text-sm">
                  {{ panelSubtitle }}
                </p>
              </div>
              <p
                v-if="panelPhone"
                class="text-sm font-medium text-[var(--astra-text)]"
              >
                {{ panelPhone }}
              </p>
              <div
                v-if="panelDealValue || panelBadges.length"
                class="w-full rounded-[12px] border border-[var(--astra-border)] p-3"
              >
                <p
                  v-if="panelDealValue"
                  class="text-base font-bold text-[var(--astra-text)]"
                >
                  {{ panelDealValue }}
                </p>
                <div class="mt-2 flex flex-wrap gap-1.5">
                  <span
                    v-for="badge in panelBadges"
                    :key="badge"
                    class="astra-badge astra-badge--med"
                  >{{ badge }}</span>
                </div>
              </div>
              <button
                type="button"
                class="astra-btn astra-btn--outline"
                @click="openPanelRecord"
              >
                {{ __('Open record') }}
              </button>
            </div>
          </template>
          <AstraEmptyState
            v-else-if="contactPanel.loading"
            :title="__('Loading…')"
            body=""
          />
          <AstraEmptyState
            v-else
            :title="__('No linked record')"
            :body="__(
              'This item is not linked to a lead, deal or contact, so details cannot be shown.',
            )"
          />
        </div>
      </AstraCard>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePageMeta } from 'frappe-ui'
import { ASTRA_FAVICON } from '@/assets/brand'
import AstraCard from '@/components/astra/AstraCard.vue'
import AstraEmptyState from '@/components/astra/AstraEmptyState.vue'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import { useConversations } from '@/components/astra/conversations/useConversations'
import {
  formatCompactCurrency,
  formatTime,
  routeForReference,
} from '@/components/astra/format'
import {
  isAstraConnectConfigured,
  openAstraConnect,
} from '@/utils/astraConnect'
import '@/components/astra/astra-bento.css'

usePageMeta(() => ({
  title: __('Conversations'),
  icon: ASTRA_FAVICON,
}))

const router = useRouter()
const connectConfigured = isAstraConnectConfigured()

const {
  channel,
  selectedId,
  threads,
  selected,
  conversationMessages,
  panelDoc,
  contactPanel,
  showWhatsApp,
  loading,
} = useConversations()

const channelPills = computed(() => {
  const pills = [
    { value: 'all', label: 'All' },
    { value: 'calls', label: 'Calls' },
  ]
  if (showWhatsApp.value) pills.push({ value: 'whatsapp', label: 'WhatsApp' })
  pills.push({ value: 'emails', label: 'Email' })
  return pills
})

const conversationTitle = computed(() => {
  if (!selected.value) return __('Conversation')
  const doc = panelDoc.value
  if (!doc) return selected.value.title
  const name =
    doc.lead_name || doc.organization || doc.first_name || doc.name || selected.value.title
  const company = doc.organization && doc.lead_name ? doc.organization : ''
  return company ? `${name} - ${company}` : name
})

const panelTitle = computed(() => {
  const doc = panelDoc.value
  if (!doc) return ''
  return (
    doc.lead_name ||
    [doc.first_name, doc.last_name].filter(Boolean).join(' ') ||
    doc.organization ||
    doc.name
  )
})

const panelSubtitle = computed(() => {
  const doc = panelDoc.value
  if (!doc) return ''
  if (doc.lead_name && doc.organization) return doc.organization
  return doc.status || selected.value?.reference_doctype || ''
})

const panelPhone = computed(
  () => panelDoc.value?.mobile_no || panelDoc.value?.phone || '',
)

const panelDealValue = computed(() => {
  const doc = panelDoc.value
  if (!doc) return ''
  const amount = doc.deal_value || doc.expected_deal_value || doc.annual_revenue
  if (!amount) return ''
  return formatCompactCurrency(amount)
})

const panelBadges = computed(() => {
  const doc = panelDoc.value
  if (!doc) return []
  const badges = []
  if (doc.lead_temperature === 'Hot') badges.push(__('Hot'))
  if (doc.status) badges.push(doc.status)
  return badges.slice(0, 3)
})

function channelLabel(ch) {
  if (ch === 'calls') return __('Call')
  if (ch === 'emails') return __('Email')
  if (ch === 'notes') return __('Note')
  if (ch === 'whatsapp') return __('WhatsApp')
  return __('Activity')
}

function isCall(msg) {
  return msg.kind === 'incoming_call' || msg.kind === 'outgoing_call'
}

function isOutgoing(msg) {
  if (msg.kind === 'outgoing_call') return true
  if (msg.kind === 'communication') {
    return (
      msg.data?.sent_or_received === 'Sent' ||
      String(msg.data?.sent_or_received || '').toLowerCase() === 'sent'
    )
  }
  return false
}

function callHeading(msg) {
  const duration = msg.data?.duration
  const type = msg.kind === 'incoming_call' ? __('Incoming call') : __('Outgoing call')
  if (duration) return `${type} · ${duration}`
  return type
}

function messageBody(msg) {
  if (msg.kind === 'note') return msg.data?.title || msg.data?.content || ''
  const html = msg.data?.content || msg.data?.text || ''
  return String(html)
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function openConnectMessages() {
  openAstraConnect('messages')
}

function openPanelRecord() {
  const sel = selected.value
  if (!sel) return
  const route = routeForReference(sel.reference_doctype, sel.reference_docname)
  if (route) router.push(route)
}
</script>
