<template>
  <Dialog v-model:open="show" :options="{ title: __('CSV import') }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-p-sm text-ink-gray-7">
          {{
            __(
              'Import {0} from a CSV. Duplicates are matched by email or phone.',
              [__(doctypeLabel)],
            )
          }}
        </p>
        <div class="flex flex-wrap gap-2">
          <Button
            variant="outline"
            :label="__('Download template')"
            @click="downloadTemplate"
          />
        </div>
        <FormControl
          v-model="onDuplicate"
          type="select"
          :label="__('When a duplicate is found')"
          :options="duplicateOptions"
        />
        <div>
          <p class="mb-1 text-p-sm text-ink-gray-7">{{ __('CSV file') }}</p>
          <input
            type="file"
            accept=".csv,text/csv"
            class="block w-full text-p-sm text-ink-gray-8"
            @change="onFile"
          />
        </div>
        <ErrorMessage v-if="error" :message="error" />
        <div
          v-if="result"
          class="rounded-md border border-outline-gray-2 bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-8"
        >
          <p>
            {{ __('Status') }}: {{ result.status }}
            <template v-if="result.status === 'done'">
              — {{ __('Created') }} {{ result.created || 0 }},
              {{ __('Updated') }} {{ result.updated || 0 }},
              {{ __('Skipped') }} {{ result.skipped || 0 }},
              {{ __('Errors') }} {{ result.error_count || 0 }}
            </template>
          </p>
          <Button
            v-if="result.error_count"
            class="mt-2"
            variant="outline"
            :label="__('Download error report')"
            @click="downloadErrors"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        variant="solid"
        :label="__('Start import')"
        :loading="busy"
        :disabled="!fileUrl || busy"
        @click="start"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { call, Dialog, ErrorMessage, FormControl, toast } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { crmCsvTemplateUrl } from '@/utils/csvExport'

const props = defineProps({
  doctype: { type: String, required: true },
})
const show = defineModel({ type: Boolean })

const doctypeLabel = computed(() => {
  const map = {
    'CRM Lead': __('Leads'),
    Contact: __('Contacts'),
  }
  return map[props.doctype] || props.doctype
})

const onDuplicate = ref('skip')
const duplicateOptions = [
  { label: __('Skip existing'), value: 'skip' },
  { label: __('Update existing'), value: 'update' },
  { label: __('Create new anyway'), value: 'create' },
]

const fileUrl = ref('')
const error = ref('')
const busy = ref(false)
const result = ref(null)
const jobId = ref('')
let pollTimer = null

watch(show, (open) => {
  if (!open) {
    clearInterval(pollTimer)
    fileUrl.value = ''
    error.value = ''
    result.value = null
    jobId.value = ''
    busy.value = false
  }
})

function downloadTemplate() {
  window.location.href = crmCsvTemplateUrl(props.doctype)
}

async function onFile(event) {
  const file = event.target.files?.[0]
  if (!file) return
  error.value = ''
  try {
    const fd = new FormData()
    fd.append('file', file, file.name)
    fd.append('is_private', '1')
    const res = await fetch('/api/method/upload_file', {
      method: 'POST',
      body: fd,
      credentials: 'include',
      headers: {
        'X-Frappe-CSRF-Token': window.csrf_token || '',
      },
    })
    const data = await res.json()
    if (!res.ok || data.exc) {
      throw new Error(data._error_message || data.message || __('Upload failed'))
    }
    fileUrl.value = data.message?.file_url || data.message
  } catch (e) {
    error.value = e.message || __('Upload failed')
    fileUrl.value = ''
  }
}

async function start() {
  if (!fileUrl.value) return
  busy.value = true
  error.value = ''
  result.value = null
  try {
    const res = await call('crm.api.csv_import.start_csv_import', {
      doctype: props.doctype,
      file_url: fileUrl.value,
      on_duplicate: onDuplicate.value,
      dedupe_by: JSON.stringify(['email', 'phone']),
    })
    jobId.value = res.job_id
    result.value = { status: 'queued' }
    pollTimer = setInterval(poll, 1500)
    await poll()
  } catch (e) {
    error.value = e.messages?.join?.('\n') || e.message || __('Import failed')
    busy.value = false
  }
}

async function poll() {
  if (!jobId.value) return
  try {
    const res = await call('crm.api.csv_import.get_import_result', {
      job_id: jobId.value,
    })
    result.value = res
    if (res.status === 'done' || res.status === 'failed') {
      clearInterval(pollTimer)
      busy.value = false
      if (res.status === 'done') {
        toast.success(
          __('Import finished: {0} created, {1} updated, {2} skipped', [
            res.created || 0,
            res.updated || 0,
            res.skipped || 0,
          ]),
        )
      } else {
        error.value = res.error || __('Import failed')
      }
    }
  } catch (e) {
    clearInterval(pollTimer)
    busy.value = false
    error.value = e.message || __('Could not read import status')
  }
}

function downloadErrors() {
  if (!jobId.value) return
  window.location.href = `/api/method/crm.api.csv_import.download_import_errors?job_id=${encodeURIComponent(jobId.value)}`
}
</script>
