<template>
  <div class="flex h-full min-h-0 flex-col text-ink-gray-8">
    <div class="flex items-start justify-between gap-4 px-6 pt-6 pb-3">
      <div class="flex min-w-0 flex-col gap-1">
        <h2 class="text-2xl-semibold leading-none">
          {{ __('Fields layout') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Choose which fields appear and in what order.') }}
        </p>
      </div>
      <div class="flex shrink-0 items-center gap-2">
        <Button
          :label="preview ? __('Hide preview') : __('Preview')"
          @click="preview = !preview"
        />
        <Button
          :label="__('Discard')"
          :disabled="!dirty || saving"
          @click="reload"
        />
        <Button
          variant="solid"
          :label="__('Save layout')"
          :loading="saving"
          :disabled="!dirty"
          @click="save"
        />
      </div>
    </div>

    <div class="flex flex-wrap items-center gap-2 px-6 pb-2">
      <button
        v-for="entity in entities"
        :key="entity.doctype"
        type="button"
        class="rounded-full px-3 py-1.5 text-sm font-medium transition-colors"
        :class="
          doctype === entity.doctype
            ? 'bg-[var(--crm-primary-soft,var(--surface-gray-3))] text-[var(--crm-primary,var(--ink-gray-9))]'
            : 'text-ink-gray-6 hover:bg-surface-gray-2'
        "
        @click="switchDoctype(entity.doctype)"
      >
        {{ entity.label }}
      </button>
    </div>

    <div class="flex flex-wrap items-center gap-2 px-6 pb-4">
      <button
        v-for="lt in layoutTypes"
        :key="lt.value"
        type="button"
        class="rounded-md px-3 py-1 text-sm transition-colors"
        :class="
          layoutType === lt.value
            ? 'bg-surface-gray-3 font-semibold text-ink-gray-9'
            : 'text-ink-gray-6 hover:bg-surface-gray-2'
        "
        @click="switchType(lt.value)"
      >
        {{ lt.label }}
      </button>
    </div>

    <div class="min-h-0 flex-1 overflow-y-auto px-6 pb-6">
      <div v-if="tabs.loading" class="py-12 text-center text-ink-gray-5">
        {{ __('Loading…') }}
      </div>
      <template v-else-if="tabs.data">
        <SidePanelLayoutEditor
          v-if="layoutType === 'Side Panel' && !preview && tabs.data?.[0]"
          v-model="tabs.data[0].sections"
          :doctype="doctype"
        />
        <FieldLayoutEditor
          v-else-if="!preview"
          v-model="tabs.data"
          :doctype="doctype"
        />
        <div
          v-else
          class="rounded-lg border border-outline-gray-2 bg-surface-white p-4"
        >
          <FieldLayout :tabs="previewTabs" :data="{}" :preview="true" />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import FieldLayoutEditor from '@/components/FieldLayoutEditor.vue'
import SidePanelLayoutEditor from '@/components/SidePanelLayoutEditor.vue'
import { usersStore } from '@/stores/users'
import { useDebounceFn } from '@vueuse/core'
import { Button, call, createResource, toast } from 'frappe-ui'
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

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: 'SettingsFieldsLayout',
  auto: false,
  onSuccess(data) {
    tabs.originalData = JSON.parse(JSON.stringify(data))
    dirty.value = false
  },
})

const previewTabs = computed(() => tabs.data || [])

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
  reload()
}

function switchType(type) {
  if (type === layoutType.value) return
  if (dirty.value && !window.confirm(__('Discard unsaved changes?'))) return
  layoutType.value = type
  preview.value = false
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
