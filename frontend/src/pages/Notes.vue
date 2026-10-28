<template>
  <div class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg">
    <AstraPageHeader
      :title="__('Notes')"
      :description="__('Notes on your leads and deals.')"
    >
      <template #actions>
        <AstraButton variant="primary" :label="__('New note')" @click="createNote">
          <template #prefix>
            <LucidePlus class="size-3.5" aria-hidden="true" />
          </template>
        </AstraButton>
      </template>
    </AstraPageHeader>

    <ViewControls
      ref="viewControls"
      v-model="notes"
      v-model:loadMore="loadMore"
      v-model:updatedPageCount="updatedPageCount"
      doctype="FCRM Note"
      :options="{
        hideColumnsButton: true,
        defaultViewName: __('Notes View'),
      }"
    />

    <div
      v-if="noteRows.length"
      class="grid min-h-0 flex-1 grid-cols-1 border-t border-crm-border lg:grid-cols-[minmax(280px,380px)_1fr]"
    >
      <aside class="flex min-h-0 flex-col overflow-y-auto border-r border-crm-border bg-crm-card">
        <template v-if="pinnedNotes.length">
          <p
            class="px-4 pb-1 pt-3 text-[10.5px] font-bold uppercase tracking-[0.06em] text-crm-faint"
          >
            {{ __('Pinned') }}
          </p>
          <button
            v-for="note in pinnedNotes"
            :key="'p-' + note.name"
            type="button"
            class="w-full border-b border-crm-border px-4 py-3 text-left hover:bg-crm-row-hover"
            :class="{ 'bg-crm-row-selected': selectedName === note.name }"
            @click="selectNote(note)"
          >
            <div class="flex items-start justify-between gap-2">
              <p class="m-0 truncate text-crm-label font-semibold text-crm-fg">
                {{ note.title }}
              </p>
              <div class="flex shrink-0 items-center gap-1.5">
                <span class="text-crm-micro text-crm-faint">
                  {{ __(timeAgo(note.modified)) }}
                </span>
                <span
                  class="rounded bg-crm-warning-soft px-1.5 text-[10.5px] font-semibold text-crm-warning"
                >
                  {{ __('Pinned') }}
                </span>
              </div>
            </div>
            <p
              v-if="noteSnippet(note)"
              class="m-0 mt-1 line-clamp-2 text-crm-meta text-crm-muted-fg"
            >
              {{ noteSnippet(note) }}
            </p>
            <p
              v-if="linkedLabel(note)"
              class="m-0 mt-1.5 truncate text-crm-meta font-semibold text-crm-primary"
            >
              {{ linkedLabel(note) }}
            </p>
          </button>
        </template>
        <p
          class="px-4 pb-1 pt-3 text-[10.5px] font-bold uppercase tracking-[0.06em] text-crm-faint"
        >
          {{ __('Recent') }}
        </p>
        <button
          v-for="note in recentNotes"
          :key="'r-' + note.name"
          type="button"
          class="w-full border-b border-crm-border px-4 py-3 text-left hover:bg-crm-row-hover"
          :class="{ 'bg-crm-row-selected': selectedName === note.name }"
          @click="selectNote(note)"
        >
          <div class="flex items-start justify-between gap-2">
            <p class="m-0 truncate text-crm-label font-semibold text-crm-fg">
              {{ note.title }}
            </p>
            <span class="shrink-0 text-crm-micro text-crm-faint">
              {{ __(timeAgo(note.modified)) }}
            </span>
          </div>
          <p
            v-if="noteSnippet(note)"
            class="m-0 mt-1 line-clamp-2 text-crm-meta text-crm-muted-fg"
          >
            {{ noteSnippet(note) }}
          </p>
          <p
            v-if="linkedLabel(note)"
            class="m-0 mt-1.5 truncate text-crm-meta font-semibold text-crm-primary"
          >
            {{ linkedLabel(note) }}
          </p>
        </button>
        <ListFooter
          v-if="notes.data?.data?.length"
          v-model="notes.data.page_length_count"
          class="border-t px-3 py-2"
          :options="{
            rowCount: notes.data.row_count,
            totalCount: notes.data.total_count,
          }"
          @loadMore="() => loadMore++"
        />
      </aside>

      <section
        v-if="selectedNote"
        class="flex min-h-0 flex-col overflow-y-auto bg-crm-card"
      >
        <header
          class="flex flex-wrap items-start justify-between gap-3 border-b border-crm-border px-5 py-4"
        >
          <div class="min-w-0">
            <h2 class="m-0 text-crm-dialog font-semibold text-crm-fg">
              {{ selectedNote.title }}
            </h2>
            <AstraBadge
              v-if="selectedNote.pinned"
              class="mt-2"
              :label="pinnedBadgeLabel"
              tone="warn"
            />
          </div>
          <div class="flex flex-wrap gap-2">
            <AstraButton
              v-if="canPin"
              size="sm"
              :label="selectedNote.pinned ? __('Unpin') : __('Pin')"
              @click="togglePin(selectedNote)"
            />
            <AstraButton
              size="sm"
              :label="__('Edit')"
              @click="editNote(selectedNote.name)"
            />
          </div>
        </header>
        <!-- content is passed through sanitizeHTML() (DOMPurify) before rendering, so v-html is safe here -->
        <!-- eslint-disable vue/no-v-html -->
        <div
          class="prose-f prose-sm max-w-none flex-1 px-5 py-4 text-crm-label text-crm-fg"
          v-html="sanitizeHTML(selectedNote.content || '')"
        />
        <!-- eslint-enable vue/no-v-html -->
        <footer
          class="flex flex-wrap items-center justify-between gap-2 border-t border-crm-border px-5 py-3 text-crm-meta text-crm-muted-fg"
        >
          <router-link
            v-if="linkedRoute(selectedNote)"
            :to="linkedRoute(selectedNote)"
            class="font-semibold text-crm-primary hover:underline"
          >
            {{ __('Linked to') }} {{ linkedLabel(selectedNote) }}
          </router-link>
          <span v-else />
          <span>
            {{ __('By') }}
            {{ getUser(selectedNote.owner).full_name }}
            · {{ formatDate(selectedNote.modified) }}
          </span>
        </footer>
      </section>
    </div>

    <AstraEmptyState
      v-else-if="notes.data"
      :title="__('No notes yet')"
      :body="
        __(
          'Notes keep what you learned on a call or in a meeting next to the lead or deal it belongs to.',
        )
      "
    >
      <AstraButton variant="primary" :label="__('New note')" @click="createNote" />
    </AstraEmptyState>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { call, usePageMeta } from 'frappe-ui'
