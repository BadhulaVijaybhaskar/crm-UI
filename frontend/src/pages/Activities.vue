<template>
  <div class="flex h-full min-h-0 flex-col overflow-hidden">
    <div class="border-b px-4 py-4 sm:px-6">
      <h1 class="text-[28px] font-bold tracking-tight text-ink-gray-9">
        {{ __('Activities') }}
      </h1>
      <p class="mt-1 text-p-sm text-ink-gray-5">
        {{ __('Your day and a feed across leads, deals and contacts.') }}
      </p>
    </div>

    <div
      class="flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto px-4 py-4 sm:px-6 lg:flex-row"
    >
      <!-- My day -->
      <section class="flex w-full flex-col gap-3 lg:w-80 lg:shrink-0">
        <h2 class="text-lg-semibold text-ink-gray-9">{{ __('My day') }}</h2>
        <div
          v-if="myDay.loading"
          class="text-p-sm text-ink-gray-5"
        >
          {{ __('Loading…') }}
        </div>
        <template v-else>
          <div>
            <h3 class="mb-1 text-sm font-medium text-ink-gray-7">
              {{ __('Tasks') }}
            </h3>
            <p
              v-if="!(myDay.data?.tasks || []).length"
              class="text-p-sm text-ink-gray-5"
            >
              {{ __('Nothing due today.') }}
            </p>
            <ul v-else class="flex flex-col gap-1.5">
              <li
                v-for="task in myDay.data.tasks"
                :key="task.name"
                class="rounded-md border border-outline-gray-2 px-3 py-2 text-p-sm"
              >
                <div class="font-medium text-ink-gray-9">{{ task.title }}</div>
                <div class="mt-0.5 text-ink-gray-5">
                  <span v-if="task.overdue" class="text-ink-red-4">{{
                    __('Overdue')
                  }}</span>
                  <span v-else>{{ __('Due today') }}</span>
                  <span v-if="task.priority"> · {{ task.priority }}</span>
                </div>
              </li>
            </ul>
          </div>
          <div>
            <h3 class="mb-1 text-sm font-medium text-ink-gray-7">
              {{ __('Calls') }}
            </h3>
            <p
              v-if="!(myDay.data?.calls || []).length"
              class="text-p-sm text-ink-gray-5"
            >
              {{ __('No calls today.') }}
            </p>
            <ul v-else class="flex flex-col gap-1.5">
              <li
                v-for="call in myDay.data.calls"
                :key="call.name"
                class="rounded-md border border-outline-gray-2 px-3 py-2 text-p-sm text-ink-gray-8"
              >
                {{ call.type }} · {{ call.status }}
                <span v-if="call.outcome"> · {{ call.outcome }}</span>
              </li>
            </ul>
          </div>
          <div>
            <h3 class="mb-1 text-sm font-medium text-ink-gray-7">
              {{ __('Meetings') }}
            </h3>
            <p
              v-if="!(myDay.data?.meetings || []).length"
              class="text-p-sm text-ink-gray-5"
            >
              {{ __('No meetings today.') }}
            </p>
            <ul v-else class="flex flex-col gap-1.5">
              <li
                v-for="m in myDay.data.meetings"
                :key="m.name"
                class="rounded-md border border-outline-gray-2 px-3 py-2 text-p-sm text-ink-gray-8"
              >
                {{ m.subject }}
              </li>
            </ul>
          </div>
        </template>
      </section>

      <!-- Global feed -->
      <section class="flex min-w-0 flex-1 flex-col gap-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <h2 class="text-lg-semibold text-ink-gray-9">{{ __('Feed') }}</h2>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="chip in feedChips"
              :key="chip.value"
              type="button"
              class="rounded-full px-2.5 py-1 text-xs font-medium transition-colors"
              :class="
                feedFilter === chip.value
                  ? 'bg-surface-gray-10 text-ink-white'
                  : 'bg-surface-gray-2 text-ink-gray-7 hover:bg-surface-gray-3'
              "
              @click="setFeedFilter(chip.value)"
            >
              {{ __(chip.label) }}
            </button>
          </div>
        </div>

        <div v-if="feed.loading" class="text-p-sm text-ink-gray-5">
          {{ __('Loading…') }}
        </div>
        <div
          v-else-if="feed.error"
          class="rounded-md border border-outline-gray-2 bg-surface-red-1 px-3 py-3 text-p-sm text-ink-red-4"
          role="alert"
        >
          <p class="font-medium">{{ __('Could not load the activity feed.') }}</p>
          <p class="mt-1 text-ink-gray-7">
            {{
              feed.error?.messages?.[0] ||
              feed.error?.message ||
              __('Check your permissions or try again.')
            }}
          </p>
          <Button
            class="mt-2"
            :label="__('Retry')"
            @click="feed.reload()"
          />
        </div>
        <p
          v-else-if="!(feed.data?.items || []).length"
          class="text-p-sm text-ink-gray-5"
        >
          {{ __('No activity yet.') }}
        </p>
        <ul v-else class="flex flex-col gap-2">
          <li
            v-for="item in feed.data.items"
            :key="`${item.activity_type}-${item.name}`"
            class="rounded-md border border-outline-gray-2 px-3 py-2.5"
          >
            <div class="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
              <span class="text-xs font-semibold uppercase tracking-wide text-ink-gray-5">
                {{ __(item.activity_type.replace('_', ' ')) }}
              </span>
              <button
                v-if="item.reference_docname"
                type="button"
                class="text-p-sm font-medium text-ink-gray-9 hover:underline"
                @click="openRecord(item)"
              >
                {{ item.reference_docname }}
              </button>
            </div>
            <p
              v-if="item.data?.subject || item.data?.title || item.data?.from"
              class="mt-1 text-p-sm text-ink-gray-7"
            >
              <template v-if="item.activity_type === 'stage_change'">
                {{ item.data.from || __('(start)') }} → {{ item.data.to }}
              </template>
              <template v-else>
                {{ item.data.subject || item.data.title || item.data.content }}
              </template>
            </p>
            <p class="mt-1 text-xs text-ink-gray-5">
              {{ item.owner }} · {{ formatDate(item.creation) }}
            </p>
          </li>
        </ul>
        <Button
          v-if="feed.data?.has_more"
          :label="__('Load more')"
          :loading="feed.loading"
          @click="loadMore"
        />
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, createResource, usePageMeta } from 'frappe-ui'
import { formatDate } from '@/utils'
import { TIMELINE_FILTER_CHIPS } from '@/utils/timelineFilters'
import { ASTRA_FAVICON } from '@/assets/brand'

