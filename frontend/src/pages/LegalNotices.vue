<template>
  <div class="flex h-full flex-col overflow-y-auto bg-surface-base">
    <div class="mx-auto w-full max-w-3xl px-6 py-8">
      <h1 class="text-2xl-semibold text-ink-gray-9">
        {{ __('Legal notices') }}
      </h1>

      <ul class="mt-8 flex flex-col gap-3">
        <li
          v-for="licence in notices"
          :key="licence"
          class="rounded-5 border border-outline-gray-2 px-4 py-3 text-base-medium text-ink-gray-9"
        >
          {{ licence }}
        </li>
      </ul>

      <p class="mt-8 text-p-sm text-ink-gray-5">
        {{ __(sourceLine) }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { usePageMeta } from 'frappe-ui'
import { ASTRA_FAVICON } from '@/assets/brand'
import { LEGAL_SOURCE_LINE, legalNotices } from '@/data/legalNotices'

const notices = legalNotices
const sourceLine = LEGAL_SOURCE_LINE

usePageMeta(() => ({
  title: __('Legal notices'),
  icon: ASTRA_FAVICON,
}))
</script>
