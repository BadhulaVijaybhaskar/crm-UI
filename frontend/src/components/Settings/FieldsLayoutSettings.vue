<template>
  <div class="flex h-full min-h-0 flex-col bg-crm-bg text-crm-fg">
    <AstraPageHeader
      :title="__('Fields layout')"
      :description="__('Choose which fields appear and in what order')"
    >
      <template #actions>
        <ExampleDataTag />
        <AstraButton
          size="sm"
          :label="__('Discard')"
          :disabled="saving"
          @click="reload"
        />
        <AstraButton
          size="sm"
          variant="primary"
          :label="__('Save layout')"
          :loading="saving"
          :disabled="saving"
          @click="save"
        />
      </template>
    </AstraPageHeader>

    <div class="flex flex-wrap items-center gap-2 px-crm-page-x pb-2.5 pt-0">
      <div
        class="inline-flex gap-0.5 rounded-crm-card border border-crm-border bg-crm-muted p-[3px]"
        role="group"
        :aria-label="__('Record')"
      >
        <button
          v-for="entity in entities"
          :key="entity.doctype"
          type="button"
          class="inline-flex h-[26px] items-center rounded-crm-chip px-2.5 text-crm-label font-medium"
          :class="
            doctype === entity.doctype
              ? 'bg-crm-card font-semibold text-crm-fg shadow-[0_0_0_1px_var(--crm-border)]'
              : 'text-crm-muted-fg'
          "
          :aria-pressed="doctype === entity.doctype"
          @click="switchDoctype(entity.doctype)"
        >
          {{ entity.label }}
        </button>
      </div>
      <span class="hidden h-6 w-px bg-crm-border sm:block" aria-hidden="true" />
      <div
        class="inline-flex gap-0.5 rounded-crm-card border border-crm-border bg-crm-muted p-[3px]"
        role="group"
        :aria-label="__('Layout')"
      >
        <button
          v-for="lt in layoutTypes"
          :key="lt.value"
          type="button"
          class="inline-flex h-[26px] items-center rounded-crm-chip px-2.5 text-crm-label font-medium"
          :class="
            layoutType === lt.value
              ? 'bg-crm-card font-semibold text-crm-fg shadow-[0_0_0_1px_var(--crm-border)]'
              : 'text-crm-muted-fg'
          "
          :aria-pressed="layoutType === lt.value"
          @click="switchType(lt.value)"
        >
          {{ lt.label }}
        </button>
      </div>
      <span class="flex-1" />
      <button
        type="button"
        class="inline-flex h-7 items-center gap-[7px] rounded-[7px] px-2.5 text-[12.5px] font-medium text-crm-muted-fg hover:bg-crm-muted"
        @click="preview = !preview"
      >
        <Icon :icon="preview ? 'pencil' : 'eye'" class="size-3.5" />
        {{ preview ? __('Edit') : __('Preview') }}
      </button>
    </div>

    <div class="flex items-stretch gap-4 px-crm-page-x pb-6">
      <div class="min-w-0 flex-1">
        <div
          v-if="tabs.loading"
          class="py-16 text-center text-crm-body text-crm-muted-fg"
        >
          {{ __('Loading…') }}
        </div>
        <template v-else-if="tabs.data">
          <SidePanelLayoutEditor
            v-if="layoutType === 'Side Panel' && !preview && tabs.data?.[0]"
            :key="editorKey"
            ref="editorRef"
            v-model="tabs.data[0].sections"
            v-model:selected="selectedField"
            appearance="settings"
            :doctype="doctype"
          />
          <FieldLayoutEditor
            v-else-if="!preview"
            :key="editorKey"
            ref="editorRef"
            v-model="tabs.data"
            v-model:selected="selectedField"
            appearance="settings"
            :doctype="doctype"
          />
          <div
            v-else
            class="rounded-crm-panel border border-crm-border bg-crm-card p-4"
          >
            <FieldLayout :tabs="previewTabs" :data="{}" :preview="true" />
          </div>
        </template>
      </div>

      <aside
        v-if="selectedField && !preview"
        class="panel hidden w-[300px] shrink-0 overflow-hidden rounded-crm-panel border border-crm-border bg-crm-card lg:block"
      >
        <div
          class="flex items-center gap-2.5 border-b border-crm-border px-[18px] py-3.5"
        >
          <h2
            class="text-[14px] font-semibold leading-[1.45] tracking-[-0.005em] text-crm-fg"
          >
            {{ selectedField.label || selectedField.fieldname }}
          </h2>
          <span class="flex-1" />
          <span
            class="inline-flex h-[22px] shrink-0 items-center rounded-crm-chip bg-crm-neutral-soft px-2 text-[11.5px] font-semibold text-crm-muted-fg"
          >
            {{ selectedField.fieldtype }}
          </span>
        </div>
        <div class="flex flex-col gap-3 px-4 py-3.5">
          <div class="flex flex-col gap-[5px]">
            <label class="text-[12px] font-semibold leading-[1.45] text-crm-fg">
              {{ __('Label') }}
            </label>
            <div
              class="flex h-8 items-center rounded-[7px] border border-crm-primary bg-crm-card px-2.5 text-[12.5px] text-crm-fg shadow-[0_0_0_3px_var(--crm-primary-soft)]"
              role="textbox"
              aria-readonly="true"
            >
              {{ selectedField.label || selectedField.fieldname }}
            </div>
          </div>
          <label class="flex items-center gap-2.5 text-[12.5px] text-crm-fg">
            <button
              type="button"
              role="switch"
              class="relative inline-block h-[18px] w-[30px] shrink-0 rounded-full"
              :class="
                showInQuickEntry ? 'bg-crm-primary' : 'bg-crm-border-strong'
              "
              :aria-checked="showInQuickEntry"
              @click="showInQuickEntry = !showInQuickEntry"
            >
              <span
                class="absolute top-0.5 size-3.5 rounded-full bg-white transition-[left]"
                :class="showInQuickEntry ? 'left-[14px]' : 'left-0.5'"
              />
            </button>
            {{ __('Show in quick entry') }}
          </label>
          <label class="flex items-center gap-2.5 text-[12.5px] text-crm-fg">
            <button
              type="button"
              role="switch"
              class="relative inline-block h-[18px] w-[30px] shrink-0 rounded-full"
              :class="isMandatory ? 'bg-crm-primary' : 'bg-crm-border-strong'"
              :aria-checked="isMandatory"
              @click="toggleMandatory"
            >
              <span
                class="absolute top-0.5 size-3.5 rounded-full bg-white transition-[left]"
                :class="isMandatory ? 'left-[14px]' : 'left-0.5'"
              />
            </button>
            {{ __('Mandatory') }}
          </label>
          <label class="flex items-center gap-2.5 text-[12.5px] text-crm-fg">
            <button
              type="button"
              role="switch"
              class="relative inline-block h-[18px] w-[30px] shrink-0 rounded-full"
              :class="
                showInSidePanel ? 'bg-crm-primary' : 'bg-crm-border-strong'
              "
              :aria-checked="showInSidePanel"
              @click="showInSidePanel = !showInSidePanel"
            >
              <span
                class="absolute top-0.5 size-3.5 rounded-full bg-white transition-[left]"
                :class="showInSidePanel ? 'left-[14px]' : 'left-0.5'"
              />
            </button>
            {{ __('Show in side panel') }}
          </label>
          <div
            class="note flex gap-2.5 rounded-crm-card border border-crm-border bg-crm-muted px-3 py-2.5 text-[12.5px] leading-[1.45] text-crm-muted-fg"
          >
            <Icon icon="eye" class="mt-0.5 size-3.5 shrink-0 text-crm-faint" />
            <span>{{ saveNote }}</span>
          </div>
        </div>
      </aside>
      <aside
        v-else
        class="hidden w-[300px] shrink-0 flex-col gap-3 self-start lg:flex"
      >
        <div
          class="flex gap-2.5 rounded-crm-card border border-crm-border bg-crm-muted px-3 py-2.5 text-[12.5px] leading-[1.45] text-crm-muted-fg"
        >
          <Icon icon="eye" class="mt-0.5 size-3.5 shrink-0 text-crm-faint" />
          <p>{{ saveNote }}</p>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import ExampleDataTag from '@/components/astra/ExampleDataTag.vue'
