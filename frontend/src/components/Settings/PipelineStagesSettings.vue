<template>
  <div class="flex h-full min-h-0 flex-col bg-crm-bg text-crm-fg">
    <div
      class="mx-crm-page-x mt-0 flex h-[30px] items-center gap-2 border-b border-dashed border-crm-border-strong bg-crm-muted px-0 text-crm-label text-crm-muted-fg"
      style="
        margin-left: var(--crm-page-x, 24px);
        margin-right: var(--crm-page-x, 24px);
      "
    >
      <Icon icon="triangle-alert" class="size-3.5 shrink-0 text-crm-warning" />
      <span>
        <span class="font-semibold text-crm-fg">{{ __('Concept') }}</span>
        {{
          __(
            ': In-app stage editor. Stages are real, configurable records today; this editor screen is new and needs backend work.',
          )
        }}
      </span>
    </div>
    <AstraPageHeader
      :title="__('Pipeline stages')"
      :description="
        __(
          'Order, type, probability and colour drive the board, the stage path and reports.',
        )
      "
    >
      <template #actions>
        <ExampleDataTag />
        <AstraButton
          :label="__('Discard')"
          :disabled="!dirty || saving"
          @click="discard"
        />
        <AstraButton
          variant="primary"
          :label="__('Save changes')"
          :loading="saving"
          :disabled="!dirty"
          @click="save"
        />
      </template>
    </AstraPageHeader>

    <div
      class="flex items-center gap-1 border-b border-crm-border px-crm-page-x"
      role="tablist"
    >
      <button
        v-for="tab in tabs"
        :key="tab.parent"
        type="button"
        role="tab"
        class="inline-flex h-[38px] items-center gap-1.5 border-b-2 px-2.5 text-crm-body font-medium"
        :class="
          activeParent === tab.parent
            ? 'border-crm-primary font-semibold text-crm-fg'
            : 'border-transparent text-crm-muted-fg'
        "
        :aria-selected="activeParent === tab.parent"
        @click="switchTab(tab.parent)"
      >
        {{ tab.label }}
        <span
          class="inline-flex h-4 min-w-4 items-center justify-center rounded bg-crm-neutral-soft px-1 text-crm-micro font-semibold text-crm-muted-fg"
        >
          {{ tab.count }}
        </span>
      </button>
    </div>

    <div class="min-h-0 flex-1 overflow-y-auto px-crm-page-x pb-6 pt-4">
      <div
        v-if="loading"
        class="py-16 text-center text-crm-body text-crm-muted-fg"
      >
        {{ __('Loading…') }}
      </div>
      <div v-else class="flex items-start gap-4">
        <div
          class="min-w-0 flex-1 overflow-hidden rounded-crm-panel border border-crm-border bg-crm-card"
        >
          <div class="overflow-x-auto">
            <div class="min-w-0">
              <div
                class="grid h-crm-th items-center gap-2 bg-crm-muted px-4 text-crm-meta font-semibold text-crm-muted-fg"
                :class="rowGridClass"
              >
                <span />
                <span>#</span>
                <span>{{ __('Stage') }}</span>
                <span>{{ __('Type') }}</span>
                <span v-if="isDeal">{{ __('Probability') }}</span>
                <span>{{ __('Colour') }}</span>
                <span>{{ __('In use') }}</span>
                <span />
              </div>
              <Draggable
                :list="draft"
                item-key="_key"
                handle=".stage-drag-handle"
                @end="renumber"
              >
                <template #item="{ element: stage, index }">
                  <div
                    class="grid h-[46px] items-center gap-2 border-t border-crm-border px-4"
                    :class="[
                      rowGridClass,
                      highlightedKey === stage._key
                        ? 'bg-crm-row-selected shadow-[inset_0_0_0_1.5px_var(--crm-primary)]'
                        : 'bg-crm-card',
                    ]"
                    @click="selectedKey = stage._key"
                  >
                    <button
                      type="button"
                      class="stage-drag-handle flex size-7 cursor-grab items-center justify-center text-crm-faint"
                      :aria-label="__('Drag to reorder')"
                      @click.stop
                    >
                      <Icon icon="grip-vertical" class="size-4" />
                    </button>
                    <span
                      class="inline-flex size-6 items-center justify-center rounded-crm-mini bg-crm-muted text-crm-micro font-semibold text-crm-muted-fg"
                    >
                      {{ index + 1 }}
                    </span>
                    <label
                      class="flex h-8 min-w-0 items-center gap-2 rounded-crm-control-sm bg-crm-card px-2 shadow-[inset_0_0_0_1px_var(--crm-border)]"
                    >
                      <span
                        class="size-[7px] shrink-0 rounded-[2px]"
                        :style="stageColourStyle(stage.color, stage.label)"
                      />
                      <input
                        v-model="stage.label"
                        class="min-w-0 flex-1 bg-transparent text-crm-label text-crm-fg outline-none"
                        :placeholder="__('Stage name')"
                        @click.stop
                      />
                    </label>
                    <label
                      class="relative inline-flex h-[22px] max-w-full items-center rounded-crm-chip px-2"
                      :class="typeTone(stage.type)"
                      @click.stop
                    >
                      <select
                        v-model="stage.type"
                        class="w-full cursor-pointer appearance-none bg-transparent pr-4 text-crm-meta font-semibold outline-none"
                      >
                        <option
                          v-for="type in typeOptions"
                          :key="type"
                          :value="type"
                        >
                          {{ __(type) }}
                        </option>
                      </select>
                      <Icon
                        icon="chevron-down"
                        class="pointer-events-none absolute right-1.5 size-3"
                      />
                    </label>
                    <label
                      v-if="isDeal"
                      class="relative inline-flex h-[22px] items-center rounded-crm-chip bg-crm-muted px-2 text-crm-fg"
                      @click.stop
                    >
                      <select
                        v-model="stage.probability"
                        class="w-full cursor-pointer appearance-none bg-transparent pr-4 text-crm-meta font-semibold outline-none"
                      >
                        <option
                          v-for="option in probabilityOptions"
                          :key="option.value"
                          :value="option.value"
                        >
                          {{ option.label }}
                        </option>
                      </select>
                      <Icon
                        icon="chevron-down"
                        class="pointer-events-none absolute right-1.5 size-3 text-crm-faint"
                      />
                    </label>
                    <div class="relative" @click.stop>
                      <button
                        type="button"
                        class="size-4 rounded-full border border-crm-border"
                        :style="stageColourStyle(stage.color, stage.label)"
                        :aria-label="__('Pick colour')"
                        @click="togglePalette(stage._key)"
                      />
                      <div
                        v-if="openPaletteKey === stage._key"
                        class="absolute left-0 top-7 z-20 grid grid-cols-5 gap-1.5 rounded-crm-control border border-crm-border bg-crm-card p-2 shadow-crm-modal"
                      >
                        <button
                          v-for="c in ASTRA_STAGE_COLOURS"
                          :key="c"
                          type="button"
                          class="size-6 rounded-full border border-crm-border"
                          :class="
                            stage.color === c ? 'ring-2 ring-crm-primary' : ''
                          "
                          :style="stageColourStyle(c)"
                          :title="c"
                          @click="pickColour(stage, c)"
                        />
                      </div>
                    </div>
                    <span class="truncate text-crm-meta text-crm-muted-fg">
                      {{ inUseLabel(stage) }}
                    </span>
                    <Dropdown :options="rowOptions(stage)" align="end">
                      <template #default>
                        <button
                          type="button"
                          class="inline-flex size-7 items-center justify-center rounded-crm-chip text-crm-faint hover:bg-crm-muted"
                          :aria-label="__('More')"
                          @click.stop
                        >
                          <Icon icon="more-horizontal" class="size-4" />
                        </button>
                      </template>
                    </Dropdown>
                  </div>
                </template>
              </Draggable>
            </div>
          </div>
          <button
            type="button"
            class="mx-3 mb-3 mt-3 flex h-11 w-[calc(100%-1.5rem)] items-center justify-center gap-1.5 rounded-crm-control border border-dashed border-crm-border-strong text-crm-label font-semibold text-crm-primary hover:bg-crm-primary-soft"
            @click="addStage"
          >
            <Icon icon="plus" class="size-4" />
            {{ __('Add stage') }}
          </button>
        </div>

        <aside class="hidden w-[260px] shrink-0 flex-col gap-3 lg:flex">
          <div
            class="rounded-crm-panel border border-crm-border bg-crm-card p-3.5"
          >
            <h2 class="text-crm-panel font-semibold text-crm-fg">
              {{ __('How types group stages') }}
            </h2>
            <div class="mt-3 flex flex-col gap-3">
              <div class="flex gap-2">
                <span
                  class="inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-crm-muted text-crm-micro font-semibold text-crm-muted-fg"
                >
                  1
                </span>
                <div>
                  <div class="text-crm-label font-semibold text-crm-fg">
                    {{ __('Open · Ongoing · On Hold') }}
                  </div>
                  <p class="mt-0.5 text-crm-meta text-crm-muted-fg">
                    {{
                      __(
                        'Shown as columns on the board and steps on the stage path.',
                      )
                    }}
                  </p>
                </div>
              </div>
              <div class="flex gap-2">
                <span
                  class="inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-crm-muted text-crm-micro font-semibold text-crm-muted-fg"
                >
                  2
                </span>
                <div>
                  <div class="text-crm-label font-semibold text-crm-fg">
                    {{ __('Won · Lost') }}
                  </div>
                  <p class="mt-0.5 text-crm-meta text-crm-muted-fg">
                    {{
                      __('Collapsed into the Closed lane, used for win rate.')
                    }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div
            v-if="moveNotice"
            class="rounded-crm-panel border border-crm-border bg-crm-card p-3.5"
          >
            <div class="flex gap-2">
              <Icon
                icon="triangle-alert"
                class="mt-0.5 size-4 shrink-0 text-crm-warning"
              />
              <div>
                <p class="text-crm-label font-semibold text-crm-fg">
                  {{
                    __('Moving {0} above {1}', [
                      moveNotice.stage.label,
                      moveNotice.above.label,
                    ])
                  }}
                </p>
                <p class="mt-1 text-crm-meta text-crm-muted-fg">
                  {{ moveDetail }}
                </p>
              </div>
            </div>
          </div>

          <div
            class="flex gap-2 rounded-crm-panel border border-crm-border bg-crm-card p-3.5"
          >
            <Icon
              icon="palette"
              class="mt-0.5 size-4 shrink-0 text-crm-faint"
            />
            <p class="text-crm-meta text-crm-muted-fg">
              {{
                __(
                  'Colours are limited to the Astra palette so stages stay readable in light and dark.',
                )
              }}
            </p>
          </div>
        </aside>
      </div>
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
import ExampleDataTag from '@/components/astra/ExampleDataTag.vue'
import AstraButton from '@/components/astra/AstraButton.vue'
import AstraPageHeader from '@/components/astra/AstraPageHeader.vue'
import Icon from '@/components/Icon.vue'
import {
  ASTRA_STAGE_COLOURS,
  stageColourStyle,
  toAstraStageColour,
} from '@/utils/stageColours'
import { statusesStore } from '@/stores/statuses'
import { Dialog, Dropdown, FormControl, call, toast } from 'frappe-ui'
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

const TYPE_TONE = {
  Open: 'bg-crm-neutral-soft text-crm-muted-fg',
  Ongoing: 'bg-crm-blue-soft text-crm-blue',
  'On Hold': 'bg-crm-warning-soft text-crm-warning',
  Won: 'bg-crm-success-soft text-crm-success',
  Lost: 'bg-crm-danger-soft text-crm-danger',
}

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
const selectedKey = ref(null)
let keySeq = 0

const { dealStatuses, leadStatuses } = statusesStore()

const isDeal = computed(() => activeParent.value === PARENTS.deal)

const rowGridClass = computed(() =>
  isDeal.value
    ? 'grid-cols-[24px_28px_minmax(0,1.6fr)_108px_76px_36px_72px_28px]'
    : 'grid-cols-[24px_28px_minmax(0,1.6fr)_108px_36px_72px_28px]',
)

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

const moveNotice = computed(() => {
  const before = original.value.map((stage) => stage._key)
  const after = draft.value
    .map((stage) => stage._key)
    .filter((key) => before.includes(key))
  const beforeExisting = before.filter((key) => after.includes(key))
  for (let i = 0; i < after.length; i++) {
    const prev = beforeExisting.indexOf(after[i])
    if (prev <= i) continue
    const stage = draft.value.find((row) => row._key === after[i])
    const above = draft.value.find((row) => row._key === after[i + 1])
    if (stage && above) return { stage, above }
  }
  return null
})

const highlightedKey = computed(
  () => moveNotice.value?.stage._key || selectedKey.value,
)

const moveDetail = computed(() => {
  const notice = moveNotice.value
  if (!notice) return ''
  const n = notice.stage.in_use || 0
  const kept = isDeal.value
    ? n === 1
      ? __('1 deal keeps its stage.')
      : __('{0} deals keep their stage.', [n])
    : n === 1
      ? __('1 lead keeps its stage.')
      : __('{0} leads keep their stage.', [n])
  return `${kept} ${__('Board columns and stage path update for everyone after you save.')}`
})

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

function typeTone(type) {
  return TYPE_TONE[type] || TYPE_TONE.Open
}

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
  selectedKey.value = null
  try {
    const rows = await call('crm.api.pipeline_stages.get_pipeline_stages', {
      parent_doctype: activeParent.value,
    })
    const normalized = (rows || []).map(normalizeRow)
    draft.value = normalized
    original.value = JSON.parse(JSON.stringify(normalized))
    // Figma 21 shows Negotiation selected with the reorder notice card.
    const negotiation = draft.value.find((s) => s.label === 'Negotiation')
    const proposal = draft.value.find((s) => s.label === 'Proposal/Quotation')
    if (negotiation && proposal && isDeal.value) {
      const from = draft.value.findIndex((s) => s._key === negotiation._key)
      const to = draft.value.findIndex((s) => s._key === proposal._key)
      if (from > to) {
        const [row] = draft.value.splice(from, 1)
        draft.value.splice(to, 0, row)
        renumber()
      }
      selectedKey.value = negotiation._key
    }
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
  selectedKey.value = null
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
