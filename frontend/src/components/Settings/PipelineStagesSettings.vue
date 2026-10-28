<template>
  <div class="flex h-full min-h-0 flex-col text-ink-gray-8">
    <div class="flex items-start justify-between gap-4 px-6 pt-6 pb-3">
      <div class="flex min-w-0 flex-col gap-1">
        <h2 class="text-2xl-semibold leading-none">
          {{ __('Pipeline stages') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Order, type, probability and colour drive the board, the stage path and reports.',
            )
          }}
        </p>
      </div>
      <div class="flex shrink-0 items-center gap-2">
        <Button
          :label="__('Discard')"
          :disabled="!dirty || saving"
          @click="discard"
        />
        <Button
          variant="solid"
          :label="__('Save changes')"
          :loading="saving"
          :disabled="!dirty"
          @click="save"
        />
      </div>
    </div>

    <div class="flex items-center gap-2 px-6 pb-4">
      <button
        v-for="tab in tabs"
        :key="tab.parent"
        type="button"
        class="rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
        :class="
          activeParent === tab.parent
            ? 'bg-[var(--crm-primary-soft,var(--surface-gray-3))] text-[var(--crm-primary,var(--ink-gray-9))]'
            : 'text-ink-gray-6 hover:bg-surface-gray-2'
        "
        :aria-selected="activeParent === tab.parent"
        @click="switchTab(tab.parent)"
      >
        {{ tab.label }}
        <span class="ml-1 text-ink-gray-5">({{ tab.count }})</span>
      </button>
    </div>

    <div class="flex min-h-0 flex-1 gap-4 overflow-hidden px-6 pb-6">
      <div class="flex min-w-0 flex-1 flex-col overflow-hidden">
        <div
          v-if="loading"
          class="flex flex-1 items-center justify-center text-ink-gray-5"
        >
          {{ __('Loading…') }}
        </div>
        <template v-else>
          <div
            class="mb-2 hidden grid-cols-[28px_36px_minmax(0,1.4fr)_120px_100px_72px_88px_40px] gap-2 px-2 text-[11.5px] font-semibold text-ink-gray-5 sm:grid"
          >
            <span />
            <span>#</span>
            <span>{{ __('Stage') }}</span>
            <span>{{ __('Type') }}</span>
            <span>{{ isDeal ? __('Probability') : '' }}</span>
            <span>{{ __('Colour') }}</span>
            <span>{{ __('In use') }}</span>
            <span />
          </div>
          <Draggable
            :list="draft"
            item-key="_key"
            handle=".stage-drag-handle"
            class="flex flex-col gap-1.5 overflow-y-auto pr-1"
            @end="renumber"
          >
            <template #item="{ element: stage, index }">
              <div
                class="grid grid-cols-[28px_minmax(0,1fr)] items-center gap-2 rounded-lg border border-outline-gray-2 bg-surface-white px-2 py-2 sm:grid-cols-[28px_36px_minmax(0,1.4fr)_120px_100px_72px_88px_40px]"
              >
                <button
                  type="button"
                  class="stage-drag-handle flex h-8 w-7 cursor-grab items-center justify-center text-ink-gray-4"
                  :aria-label="__('Drag to reorder')"
                >
                  <span
                    class="lucide-grip-vertical h-4 w-4"
                    aria-hidden="true"
                  />
                </button>
                <div class="flex flex-col gap-2 sm:contents">
                  <span class="hidden text-sm text-ink-gray-5 sm:block">{{
                    index + 1
                  }}</span>
                  <TextInput
                    v-model="stage.label"
                    class="w-full"
                    :placeholder="__('Stage name')"
                  />
                  <FormControl
                    v-model="stage.type"
                    type="select"
                    :options="typeOptions"
                  />
                  <FormControl
                    v-if="isDeal"
                    v-model="stage.probability"
                    type="select"
                    :options="probabilityOptions"
                  />
                  <span v-else class="hidden sm:block" />
                  <div class="relative">
                    <button
                      type="button"
                      class="flex h-8 w-8 items-center justify-center rounded-full border border-outline-gray-2"
                      :style="stageColourStyle(stage.color, stage.label)"
                      :aria-label="__('Pick colour')"
                      @click.stop="togglePalette(stage._key)"
                    />
                    <div
                      v-if="openPaletteKey === stage._key"
                      class="absolute left-0 top-9 z-20 grid grid-cols-5 gap-1.5 rounded-lg border border-outline-gray-2 bg-surface-white p-2 shadow-md"
                    >
                      <button
                        v-for="c in ASTRA_STAGE_COLOURS"
                        :key="c"
                        type="button"
                        class="h-6 w-6 rounded-full border border-outline-gray-1"
                        :class="
                          stage.color === c
                            ? 'ring-2 ring-[var(--crm-primary,#0a7393)]'
                            : ''
                        "
                        :style="stageColourStyle(c)"
                        :title="c"
                        @click.stop="pickColour(stage, c)"
                      />
                    </div>
                  </div>
                  <span class="truncate text-xs text-ink-gray-5">
                    {{ inUseLabel(stage) }}
                  </span>
                  <Dropdown :options="rowOptions(stage)" align="end">
                    <template #default>
                      <Button variant="ghost" icon="lucide-more-horizontal" />
                    </template>
                  </Dropdown>
                </div>
              </div>
            </template>
          </Draggable>
          <button
            type="button"
            class="mt-3 flex h-11 items-center justify-center gap-2 rounded-lg border border-dashed border-outline-gray-3 text-sm font-medium text-ink-gray-6 hover:border-[var(--crm-primary,#0a7393)] hover:text-[var(--crm-primary,#0a7393)]"
            @click="addStage"
          >
            <span class="lucide-plus h-4 w-4" aria-hidden="true" />
            {{ __('Add stage') }}
          </button>
        </template>
      </div>

      <aside class="hidden w-64 shrink-0 flex-col gap-3 lg:flex">
        <div
          class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 text-sm text-ink-gray-6"
        >
          <div class="mb-1 font-semibold text-ink-gray-8">
            {{ __('How types group stages') }}
          </div>
          {{
            __(
              'Open · Ongoing · On Hold show as columns on the board. Won · Lost collapse into the Closed lane.',
            )
          }}
        </div>
        <div
          class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 text-sm text-ink-gray-6"
        >
          {{
            __(
              'Colours are limited to the Astra palette so stages stay readable in light and dark.',
            )
          }}
        </div>
      </aside>
    </div>

    <Dialog v-model="showRemap" :options="{ title: __('Move records first') }">
      <template #body-content>
        <p class="mb-3 text-p-base text-ink-gray-6">
          {{
            __(
              '{0} is in use. Choose another stage for those records before deleting.',
              [pendingDelete?.label || ''],
            )
          }}
        </p>
        <FormControl
          v-model="remapTo"
          type="select"
          :label="__('Map records to')"
          :options="remapOptions"
        />
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button :label="__('Cancel')" @click="showRemap = false" />
          <Button
            variant="solid"
            theme="red"
            :label="__('Delete stage')"
            :disabled="!remapTo && (pendingDelete?.in_use || 0) > 0"
            :loading="deleting"
            @click="confirmDelete"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import {
  ASTRA_STAGE_COLOURS,
  stageColourStyle,
  toAstraStageColour,
} from '@/utils/stageColours'
import { statusesStore } from '@/stores/statuses'
import {
  Button,
  Dialog,
  Dropdown,
  FormControl,
  TextInput,
  call,
  toast,
} from 'frappe-ui'
import Draggable from 'vuedraggable'
import { computed, onMounted, onUnmounted, ref } from 'vue'