import { ListFooter } from 'frappe-ui/experimental'
import LucidePlus from '~icons/lucide/plus'
import ViewControls from '@/components/ViewControls.vue'
import {
  AstraBadge,
  AstraButton,
  AstraEmptyState,
  AstraPageHeader,
} from '@/components/astra'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useNoteView } from '@/composables/noteView'
import { usersStore } from '@/stores/users'
import { timeAgo, formatDate, sanitizeHTML } from '@/utils'
import { useTelemetry } from '@framework/ui/telemetry'
import { getSettings } from '@/stores/settings'
import { ASTRA_FAVICON } from '@/assets/brand'

const { brand } = getSettings()
const { getUser } = usersStore()
const { capture } = useTelemetry()
const { showModal } = useDoctypeModal()
const { openNote, loadLinkedTitles, linkedRoute, linkedLabel } = useNoteView()

const notes = ref({})
const loadMore = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)
const selectedName = ref(null)

const noteRows = computed(() => notes.value?.data?.data || [])
const pinnedNotes = computed(() => noteRows.value.filter((n) => n.pinned))
const recentNotes = computed(() => noteRows.value.filter((n) => !n.pinned))
const selectedNote = computed(
  () => noteRows.value.find((n) => n.name === selectedName.value) || null,
)
const canPin = computed(() =>
  noteRows.value.some((n) => Object.prototype.hasOwnProperty.call(n, 'pinned')),
)

const pinnedBadgeLabel = computed(() => {
  const n = selectedNote.value
  if (!n?.pinned) return __('Pinned')
  if (n.pinned_by) {
    return __('Pinned by {0}', [getUser(n.pinned_by).full_name])
  }
  return __('Pinned')
})

watch(
  () => notes.value?.data?.page_length_count,
  (val, old_value) => {
    if (!val || val === old_value) return
    updatedPageCount.value = val
  },
)

watch(
  () => notes.value?.data?.data,
  (rows) => {
    loadLinkedTitles(rows)
    if (!rows?.length) {
      selectedName.value = null
      return
    }
    if (!selectedName.value || !rows.find((n) => n.name === selectedName.value)) {
      selectedName.value = rows[0].name
    }
  },
)

function selectNote(note) {
  selectedName.value = note.name
}

function noteSnippet(note) {
  if (!note?.content) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = sanitizeHTML(note.content)
  return (tmp.textContent || '').trim().slice(0, 180)
}

const noteCallbacks = {
  afterInsert: () => {
    notes.value.reload()
    capture('note_created')
  },
  afterUpdate: () => {
    notes.value.reload()
    capture('note_updated')
  },
}

function createNote() {
  showModal({
    doctype: 'FCRM Note',
    title: 'Note',
    callbacks: noteCallbacks,
  })
}

function editNote(noteName) {
  showModal({
    name: noteName,
    doctype: 'FCRM Note',
    title: 'Note',
    callbacks: noteCallbacks,
  })
}

async function togglePin(note) {
  await call('crm.fcrm.doctype.fcrm_note.fcrm_note.set_pinned', {
    name: note.name,
    pinned: !note.pinned,
  })
  notes.value.reload()
}

onMounted(() => {
  const searchParams = new URLSearchParams(window.location.search)
  const noteName = searchParams.get('open')
  if (!noteName) return
  openNote({ name: noteName }, { edit: () => editNote(noteName) })
  searchParams.delete('open')
  window.history.replaceState(null, '', window.location.pathname)
})

usePageMeta(() => ({
  title: __('Notes'),
  icon: brand?.favicon || ASTRA_FAVICON,
}))
</script>
