<template>
  <div class="flex flex-col gap-5 p-5">
    <div>
      <h2 class="text-lg-semibold text-ink-gray-9">{{ __('Astra Connect') }}</h2>
      <p class="mt-1 text-p-sm text-ink-gray-6">
        {{
          __(
            'Enable Connect to show AI Calling, Messages and AI Employees, and to exchange signed webhooks.',
          )
        }}
      </p>
    </div>

    <div v-if="settings.get.loading" class="text-p-sm text-ink-gray-5">
      {{ __('Loading…') }}
    </div>
    <template v-else-if="settings.doc">
      <FormControl
        type="checkbox"
        :label="__('Enabled')"
        :modelValue="!!settings.doc.enabled"
        @update:modelValue="(v) => (settings.doc.enabled = v ? 1 : 0)"
      />
      <FormControl
        v-model="settings.doc.connect_base_url"
        type="text"
        :label="__('Connect base URL')"
        :description="__('No trailing slash. Required when Enabled.')"
      />
      <Link
        class="form-control"
        :value="settings.doc.default_lead_owner"
        doctype="User"
        :label="__('Default lead owner')"
        @change="(v) => (settings.doc.default_lead_owner = v)"
      />
      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'The signing secret is set in site config as astra_connect_webhook_secret and is never shown in the UI.',
          )
        }}
      </p>
      <div class="flex gap-2">
        <Button
          variant="solid"
          :label="__('Save')"
          :loading="settings.save.loading"
          @click="save"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { createDocumentResource, FormControl, toast } from 'frappe-ui'

const settings = createDocumentResource({
  doctype: 'Astra Connect Settings',
  name: 'Astra Connect Settings',
  auto: true,
})

function save() {
  if (settings.doc.enabled && !String(settings.doc.connect_base_url || '').trim()) {
    toast.error(__('Connect base URL is required when Enabled'))
    return
  }
  settings.save.submit(null, {
    onSuccess: () => toast.success(__('Saved')),
  })
}
</script>
