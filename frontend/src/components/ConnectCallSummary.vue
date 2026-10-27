<template>
  <div
    v-if="summary"
    class="flex max-w-md flex-col gap-0.5 rounded-md border border-outline-gray-2 bg-surface-gray-2 px-3 py-1.5 text-p-sm text-ink-gray-8"
    role="status"
  >
    <div class="flex flex-wrap items-center gap-2">
      <span class="text-p-sm-medium text-ink-gray-9">{{ __('Latest AI call') }}</span>
      <Badge
        v-if="summary.qualified"
        :label="__('Qualified')"
        theme="green"
        variant="subtle"
      />
      <span v-if="summary.outcome" class="text-ink-gray-6">{{ summary.outcome }}</span>
      <span v-else-if="summary.disposition" class="text-ink-gray-6">{{
        summary.disposition
      }}</span>
    </div>
    <p
      v-if="summary.call_summary"
      class="line-clamp-2 text-ink-gray-7"
      :title="summary.call_summary"
    >
      {{ summary.call_summary }}
    </p>
  </div>
</template>

<script setup>
import { Badge, createResource } from 'frappe-ui'
import { computed, watch } from 'vue'
import { isAstraConnectConfigured } from '@/utils/astraConnect'

const props = defineProps({
  doctype: { type: String, required: true },
  name: { type: String, default: '' },
})

const resource = createResource({
  url: 'crm.integrations.astra_connect.outbound.get_latest_call_summary',
  auto: false,
})

watch(
  () => [props.doctype, props.name],
  ([doctype, name]) => {
    if (!isAstraConnectConfigured() || !doctype || !name) {
      resource.reset?.()
      return
    }
    resource.submit({ doctype, name })
  },
  { immediate: true },
)

const summary = computed(() =>
  isAstraConnectConfigured() ? resource.data || null : null,
)
</script>