usePageMeta(() => ({
  title: __('Activities'),
  icon: ASTRA_FAVICON,
}))

const router = useRouter()
const feedFilter = ref('all')
const feedStart = ref(0)

const feedChips = computed(() =>
  TIMELINE_FILTER_CHIPS.filter((c) => c.value !== 'whatsapp'),
)

const myDay = createResource({
  url: 'crm.api.activities.get_my_day',
  auto: true,
  cache: 'activities-my-day',
})

const feed = createResource({
  url: 'crm.api.activities.get_activity_feed',
  auto: true,
  cache: ['activities-feed', feedFilter],
  makeParams: () => ({
    activity_type: feedFilter.value === 'all' ? null : feedFilter.value,
    limit: 40,
    start: feedStart.value,
  }),
})

watch(feedFilter, () => {
  feedStart.value = 0
  feed.reload()
})

function setFeedFilter(value) {
  feedFilter.value = value
}

function loadMore() {
  feedStart.value += 40
  feed.reload()
}

function openRecord(item) {
  const map = {
    'CRM Lead': 'Lead',
    'CRM Deal': 'Deal',
    Contact: 'Contact',
  }
  const name = map[item.reference_doctype]
  if (!name || !item.reference_docname) return
  const param =
    name === 'Lead'
      ? { leadId: item.reference_docname }
      : name === 'Deal'
        ? { dealId: item.reference_docname }
        : { contactId: item.reference_docname }
  router.push({ name, params: param })
}
</script>
