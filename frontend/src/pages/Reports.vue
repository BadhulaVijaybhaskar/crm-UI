<template>
  <div class="flex h-full flex-col gap-4 p-6">
    <div class="flex items-center gap-3">
      <h1 class="text-2xl font-bold tracking-tight text-ink-gray-9">
        {{ __('Reports') }}
      </h1>
      <span class="astra-placeholder-banner">{{ __('Placeholder') }}</span>
    </div>
    <p class="max-w-xl text-p-base text-ink-gray-6">
      {{
        __(
          'Sales reports and dashboards will land here. Use Dashboard for the current charts.',
        )
      }}
    </p>
  </div>
</template>

<script setup>
import { usePageMeta } from 'frappe-ui'

usePageMeta(() => ({ title: __('Reports') }))
</script>
