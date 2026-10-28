<template>
  <div class="border-t px-4 py-3">
    <div class="mb-2 text-sm font-medium text-ink-gray-9">
      {{ __('Stage history') }}
    </div>
    <p v-if="!entries.length" class="text-p-sm text-ink-gray-5">
      {{ __('No stage changes yet.') }}
    </p>
    <ul v-else class="flex flex-col gap-2">
      <li
        v-for="(entry, index) in entries"
        :key="`${entry.at}-${index}`"
        class="rounded-md border border-outline-gray-2 px-3 py-2 text-p-sm text-ink-gray-8"
      >
        <div class="flex flex-wrap items-baseline gap-1">
          <span v-if="entry.open" class="font-medium">{{ entry.from }}</span>
          <template v-else>
            <span class="font-medium">{{ entry.from || __('(start)') }}</span>
            <span class="text-ink-gray-5">→</span>
            <span class="font-medium">{{ entry.to }}</span>
          </template>
          <Badge
            v-if="entry.open"
            class="ml-1"
            :label="__('Current')"
            theme="blue"
            variant="subtle"
          />
        </div>
        <div class="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-ink-gray-5">
          <span v-if="entry.by">{{ __('By {0}', [entry.by]) }}</span>
          <span v-if="entry.at">{{ formatDate(entry.at) }}</span>
          <span v-if="entry.duration">
            {{ __('Duration {0}', [entry.duration]) }}
          </span>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Badge } from 'frappe-ui'
import { formatDate } from '@/utils'
import { normalizeStageHistory } from '@/utils/stageHistory'

const props = defineProps({
  rows: { type: Array, default: () => [] },
})

const entries = computed(() => normalizeStageHistory(props.rows))
</script>
