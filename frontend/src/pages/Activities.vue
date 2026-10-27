<template>
  <div class="astra-bento flex h-full min-h-0 min-w-0 flex-col overflow-x-hidden overflow-y-hidden">
    <div class="min-h-0 min-w-0 flex-1 overflow-x-hidden overflow-y-auto px-4 py-4 sm:px-6">
      <MyDayBoard
        :my-day-data="myDay.data"
        :my-day-loading="myDay.loading"
      />

      <!-- Global feed — preserved behaviour from CRM-08 -->
      <section class="mt-6">
        <AstraCard :title="__('Feed')">
          <template #actions>
            <div
              class="flex max-w-full min-w-0 flex-wrap gap-1.5"
              role="tablist"
              :aria-label="__('Feed filters')"
            >
              <button
                v-for="chip in feedChips"
                :key="chip.value"
                type="button"
                role="tab"
                class="astra-pill"
                :class="{ 'astra-pill--active': feedFilter === chip.value }"
                :aria-selected="feedFilter === chip.value"
                @click="setFeedFilter(chip.value)"
              >
                {{ __(chip.label) }}
              </button>
            </div>
          </template>

          <div v-if="feed.loading && !feed.data" class="astra-muted text-sm">
            {{ __('Loading…') }}
          </div>
          <AstraEmptyState
            v-else-if="!(feed.data?.items || []).length"
            :title="__('No activity yet')"
            :body="__('Calls, emails, notes and stage changes across your records will appear here.')"
          />
          <ul v-else class="flex flex-col" role="list">
            <li
              v-for="item in feed.data.items"
              :key="`${item.activity_type}-${item.name}`"
              class="astra-row !items-start"
            >
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                  <span class="astra-label uppercase tracking-wide">
                    {{ __(item.activity_type.replace('_', ' ')) }}
                  </span>
                  <button
                    v-if="item.reference_docname"
                    type="button"
                    class="text-sm font-semibold text-[var(--astra-text)] hover:underline"
                    @click="openRecord(item)"
                  >
                    {{ item.reference_docname }}
                  </button>
                </div>
                <p
                  v-if="item.data?.subject || item.data?.title || item.data?.from || item.data?.content"
                  class="mt-1 text-sm text-[var(--astra-text)]"
                >
                  <template v-if="item.activity_type === 'stage_change'">
                    {{ item.data.from || __('(start)') }} → {{ item.data.to }}
                  </template>
                  <template v-else>
                    {{ item.data.subject || item.data.title || item.data.content }}
                  </template>
                </p>
                <p class="astra-muted mt-1 text-xs">
                  {{ item.owner }} · {{ formatDate(item.creation) }}
                </p>
              </div>
            </li>
          </ul>
          <Button
            v-if="feed.data?.has_more"
            class="mt-3"
            :label="__('Load more')"
            :loading="feed.loading"
            @click="loadMore"
          />
        </AstraCard>
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
import MyDayBoard from '@/components/astra/myday/MyDayBoard.vue'
import AstraCard from '@/components/astra/AstraCard.vue'
import AstraEmptyState from '@/components/astra/AstraEmptyState.vue'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import '@/components/astra/astra-bento.css'

usePageMeta(() => ({
  title: __('Activities'),
  icon: ASTRA_FAVICON,
}))

const router = useRouter()
const { user } = sessionStore()
const { isManager } = usersStore()
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

// Backend get_activity_feed supports optional `owner` (crm/api/activities.py ~812).
// Non-managers must pass the current user or they see every readable Call Log
// (including Administrator notes). Managers keep the unscoped team feed.
const feed = createResource({
  url: 'crm.api.activities.get_activity_feed',
  auto: true,
  cache: ['activities-feed', feedFilter],
  makeParams: () => ({
    activity_type: feedFilter.value === 'all' ? null : feedFilter.value,
    owner: isManager() ? null : user,
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
