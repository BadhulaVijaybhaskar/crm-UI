<template>
  <div class="flex h-full flex-col overflow-y-auto bg-surface-white">
    <div class="mx-auto w-full max-w-3xl px-6 py-8">
      <h1 class="text-2xl-semibold text-ink-gray-9">
        {{ __('Legal notices') }}
      </h1>
      <p class="mt-2 text-p-base text-ink-gray-6">
        {{
          __(
            'Astra CRM includes third-party open-source components. Their licences and source repositories are listed below. This page exists to satisfy notice obligations; product screens do not otherwise display these names.',
          )
        }}
      </p>

      <ul class="mt-8 flex flex-col gap-6">
        <li
          v-for="item in notices"
          :key="item.name"
          class="rounded-5 border border-outline-gray-2 p-4"
        >
          <h2 class="text-lg-semibold text-ink-gray-9">{{ item.name }}</h2>
          <p class="mt-1 text-p-base text-ink-gray-6">{{ item.summary }}</p>
          <p class="mt-2 text-sm text-ink-gray-7">
            {{ __('Licence') }}: {{ item.licence }}
          </p>
          <div class="mt-3 flex flex-wrap gap-3 text-sm">
            <a
              v-if="item.licenceUrl"
              class="text-ink-gray-8 underline underline-offset-2"
              :href="item.licenceUrl"
              target="_blank"
              rel="noopener noreferrer"
            >
              {{ __('Licence text') }}
            </a>
            <a
              v-if="item.sourceUrl"
              class="text-ink-gray-8 underline underline-offset-2"
              :href="item.sourceUrl"
              target="_blank"
              rel="noopener noreferrer"
            >
              {{ __('Source repository') }}
            </a>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { usePageMeta } from 'frappe-ui'
import { ASTRA_FAVICON } from '@/assets/brand'
import { legalNotices } from '@/data/legalNotices'

const notices = legalNotices

usePageMeta(() => ({
  title: __('Legal notices'),
  icon: ASTRA_FAVICON,
}))
</script>
