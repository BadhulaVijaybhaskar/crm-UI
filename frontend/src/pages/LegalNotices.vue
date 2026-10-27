<template>
  <div class="flex h-full flex-col overflow-y-auto bg-surface-white">
    <div class="mx-auto w-full max-w-3xl px-6 py-8">
      <h1 class="text-2xl-semibold text-ink-gray-9">
        {{ __('Legal notices') }}
      </h1>
      <p class="mt-2 text-p-base text-ink-gray-6">
        {{
          __(
            'This product includes third-party open-source components. Their licences are listed below.',
          )
        }}
      </p>

      <ul class="mt-8 flex flex-col gap-6">
        <li
          v-for="(item, index) in notices"
          :key="`${item.licence}-${index}`"
          class="rounded-5 border border-outline-gray-2 p-4"
        >
          <h2 class="text-lg-semibold text-ink-gray-9">{{ item.licence }}</h2>
          <p class="mt-1 text-p-base text-ink-gray-6">{{ item.summary }}</p>
        </li>
      </ul>

      <p class="mt-8 text-p-base text-ink-gray-7">
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