import AstraButton from '@/components/astra/AstraButton.vue'
import AstraPageHeader from '@/components/astra/AstraPageHeader.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import FieldLayoutEditor from '@/components/FieldLayoutEditor.vue'
import Icon from '@/components/Icon.vue'
import SidePanelLayoutEditor from '@/components/SidePanelLayoutEditor.vue'
import { usersStore } from '@/stores/users'
import { useDebounceFn } from '@vueuse/core'
import { call, createResource, toast } from 'frappe-ui'
import { computed, onMounted, ref, watch } from 'vue'

const { isAdmin } = usersStore()

const entities = [
  { label: __('Lead'), doctype: 'CRM Lead' },
  { label: __('Deal'), doctype: 'CRM Deal' },
  { label: __('Contact'), doctype: 'Contact' },
  { label: __('Company'), doctype: 'CRM Organization' },
]

const layoutTypes = [
  { label: __('Quick entry'), value: 'Quick Entry' },
  { label: __('Side panel'), value: 'Side Panel' },
  { label: __('Data fields'), value: 'Data Fields' },
]

const doctype = ref('CRM Deal')
const layoutType = ref('Quick Entry')
const preview = ref(false)
const saving = ref(false)
const dirty = ref(false)
const selectedField = ref(null)
const editorRef = ref(null)
/** Figma 23 inspector toggles (layout flags; mandatory writes through to field). */
const showInQuickEntry = ref(true)
const showInSidePanel = ref(true)

