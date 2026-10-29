<template>
  <div
    class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg [text-rendering:geometricPrecision]"
  >
    <header class="flex shrink-0 items-center gap-3 px-crm-page-x pb-3.5 pt-[19px]">
      <div class="min-w-0">
        <h1
          class="m-0 text-[20px] font-semibold leading-[1.45] tracking-[-0.015em] text-crm-fg"
        >
          {{ __('Notes') }}
        </h1>
        <p
          class="relative top-px m-0 -mt-px text-[13px] leading-[1.45] tracking-[-0.005em] text-crm-muted-fg"
        >
          {{ __('Notes on your leads and deals') }}
        </p>
      </div>
      <div class="flex-1" />
      <AstraButton
        size="sm"
        variant="primary"
        :label="__('New note')"
        @click="createNote"
      >
        <template #prefix>
          <LucidePlus class="size-3.5" aria-hidden="true" />
        </template>
      </AstraButton>
    </header>

    <div class="flex h-8 shrink-0 items-center gap-2 px-crm-page-x">
      <label
        class="flex h-8 w-[300px] items-center gap-[7px] rounded-crm-control border border-crm-border-strong bg-crm-card px-[11px]"
      >
        <LucideSearch class="size-3.5 shrink-0 text-crm-faint" aria-hidden="true" />
        <input
          v-model="search"
          type="search"
          class="min-w-0 flex-1 border-0 bg-transparent p-0 text-[12.5px] text-crm-fg outline-none placeholder:text-crm-faint"
          :placeholder="__('Search notes')"
          :aria-label="__('Search notes')"
        />
      </label>
      <label
        class="relative inline-flex h-8 items-center gap-1.5 rounded-crm-control border border-crm-border-strong bg-crm-card pl-2.5 pr-[9px] text-[12.5px] font-medium"
      >
        <span class="text-crm-muted-fg">{{ __('Linked to') }}</span>
        <span class="font-semibold text-crm-fg">{{ linkedLabelText }}</span>
        <LucideChevronDown class="size-3.5 text-crm-faint" aria-hidden="true" />
        <select
          v-model="linkedDoctype"
          class="absolute inset-0 cursor-pointer opacity-0"
          :aria-label="__('Linked to')"
        >
          <option value="">{{ __('Any') }}</option>
          <option value="CRM Lead">{{ __('Lead') }}</option>
          <option value="CRM Deal">{{ __('Deal') }}</option>
        </select>
      </label>
      <label
        class="relative inline-flex h-8 items-center gap-1.5 rounded-crm-control border border-crm-border-strong bg-crm-card pl-2.5 pr-[9px] text-[12.5px] font-medium"
      >
        <span class="text-crm-muted-fg">{{ __('Author') }}</span>
        <span class="font-semibold text-crm-fg">{{ authorLabel }}</span>
        <LucideChevronDown class="size-3.5 text-crm-faint" aria-hidden="true" />
        <select
          v-model="author"
          class="absolute inset-0 cursor-pointer opacity-0"
          :aria-label="__('Author')"
        >
          <option value="">{{ __('Anyone') }}</option>
          <option v-for="u in crmUsers" :key="u.name" :value="u.name">
            {{ u.full_name || u.name }}
          </option>
        </select>
      </label>
    </div>

    <div
      v-if="board.data?.total"
      class="grid min-h-0 flex-1 grid-cols-1 gap-4 px-crm-page-x pb-6 pt-[10px] lg:grid-cols-[400px_1fr]"
    >
      <aside
        class="flex min-h-0 flex-col overflow-y-auto rounded-crm-panel border border-crm-border bg-crm-card"
      >
        <template v-for="(section, sectionIndex) in board.data.sections" :key="section.id">
          <p
            class="m-0 flex h-9 shrink-0 items-center px-4 text-[10.5px] font-bold uppercase tracking-[0.06em] text-crm-faint"
            :class="sectionIndex ? 'pt-[5px]' : 'pt-[3px]'"
          >
            {{ section.label }}
          </p>
          <button
            v-for="(note, noteIndex) in section.items"
            :key="note.name"
            type="button"
            class="block h-[86.5px] w-full shrink-0 border-t border-crm-border px-4 pb-3 text-left"
            :class="[
              sectionIndex ? 'pt-3' : 'pt-[11px]',
              selectedName === note.name
                ? 'bg-crm-row-selected shadow-[inset_3px_0_0_var(--crm-primary)]'
                : 'hover:bg-crm-row-hover',
            ]"
            @click="selectedName = note.name"
          >
            <div class="flex items-center gap-2">
              <b class="min-w-0 flex-1 truncate text-[13.3px] font-semibold text-crm-fg">
                {{ note.title }}
              </b>
              <span
                v-if="note.pinned"
                class="inline-flex h-[18px] shrink-0 items-center gap-1 rounded-[5px] border border-crm-warning/25 bg-crm-warning-soft px-1.5 text-[10.5px] font-semibold text-crm-warning"
              >
                <LucidePin class="size-2.5" aria-hidden="true" />
                {{ __('Pinned') }}
              </span>
              <span class="shrink-0 text-[11.5px] text-crm-faint">
                {{ note.time_label }}
              </span>
            </div>
            <p
              class="m-0 truncate text-[12px] tracking-[-0.005em] text-crm-muted-fg"
              :class="noteIndex % 2 ? 'mt-[3px]' : 'mt-[2px]'"
            >
              {{ note.preview }}
            </p>
            <p class="m-0 mt-[5px] truncate text-[11.5px] tracking-[-0.01em] text-crm-faint">
              <b class="font-semibold text-crm-primary">{{ note.record_label }}</b>
              · {{ note.owner_name }}
            </p>
          </button>
        </template>
      </aside>

      <section
        v-if="detail.data"
        class="flex min-h-0 flex-col overflow-hidden rounded-crm-panel border border-crm-border bg-crm-card"
      >
        <header
          class="flex h-[57px] shrink-0 items-center gap-2.5 border-b border-crm-border px-[18px]"
        >
          <h2
            class="m-0 truncate text-[14px] font-semibold tracking-[-0.005em] text-crm-fg"
          >
            {{ detail.data.title }}
          </h2>
          <span
            v-if="detail.data.pinned"
            class="inline-flex h-[18px] items-center gap-1 rounded-[5px] border border-crm-warning/25 bg-crm-warning-soft px-1.5 text-[10.5px] font-semibold text-crm-warning"
          >
            <LucidePin class="size-2.5" aria-hidden="true" />
            {{ pinnedBadgeLabel }}
          </span>
          <div class="flex-1" />
          <button
            type="button"
            class="inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-crm-muted-fg"
            @click="togglePin"
          >
            <LucidePin class="size-3.5" aria-hidden="true" />
            {{ detail.data.pinned ? __('Unpin') : __('Pin') }}
          </button>
          <AstraButton size="sm" :label="__('Edit')" @click="editNote(detail.data.name)" />
        </header>
        <!-- content is passed through sanitizeHTML() (DOMPurify) before rendering, so v-html is safe here -->
        <!-- eslint-disable vue/no-v-html -->
        <div
          class="note-body min-h-0 flex-1 overflow-y-auto px-[22px] pt-5 text-[13.4px] text-crm-fg"
          v-html="sanitizeHTML(detail.data.content || '')"
        />
        <!-- eslint-enable vue/no-v-html -->
        <footer
          class="flex h-[42px] shrink-0 items-center gap-4 border-t border-crm-border px-[22px] text-[12px] text-crm-muted-fg"
        >
          <router-link
            v-if="recordRoute"
            :to="recordRoute"
            class="hover:underline"
          >
            {{ __('Linked to') }}
            <b class="font-semibold text-crm-primary">{{ detail.data.linked_title }}</b>
          </router-link>
          <span>
            {{ __('By') }} {{ detail.data.owner_name }} ·
            {{ formatDate(detail.data.creation, 'DD MMM HH:mm') }}
          </span>
          <span v-if="detail.data.pinned && detail.data.pinned_on">
            {{ __('Pinned') }} {{ formatDate(detail.data.pinned_on, 'DD MMM') }}
          </span>
        </footer>
      </section>
    </div>

    <AstraEmptyState
      v-else-if="board.data"
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
import { computed, onMounted, ref, watch } from 'vue'
import { call, createResource, usePageMeta } from 'frappe-ui'
import LucideChevronDown from '~icons/lucide/chevron-down'
import LucidePin from '~icons/lucide/pin'
import LucidePlus from '~icons/lucide/plus'
import LucideSearch from '~icons/lucide/search'
import { AstraBadge, AstraButton, AstraEmptyState } from '@/components/astra'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useNoteView } from '@/composables/noteView'
import { usersStore } from '@/stores/users'
import { formatDate, sanitizeHTML } from '@/utils'
import { useTelemetry } from '@framework/ui/telemetry'
import { getSettings } from '@/stores/settings'
import { ASTRA_FAVICON } from '@/assets/brand'