const PARENTS = {
  deal: 'CRM Deal',
  lead: 'CRM Lead',
}

const typeOptions = ['Open', 'Ongoing', 'On Hold', 'Won', 'Lost']
const probabilityOptions = [0, 10, 25, 50, 70, 90, 100].map((n) => ({
  label: `${n}%`,
  value: String(n),
}))

const activeParent = ref(PARENTS.deal)
const draft = ref([])
const original = ref([])
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const openPaletteKey = ref(null)
const showRemap = ref(false)
const pendingDelete = ref(null)
const remapTo = ref('')
let keySeq = 0

const { dealStatuses, leadStatuses } = statusesStore()

const isDeal = computed(() => activeParent.value === PARENTS.deal)

const tabs = computed(() => [
  {
    parent: PARENTS.deal,
    label: __('Deal stages'),
    count:
      activeParent.value === PARENTS.deal
        ? draft.value.length
        : dealStatuses.data?.length || 0,
  },
  {
    parent: PARENTS.lead,
    label: __('Lead statuses'),
    count:
      activeParent.value === PARENTS.lead
        ? draft.value.length
        : leadStatuses.data?.length || 0,
  },
])

const dirty = computed(
  () => JSON.stringify(draft.value) !== JSON.stringify(original.value),
)

const remapOptions = computed(() =>
  draft.value
    .filter((s) => s.name && s.name !== pendingDelete.value?.name)
    .map((s) => ({ label: s.label, value: s.name })),
)

