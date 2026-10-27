<template>
  <div class="astra-bento flex h-full min-h-0 flex-col overflow-hidden">
    <div class="min-h-0 flex-1 overflow-y-auto px-4 py-4 sm:px-6">
      <header class="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 class="text-[1.75rem] font-bold tracking-tight text-[var(--astra-text)]">
            {{ __('Work queue') }}
            <span class="ml-2 tabular-nums text-[var(--astra-text)]">{{ counts.all }}</span>
            <span class="astra-muted ml-1 text-base font-medium">{{
              __('actions today')
            }}</span>
          </h1>
        </div>
        <div class="flex flex-wrap gap-1.5" role="tablist" :aria-label="__('Queue filters')">
          <button
            v-for="pill in pills"
            :key="pill.value"
            type="button"
            role="tab"
            class="astra-pill"
            :class="{ 'astra-pill--active': typeFilter === pill.value }"
            :aria-selected="typeFilter === pill.value"
            @click="typeFilter = pill.value"
          >
            {{ __(pill.label) }}
          </button>
        </div>
      </header>

      <div class="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <aside class="flex flex-col gap-4 lg:col-span-3">
          <AstraCard :title="__('Type')">
            <ul role="list">
              <li
                v-for="row in typeRows"
                :key="row.value"
                class="astra-row cursor-pointer"
                @click="typeFilter = row.value"
              >
                <span class="flex-1 text-sm text-[var(--astra-text)]">{{
                  __(row.label)
                }}</span>
                <span class="tabular-nums text-sm font-bold">{{ row.count }}</span>
              </li>
            </ul>
          </AstraCard>
          <AstraCard :title="__('Priority')">
            <ul role="list">
              <li class="astra-row">
                <span class="size-2 rounded-full bg-[var(--astra-danger)]" aria-hidden="true" />
                <span class="flex-1 text-sm">{{ __('High') }}</span>
                <span class="tabular-nums text-sm font-bold">{{ counts.high }}</span>
              </li>
              <li class="astra-row">
                <span class="size-2 rounded-full bg-[var(--astra-warn)]" aria-hidden="true" />
                <span class="flex-1 text-sm">{{ __('Medium') }}</span>
                <span class="tabular-nums text-sm font-bold">{{ counts.med }}</span>
              </li>
              <li class="astra-row">
                <span class="size-2 rounded-full bg-[var(--astra-muted)]" aria-hidden="true" />
                <span class="flex-1 text-sm">{{ __('Low') }}</span>
                <span class="tabular-nums text-sm font-bold">{{ counts.low }}</span>
              </li>
            </ul>
          </AstraCard>
        </aside>

        <section class="lg:col-span-9">
          <div v-if="loading" class="astra-muted text-sm">{{ __('Loading…') }}</div>
          <AstraEmptyState
            v-else-if="typeFilter === 'whatsapp'"
            :title="__('WhatsApp actions open in Astra Connect')"
            :body="__(
              'Message follow-ups are handled in Astra Connect. Use Messages in the sidebar when Connect is configured.',
            )"
          />
          <AstraEmptyState
            v-else-if="!items.length"
            :title="__('Queue is clear')"
            :body="__(
              'No overdue tasks, quiet leads or stuck deals right now. Items appear from CRM Task, Lead and Deal records.',
            )"
          />
          <ul v-else class="flex flex-col gap-2" role="list">
            <li
              v-for="(item, index) in items"
              :key="item.id"
              class="astra-card !p-3"
              :class="index === 0 ? 'ring-1 ring-[var(--astra-primary)]/30' : ''"
            >
              <div class="flex flex-wrap items-center gap-3">
                <span
                  class="astra-badge"
                  :class="{
                    'astra-badge--high': item.priority === 'High',
                    'astra-badge--med': item.priority === 'Med',
                    'astra-badge--low': item.priority === 'Low',
                  }"
                >{{ item.priority }}</span>
                <AstraAvatar :name="item.title" :seed="item.id" size="sm" />
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-semibold text-[var(--astra-text)]">
                    {{ item.title }}
                  </p>
                  <p class="astra-muted truncate text-xs">
                    {{ item.reason }}
                    <template v-if="item.subtitle"> · {{ item.subtitle }}</template>
                  </p>
                </div>
                <button
                  type="button"
                  class="astra-btn"
                  :class="actionClass(item)"
                  @click="runAction(item)"
                >
                  {{ actionLabel(item) }}
                </button>
              </div>
            </li>
          </ul>
        </section>
      </div>
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
import { useWorkQueue } from '@/components/astra/workqueue/useWorkQueue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { globalStore } from '@/stores/global'
import { routeForReference } from '@/components/astra/format'
import { isAstraConnectConfigured, openAstraConnect } from '@/utils/astraConnect'
import '@/components/astra/astra-bento.css'

usePageMeta(() => ({
  title: __('Work queue'),
  icon: ASTRA_FAVICON,
}))

const router = useRouter()
const { showModal } = useDoctypeModal()
const { makeCall } = globalStore()
const { typeFilter, items, counts, loading } = useWorkQueue()

const pills = [
  { value: 'all', label: 'All' },
  { value: 'calls', label: 'Calls' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'follow_ups', label: 'Follow-ups' },
]

const typeRows = computed(() => [
  { value: 'calls', label: 'Calls', count: counts.value.calls },
  { value: 'whatsapp', label: 'WhatsApp', count: counts.value.whatsapp },
  { value: 'follow_ups', label: 'Follow-ups', count: counts.value.follow_ups },
])

function actionLabel(item) {
  if (item.action === 'call') return __('Call')
  if (item.action === 'follow_up') return __('Follow up')
  return __('Open')
}

function actionClass(item) {
  if (item.action === 'call') return 'astra-btn--primary'
  if (item.action === 'follow_up') return 'astra-btn--outline'
  return 'astra-btn--primary'
}

function runAction(item) {
  if (item.action === 'call' && item.phone) {
    makeCall(item.phone)
    return
  }
  if (item.action === 'follow_up') {
    if (item.taskName) {
      showModal({
        doctype: 'CRM Task',
        name: item.taskName,
        title: 'Task',
      })
      return
    }
    showModal({
      doctype: 'CRM Task',
      title: 'Task',
      defaults: {
        status: 'Backlog',
        priority: 'Medium',
        reference_doctype: item.reference_doctype,
        reference_docname: item.reference_docname,
        title: `Follow up: ${item.title}`,
      },
    })
    return
  }
  if (typeFilter.value === 'whatsapp' && isAstraConnectConfigured()) {
    openAstraConnect('messages')
    return
  }
  const route = routeForReference(item.reference_doctype, item.reference_docname)
  if (route) router.push(route)
}
</script>