const { brand } = getSettings()
const { crmUsers: crmUsersRef } = usersStore()
const { capture } = useTelemetry()
const { showModal } = useDoctypeModal()
const { openNote } = useNoteView()

const crmUsers = computed(() => crmUsersRef.value || [])
const search = ref('')
const linkedDoctype = ref('')
const author = ref('')
const selectedName = ref(null)

const board = createResource({
  url: 'crm.api.notes_page.get_notes',
  auto: true,
  makeParams: () => ({
    search: search.value || undefined,
    linked_doctype: linkedDoctype.value || undefined,
    author: author.value || undefined,
  }),
})

const detail = createResource({
  url: 'crm.api.notes_page.get_note',
  makeParams: () => ({ name: selectedName.value }),
})

const allItems = computed(() =>
  (board.data?.sections || []).flatMap((s) => s.items),
)
const linkedLabelText = computed(
  () =>
    ({ 'CRM Lead': __('Lead'), 'CRM Deal': __('Deal') })[linkedDoctype.value] ||
    __('Any'),
)
const authorLabel = computed(() => {
  const u = crmUsers.value.find((x) => x.name === author.value)
  return u ? u.full_name || u.name : __('Anyone')
})
const pinnedBadgeLabel = computed(() =>
  detail.data?.pinned_by
    ? __('Pinned by {0}', [detail.data.pinned_by])
    : __('Pinned'),
)
const recordRoute = computed(() => {
  const d = detail.data
  if (!d?.reference_docname) return null
  if (d.reference_doctype === 'CRM Deal')
    return { name: 'Deal', params: { dealId: d.reference_docname } }
  if (d.reference_doctype === 'CRM Lead')
    return { name: 'Lead', params: { leadId: d.reference_docname } }
  return null
})