onMounted(() => {
  load()
  document.addEventListener('click', closePaletteOnOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', closePaletteOnOutside)
})

function closePaletteOnOutside() {
  openPaletteKey.value = null
}

function nextKey() {
  keySeq += 1
  return `stage-${keySeq}`
}

function normalizeRow(row) {
  return {
    _key: nextKey(),
    name: row.name || null,
    label: row.label || row.name || '',
    type: row.type || 'Open',
    color: toAstraStageColour(row.color, row.label || row.name),
    position: row.position || 0,
    probability: String(row.probability ?? (row.type === 'Won' ? 100 : 0)),
    in_use: row.in_use || 0,
  }
}

async function load() {
  loading.value = true
  try {
    const rows = await call('crm.api.pipeline_stages.get_pipeline_stages', {
      parent_doctype: activeParent.value,
    })
    const normalized = (rows || []).map(normalizeRow)
    draft.value = normalized
    original.value = JSON.parse(JSON.stringify(normalized))
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Failed to load stages'))
  } finally {
    loading.value = false
  }
}

function switchTab(parent) {
  if (parent === activeParent.value) return
  if (dirty.value && !window.confirm(__('Discard unsaved changes?'))) return
  activeParent.value = parent
  openPaletteKey.value = null
  load()
}

function renumber() {
  draft.value.forEach((s, i) => {
    s.position = i + 1
  })
}

function addStage() {
  draft.value.push(
    normalizeRow({
      label: __('New stage'),
      type: 'Open',
      color: 'c6',
      position: draft.value.length + 1,
      probability: 0,
      in_use: 0,
    }),
  )
}

function togglePalette(key) {
  openPaletteKey.value = openPaletteKey.value === key ? null : key
}

function pickColour(stage, color) {
  stage.color = color
  openPaletteKey.value = null
}

function inUseLabel(stage) {
  const n = stage.in_use || 0
  if (!n) return __('None')
  if (isDeal.value) {
    return n === 1 ? __('1 deal') : __('{0} deals', [n])
  }
  return n === 1 ? __('1 lead') : __('{0} leads', [n])
}

function rowOptions(stage) {
  return [
    {
      label: __('Delete'),
      icon: 'lucide-trash-2',
      onClick: () => requestDelete(stage),
    },
  ]
}

function requestDelete(stage) {
  if (!stage.name) {
    draft.value = draft.value.filter((s) => s._key !== stage._key)
    renumber()
    return
  }
  pendingDelete.value = stage
  remapTo.value = ''
  showRemap.value = true
}

async function confirmDelete() {
  const stage = pendingDelete.value
  if (!stage?.name) {
    showRemap.value = false
    return
  }
  if ((stage.in_use || 0) > 0 && !remapTo.value) return
  deleting.value = true
  try {
    await call('crm.api.pipeline_stages.delete_pipeline_stage', {
      parent_doctype: activeParent.value,
      stage: stage.name,
      remap_to: remapTo.value || null,
    })
    toast.success(__('Stage deleted'))
    showRemap.value = false
    await load()
    refreshStatusStore()
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Could not delete stage'))
  } finally {
    deleting.value = false
  }
}

function discard() {
  draft.value = JSON.parse(JSON.stringify(original.value))
}

function payload() {
  return draft.value.map((s, i) => ({
    name: s.name,
    label: s.label,
    type: s.type,
    color: s.color,
    position: i + 1,
    ...(isDeal.value ? { probability: Number(s.probability) || 0 } : {}),
  }))
}

async function save() {
  saving.value = true
  try {
    await call('crm.api.pipeline_stages.save_pipeline_stages', {
      parent_doctype: activeParent.value,
      stages: payload(),
    })
    toast.success(__('Stages saved'))
    await load()
    refreshStatusStore()
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Could not save stages'))
  } finally {
    saving.value = false
  }
}

function refreshStatusStore() {
  dealStatuses.reload?.()
  leadStatuses.reload?.()
}
</script>