const editorKey = computed(() => `${doctype.value}:${layoutType.value}`)
const isMandatory = computed(() => Boolean(selectedField.value?.reqd))

function toggleMandatory() {
  if (!selectedField.value) return
  selectedField.value.reqd = selectedField.value.reqd ? 0 : 1
}

watch(selectedField, (field) => {
  if (!field) return
  // Figma frame: Expected close → quick entry on, mandatory off, side panel on.
  showInQuickEntry.value = true
  showInSidePanel.value = true
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: 'SettingsFieldsLayout',
  auto: false,
  onSuccess(data) {
    tabs.originalData = JSON.parse(JSON.stringify(data))
    dirty.value = false
    selectedField.value = null
  },
})

const previewTabs = computed(() => tabs.data || [])

const saveNote = computed(() => {
  const entity =
    entities.find((row) => row.doctype === doctype.value)?.label || ''
  if (layoutType.value === 'Side Panel') {
    return __(
      'Changes apply to the {0} side panel for everyone after you save.',
      [entity],
    )
  }
  if (layoutType.value === 'Data Fields') {
    return __('Changes apply to {0} data fields for everyone after you save.', [
      entity,
    ])
  }
  return __(
    'Changes apply to the New {0} form for everyone after you save.',
    [String(entity).toLowerCase()],
  )
})

watch(
  () => tabs.data,
  () => {
    if (!tabs.data || !tabs.originalData) {
      dirty.value = false
      return
    }
    dirty.value =
      JSON.stringify(tabs.data) !== JSON.stringify(tabs.originalData)
  },
  { deep: true },
)

function params() {
  return { doctype: doctype.value, type: layoutType.value }
}

function reload() {
  if (saving.value) return
  tabs.params = params()
  tabs.reload()
}

function switchDoctype(dt) {
  if (dt === doctype.value) return
  if (dirty.value && !window.confirm(__('Discard unsaved changes?'))) return
  doctype.value = dt
  preview.value = false
  selectedField.value = null
  reload()
}

function switchType(type) {
  if (type === layoutType.value) return
  if (dirty.value && !window.confirm(__('Discard unsaved changes?'))) return
  layoutType.value = type
  preview.value = false
  selectedField.value = null
  reload()
}

function serializeFields(columns) {
  ;(columns || []).forEach((column) => {
    if (!column.fields) return
    column.fields = column.fields
      .map((field) => field.fieldname || field.name || field)
      .filter(Boolean)
  })
}

function serializeLayout(data) {
  const copy = JSON.parse(JSON.stringify(data))
  if (layoutType.value === 'Side Panel') {
    const sections = copy[0]?.sections || copy
    sections.forEach((section) => serializeFields(section.columns))
    return JSON.stringify(sections)
  }
  copy.forEach((tab) => {
    ;(tab.sections || []).forEach((section) => serializeFields(section.columns))
  })
  return JSON.stringify(copy)
}

async function save() {
  if (!dirty.value || saving.value) return
  if (!isAdmin()) {
    toast.error(__('Only Admin can save fields layout'))
    return
  }
  saving.value = true
  try {
    await call(
      'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.save_fields_layout',
      {
        doctype: doctype.value,
        type: layoutType.value,
        layout: serializeLayout(tabs.data),
      },
    )
    toast.success(__('Layout saved'))
    reload()
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Could not save layout'))
  } finally {
    saving.value = false
  }
}

onMounted(() => useDebounceFn(reload, 50)())
</script>
