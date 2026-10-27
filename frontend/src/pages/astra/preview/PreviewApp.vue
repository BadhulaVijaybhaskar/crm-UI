<template>
  <div class="astra-bento min-h-screen overflow-x-hidden" :data-theme="theme">
    <div class="flex min-h-screen min-w-0">
      <aside
        class="sticky top-0 flex h-screen w-16 shrink-0 flex-col items-center gap-3 bg-[var(--astra-nav)] py-4"
        aria-hidden="true"
      >
        <div class="size-8 rounded-full bg-[var(--astra-primary)]/80" />
        <div
          v-for="n in 5"
          :key="n"
          class="size-8 rounded-xl"
          :class="n === 1 ? 'bg-[var(--astra-primary)]' : 'bg-white/10'"
        />
        <div class="mt-auto size-8 rounded-full bg-white/20 text-center text-xs leading-8 text-white">
          VB
        </div>
      </aside>
      <main class="min-w-0 flex-1 overflow-x-hidden overflow-y-auto p-4 sm:p-6">
        <div class="mb-4 flex min-w-0 flex-wrap gap-2">
          <button
            v-for="p in pages"
            :key="p.id"
            type="button"
            class="astra-pill"
            :class="{ 'astra-pill--active': page === p.id }"
            @click="page = p.id"
          >
            {{ p.label }}
          </button>
          <button
            type="button"
            class="astra-pill sm:ml-auto"
            @click="theme = theme === 'light' ? 'dark' : 'light'"
          >
            {{ theme === 'light' ? 'Dark' : 'Light' }}
          </button>
        </div>
        <p class="astra-muted mb-4 text-xs">
          Mocked preview for screenshots — not live CRM data.
        </p>

        <MyDayMock v-if="page === 'myday'" />
        <WorkQueueMock v-else-if="page === 'workqueue'" />
        <ConversationsMock v-else />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import MyDayMock from './mocks/MyDayMock.vue'
import WorkQueueMock from './mocks/WorkQueueMock.vue'
import ConversationsMock from './mocks/ConversationsMock.vue'
import '@/components/astra/astra-bento.css'

const page = ref(new URLSearchParams(location.search).get('page') || 'myday')
const theme = ref(new URLSearchParams(location.search).get('theme') || 'light')
const pages = [
  { id: 'myday', label: 'My day' },
  { id: 'workqueue', label: 'Work queue' },
  { id: 'conversations', label: 'Conversations' },
]

watch([page, theme], () => {
  document.documentElement.dataset.theme = theme.value
  if (theme.value === 'dark') document.documentElement.classList.add('dark')
  else document.documentElement.classList.remove('dark')
  const url = new URL(location.href)
  url.searchParams.set('page', page.value)
  url.searchParams.set('theme', theme.value)
  history.replaceState(null, '', url)
}, { immediate: true })
</script>

<style>
html, body, #app { margin: 0; min-height: 100%; }
body { background: #f4f6fb; }
html.dark body, [data-theme='dark'] body { background: #0a1222; }
</style>