let searchTimer
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => board.reload(), 250)
})
watch([linkedDoctype, author], () => board.reload())

watch(
  () => board.data,
  () => {
    const names = allItems.value.map((n) => n.name)
    if (!names.length) {
      selectedName.value = null
      return
    }
    if (!selectedName.value || !names.includes(selectedName.value)) {
      selectedName.value = names[0]
    }
  },
)
watch(selectedName, (name) => name && detail.fetch(), { immediate: true })

const noteCallbacks = {
  afterInsert: () => {
    board.reload()
    capture('note_created')
  },
  afterUpdate: () => {
    board.reload()
    detail.reload()
    capture('note_updated')
  },
}

function createNote() {
  showModal({ doctype: 'FCRM Note', title: 'Note', callbacks: noteCallbacks })
}

function editNote(name) {
  showModal({
    name,
    doctype: 'FCRM Note',
    title: 'Note',
    callbacks: noteCallbacks,
  })
}

async function togglePin() {
  await call('crm.fcrm.doctype.fcrm_note.fcrm_note.set_pinned', {
    name: detail.data.name,
    pinned: !detail.data.pinned,
  })
  await Promise.all([board.reload(), detail.reload()])
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

<style scoped>
.note-body :deep(p) {
  margin: 0 0 17px;
  line-height: 20px;
}
.note-body :deep(p:first-child) {
  margin-bottom: 16px;
}
.note-body :deep(p:nth-child(2)) {
  margin-bottom: 18px;
}
.note-body :deep(ul) {
  margin: 0 0 17px;
  padding-left: 20px;
  list-style: disc;
}
.note-body :deep(li) {
  margin: 0 0 7px;
  line-height: 20px;
}
.note-body :deep(li:first-child) {
  margin-bottom: 6px;
}
.note-body :deep(small) {
  font-size: 12px;
  color: var(--crm-muted-fg);
}
</style>
