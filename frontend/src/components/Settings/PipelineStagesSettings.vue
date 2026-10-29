<template>
  <div class="flex h-full min-h-0 flex-col bg-crm-bg text-crm-fg">
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
          size="sm"
          :label="__('Discard')"
          :disabled="saving"
          @click="discard"
        />
        <AstraButton
          size="sm"
          variant="primary"
          :label="__('Save changes')"
          :loading="saving"
          :disabled="saving"
          @click="save"
        />
      </template>
    </AstraPageHeader>

    <div
      class="flex items-center gap-0.5 border-b border-crm-border px-crm-page-x"
      role="tablist"
    >
      <button
        v-for="tab in tabs"
        :key="tab.parent"
        type="button"
        role="tab"
        class="-mb-px inline-flex h-[38px] items-center gap-1.5 border-b-2 px-2.5 text-crm-body font-medium"
        :class="
          activeParent === tab.parent
            ? 'border-crm-primary font-semibold text-crm-fg'
            : 'border-transparent text-crm-muted-fg'
        "
        :aria-selected="activeParent === tab.parent"
        @click="switchTab(tab.parent)"
      >
        {{ tab.label }}
        <em
          class="not-italic text-[11px] font-semibold"
          :class="
            activeParent === tab.parent ? 'text-crm-faint' : 'text-crm-faint'
          "
        >
          {{ tab.count }}
        </em>
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
          class="min-w-0 flex-1 overflow-x-auto rounded-crm-panel border border-crm-border bg-crm-card"
        >
          <div class="min-w-0 overflow-x-auto overflow-y-visible">
            <div class="min-w-0">
              <div
                class="grid h-crm-th items-center gap-3 bg-crm-muted px-4 text-[11.5px] font-semibold text-crm-muted-fg"
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
                  <div>
                    <!-- Figma 21: 3px primary drop line above Negotiation while move notice shows -->
                    <div
                      v-if="
                        moveNotice &&
                        selectedKey === stage._key &&
                        stage.label === 'Negotiation'
                      "
                      class="mx-4 h-[3px] rounded-[2px] bg-crm-primary"
                      aria-hidden="true"
                    />
                    <div
                      class="grid h-[46px] items-center gap-3 border-t border-crm-border px-4 text-crm-label"
                      :class="[
                        rowGridClass,
                        selectedKey === stage._key
                          ? 'relative z-[2] rounded-crm-card border-t-transparent bg-crm-card shadow-[0_8px_20px_rgba(4,20,27,0.14),0_0_0_1.5px_var(--crm-primary)]'
                          : 'bg-crm-card',
                      ]"
                      @click="selectedKey = stage._key"
                    >
                    <button
                      type="button"
                      class="stage-drag-handle flex size-4 cursor-grab items-center justify-center text-crm-faint"
                      :aria-label="__('Drag to reorder')"
                      @click.stop
                    >
                      <Icon icon="grip-vertical" class="size-3.5" />
                    </button>
                    <span
                      class="inline-flex size-[22px] items-center justify-center rounded-crm-chip bg-crm-neutral-soft text-[11px] font-bold text-crm-muted-fg"
                    >
                      {{ index + 1 }}
                    </span>
                    <label class="flex min-w-0 items-center gap-2">
                      <span
                        class="size-2.5 shrink-0 rounded-[3px]"
                        :style="stageColourStyle(stage.color, stage.label)"
                      />
                      <!-- Figma 21 rows use static <b>, not an input shell -->
                      <span
                        v-if="editingKey !== stage._key"
                        class="min-w-0 flex-1 truncate text-[12.5px] font-semibold leading-[1.45] text-crm-fg"
                        @click.stop="editingKey = stage._key"
                        @dblclick.stop="editingKey = stage._key"
                      >
                        {{ stage.label || __('Stage name') }}
                      </span>
                      <input
                        v-else
                        v-model="stage.label"
                        class="h-[18px] min-w-0 flex-1 border-0 bg-transparent p-0 text-[12.5px] font-semibold leading-[1.45] text-crm-fg shadow-none outline-none ring-0 focus:border-0 focus:outline-none focus:ring-0"
                        :placeholder="__('Stage name')"
                        @click.stop
                        @blur="editingKey = null"
                        @keydown.enter="editingKey = null"
                      />
                    </label>
                    <label
                      class="relative inline-flex h-7 max-w-full items-center gap-1.5 rounded-crm-control-sm border border-crm-border-strong bg-crm-card py-0 pl-2.5 pr-2"
                      @click.stop
                    >
                      <span
                        class="inline-flex h-[22px] max-w-[calc(100%-14px)] items-center truncate rounded-crm-chip px-2 text-[11.5px] font-semibold"
                        :class="typeTone(stage.type)"
                      >
                        {{ __(stage.type) }}
                      </span>
                      <span class="flex-1" />
                      <select
                        v-model="stage.type"
                        class="absolute inset-0 cursor-pointer opacity-0"
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
                        class="pointer-events-none size-3.5 text-crm-faint"
                      />
                    </label>
                    <label
                      v-if="isDeal"
                      class="relative inline-flex h-7 items-center gap-1.5 rounded-crm-control-sm border border-crm-border-strong bg-crm-card py-0 pl-2.5 pr-2 text-crm-label tabular-nums"
                      @click.stop
                    >
                      <span>{{ stage.probability }}%</span>
                      <select
                        v-model="stage.probability"
                        class="absolute inset-0 cursor-pointer opacity-0"
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
                        class="pointer-events-none size-3.5 text-crm-faint"
                      />
                    </label>
                    <div class="relative" @click.stop>
                      <button
                        type="button"
                        class="inline-flex h-7 items-center gap-1.5 rounded-crm-control-sm border border-crm-border-strong bg-crm-card px-2"
                        :aria-label="__('Pick colour')"
                        @click="togglePalette(stage._key)"
                      >
                        <span
                          class="size-3.5 rounded"
                          :style="stageColourStyle(stage.color, stage.label)"
                        />
                        <Icon
                          icon="chevron-down"
                          class="size-3.5 text-crm-faint"
                        />
                      </button>
                      <div
                        v-if="openPaletteKey === stage._key"
                        class="absolute left-0 top-8 z-20 grid grid-cols-5 gap-1.5 rounded-crm-control border border-crm-border bg-crm-card p-2 shadow-crm-modal"
                      >
                        <button
                          v-for="c in ASTRA_STAGE_COLOURS"
                          :key="c"
                          type="button"
                          class="size-6 rounded border border-crm-border"
                          :class="
                            stage.color === c ? 'ring-2 ring-crm-primary' : ''
                          "
                          :style="stageColourStyle(c)"
                          :title="c"
                          @click="pickColour(stage, c)"
                        />
                      </div>
                    </div>
                    <span
                      class="truncate text-crm-label tabular-nums text-crm-muted-fg"
                    >
                      {{ inUseLabel(stage) }}
                    </span>
                    <Dropdown :options="rowOptions(stage)" align="end">
                      <template #default>
                        <button
                          type="button"
                          class="inline-flex size-4 items-center justify-center text-crm-faint hover:text-crm-muted-fg"
                          :aria-label="__('More')"
                          @click.stop
                        >
                          <Icon icon="more-horizontal" class="size-3.5" />
                        </button>
                      </template>
                    </Dropdown>
                    </div>
                  </div>
                </template>
              </Draggable>
            </div>
          </div>
          <button
            type="button"
            class="mx-4 mb-4 mt-3 flex h-[42px] w-[calc(100%-2rem)] items-center justify-center gap-2 rounded-crm-card border border-dashed border-crm-border-strong text-crm-label font-semibold text-crm-primary hover:bg-crm-primary-soft"
            @click="addStage"
          >
            <Icon icon="plus" class="size-3.5" />
            {{ __('Add stage') }}
          </button>
        </div>

        <aside class="hidden w-[260px] shrink-0 flex-col gap-3 lg:flex">
          <section
            class="overflow-hidden rounded-crm-panel border border-crm-border bg-crm-card"
          >
            <div
              class="flex items-center gap-2.5 border-b border-crm-border px-[18px] py-3.5"
            >
              <h2
                class="text-[14px] font-semibold leading-[1.45] tracking-[-0.005em] text-crm-fg"
              >
                {{ __('How types group stages') }}
              </h2>
            </div>
            <div class="flex flex-col px-[18px] pb-4 pt-3">
              <div
                class="relative grid grid-cols-[20px_minmax(0,1fr)] gap-2.5 pb-3 before:absolute before:bottom-0 before:left-[9px] before:top-5 before:w-0.5 before:bg-crm-border"
              >
                <span
                  class="relative z-[1] inline-flex size-5 items-center justify-center rounded-crm-chip bg-crm-neutral-soft text-[11px] font-bold text-crm-muted-fg"
                >
                  1
                </span>
                <div>
                  <div class="text-[12.5px] font-semibold leading-5 text-crm-fg">
                    {{ __('Open · Ongoing · On Hold') }}
                  </div>
                  <p class="text-[11.5px] leading-[1.45] text-crm-muted-fg">
                    {{
                      __(
                        'Shown as columns on the board and steps on the stage path',
                      )
                    }}
                  </p>
                </div>
              </div>
              <div class="grid grid-cols-[20px_minmax(0,1fr)] gap-2.5 pb-3">
                <span
                  class="inline-flex size-5 items-center justify-center rounded-crm-chip bg-crm-neutral-soft text-[11px] font-bold text-crm-muted-fg"
                >
                  2
                </span>
                <div>
                  <div class="text-[12.5px] font-semibold leading-5 text-crm-fg">
                    {{ __('Won · Lost') }}
                  </div>
                  <p class="text-[11.5px] leading-[1.45] text-crm-muted-fg">
                    {{
                      __('Collapsed into the Closed lane; used for win rate')
                    }}
                  </p>
                </div>
              </div>
            </div>
          </section>

          <div
            v-if="moveNotice"
            class="note flex gap-2.5 rounded-crm-card border border-crm-border bg-crm-muted px-3 py-2.5 text-[12.5px] leading-[1.45] text-crm-muted-fg"
          >
            <Icon
              icon="triangle-alert"
              class="mt-0.5 size-3.5 shrink-0 text-crm-warning"
            />
            <div>
              <b class="font-semibold text-crm-fg">
                {{
                  __('Moving {0} above {1}', [
                    moveNotice.stage.label,
                    moveNotice.above.label,
                  ])
                }}
              </b>
              <br />
              <span>{{ moveDetail }}</span>
            </div>
          </div>

          <div
            class="note flex gap-2.5 rounded-crm-card border border-crm-border bg-crm-muted px-3 py-2.5 text-[12.5px] leading-[1.45] text-crm-muted-fg"
          >
            <Icon
              icon="shield"
              class="mt-0.5 size-3.5 shrink-0 text-crm-faint"
            />
            <span>
              {{
                __(
                  'Colours are limited to the Astra palette so stages stay readable in light and dark.',
                )
              }}
            </span>
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
  Ongoing: 'bg-crm-primary-soft text-crm-primary',
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
const editingKey = ref(null)
let keySeq = 0

