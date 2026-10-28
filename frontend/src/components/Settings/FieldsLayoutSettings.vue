<template>
  <div class="flex h-full min-h-0 flex-col bg-crm-bg text-crm-fg">
    <AstraPageHeader
      :title="__('Fields layout')"
      :description="__('Choose which fields appear and in what order.')"
    >
      <template #actions>
        <ExampleDataTag />
        <AstraButton
          :label="__('Discard')"
          :disabled="!dirty || saving"
          @click="reload"
        />
        <AstraButton
          variant="primary"
          :label="__('Save layout')"
          :loading="saving"
          :disabled="!dirty"
          @click="save"
        />
      </template>
    </AstraPageHeader>

    <div class="flex flex-wrap items-center gap-2 px-crm-page-x pb-4">
      <div class="flex flex-wrap gap-1" role="group" :aria-label="__('Record')">
        <button
          v-for="entity in entities"
          :key="entity.doctype"
          type="button"
          class="inline-flex h-8 items-center rounded-full px-3 text-crm-label font-medium"
          :class="
            doctype === entity.doctype
              ? 'bg-crm-card font-semibold text-crm-fg shadow-[inset_0_0_0_1px_var(--crm-border-strong)]'
              : 'bg-crm-muted text-crm-muted-fg'
          "
          :aria-pressed="doctype === entity.doctype"
          @click="switchDoctype(entity.doctype)"
        >
          {{ entity.label }}
        </button>
      </div>
      <div
        class="flex flex-wrap gap-1 sm:ml-2"
        role="group"
        :aria-label="__('Layout')"
      >
        <button
          v-for="lt in layoutTypes"
          :key="lt.value"
          type="button"
          class="inline-flex h-8 items-center rounded-crm-control-sm px-3 text-crm-label font-medium"
          :class="
            layoutType === lt.value
              ? 'bg-crm-card font-semibold text-crm-fg shadow-[inset_0_0_0_1px_var(--crm-border-strong)]'
              : 'bg-crm-muted text-crm-muted-fg'
          "
          :aria-pressed="layoutType === lt.value"
          @click="switchType(lt.value)"
        >
          {{ lt.label }}
        </button>
      </div>
    </div>

    <div class="flex min-h-0 flex-1 gap-4 overflow-hidden px-crm-page-x pb-6">
      <div class="min-h-0 min-w-0 flex-1 overflow-y-auto">
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
        class="hidden w-[260px] shrink-0 flex-col gap-3 overflow-y-auto lg:flex"
      >
        <button
          type="button"
          class="inline-flex items-center gap-1.5 self-end text-crm-label font-medium text-crm-muted-fg"
          @click="preview = !preview"
        >
          <Icon :icon="preview ? 'pencil' : 'eye'" class="size-3.5" />
          {{ preview ? __('Edit') : __('Preview') }}
        </button>
        <div
          v-if="selectedField && !preview"
          class="rounded-crm-panel border border-crm-border bg-crm-card p-4"
        >
          <div class="flex items-start justify-between gap-2">
            <h2 class="text-crm-panel font-semibold text-crm-fg">
              {{ selectedField.label || selectedField.fieldname }}
            </h2>
            <span
              class="shrink-0 rounded-crm-chip bg-crm-neutral-soft px-1.5 py-0.5 text-crm-micro font-medium text-crm-muted-fg"
            >
              {{ selectedField.fieldtype }}
            </span>
          </div>
          <div class="mt-4 text-xs font-semibold text-crm-fg">
            {{ __('Label') }}
          </div>
          <div
            class="mt-1 flex h-8 items-center rounded-crm-control-sm px-2.5 text-crm-label text-crm-fg shadow-[inset_0_0_0_1px_var(--crm-primary)]"
            role="textbox"
            aria-readonly="true"
          >
            {{ selectedField.label || selectedField.fieldname }}
          </div>
          <p class="mt-3 text-crm-meta text-crm-muted-fg">
            {{
              selectedField.reqd
                ? __('Mandatory on this record.')
                : __('Optional on this record.')
            }}
          </p>
          <button
            type="button"
            class="mt-3 text-crm-label font-semibold text-crm-danger"
            @click="editorRef?.removeSelected?.()"
          >
            {{ __('Remove field') }}
          </button>
        </div>
        <div
          class="flex gap-2 rounded-crm-panel border border-crm-border bg-crm-card p-3.5"
        >
          <Icon icon="info" class="mt-0.5 size-4 shrink-0 text-crm-faint" />
          <p class="text-crm-meta text-crm-muted-fg">{{ saveNote }}</p>
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

const editorKey = computed(() => `${doctype.value}:${layoutType.value}`)

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
  return __('Changes apply to the new {0} form for everyone after you save.', [
    entity,
  ])
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
