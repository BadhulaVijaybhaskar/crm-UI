<template>
  <div class="max-h-36 overflow-y-auto">
    <div class="mb-2 text-crm-label font-semibold text-crm-fg">
      {{ __('Stage history') }}
    </div>
    <p v-if="!entries.length" class="text-crm-label text-crm-muted-fg">
      {{ __('No stage changes yet.') }}
    </p>
    <ul v-else class="flex flex-col gap-2">
      <li
        v-for="(entry, index) in entries"
        :key="`${entry.at}-${index}`"
        class="rounded-crm-card border border-crm-border px-3 py-2 text-crm-label text-crm-fg"
      >
        <div class="flex flex-wrap items-baseline gap-1">
          <span v-if="entry.open" class="font-semibold">{{ entry.from }}</span>
          <template v-else>
            <span class="font-semibold">{{ entry.from || __('(start)') }}</span>
            <span class="text-crm-muted-fg">→</span>
            <span class="font-semibold">{{ entry.to }}</span>
          </template>
          <AstraBadge v-if="entry.open" class="ml-1" :label="__('Current')" tone="info" />
        </div>
        <div class="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-crm-muted-fg">
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
import AstraBadge from '@/components/astra/AstraBadge.vue'
import { formatDate } from '@/utils'
import { normalizeStageHistory } from '@/utils/stageHistory'

const props = defineProps({
  rows: { type: Array, default: () => [] },
})

const entries = computed(() => normalizeStageHistory(props.rows))
</script>