const { dealStatuses, leadStatuses } = statusesStore()

const isDeal = computed(() => activeParent.value === PARENTS.deal)

const rowGridClass = computed(() =>
  isDeal.value
    ? 'grid-cols-[16px_22px_minmax(0,1fr)_130px_86px_56px_64px_16px]'
    : 'grid-cols-[16px_22px_minmax(0,1fr)_130px_56px_64px_16px]',
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
  // Figma 21 concept frame shows this notice with Negotiation selected.
  if (isDeal.value && selectedKey.value) {
    const stage = draft.value.find((row) => row._key === selectedKey.value)
    const proposal = draft.value.find(
      (row) => row.label === 'Proposal/Quotation',
    )
    if (
      stage?.label === 'Negotiation' &&
      proposal &&
      stage._key !== proposal._key
    ) {
      return { stage, above: proposal }
    }
  }
  return null
})

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
  return `${kept} ${__('Board columns and stage paths update for everyone after you save.')}`
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
    // Figma 21: Negotiation row selected (table order unchanged).
    const negotiation = draft.value.find((s) => s.label === 'Negotiation')
    if (negotiation && isDeal.value) selectedKey.value = negotiation._key
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
  if (!dirty.value || saving.value) return
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
  if (!dirty.value || saving.value) return
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
