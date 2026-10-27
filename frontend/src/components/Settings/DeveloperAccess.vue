<template>
  <div class="flex flex-col gap-8 p-5">
    <section class="flex flex-col gap-3">
      <div>
        <h2 class="text-lg-semibold text-ink-gray-9">{{ __('API keys') }}</h2>
        <p class="mt-1 text-p-sm text-ink-gray-6">
          {{
            __(
              'Keys are hashed at rest. The full key is shown only once when you create it.',
            )
          }}
        </p>
      </div>
      <div class="flex flex-wrap items-end gap-2">
        <FormControl v-model="newLabel" type="text" :label="__('Label')" class="w-56" />
        <Button variant="solid" :label="__('Create key')" :loading="creating" @click="createKey" />
      </div>
      <div
        v-if="plaintextKey"
        class="rounded-md border border-outline-gray-2 bg-surface-gray-2 px-3 py-2 text-p-sm"
      >
        <p class="font-medium text-ink-gray-9">{{ __('Copy this key now') }}</p>
        <code class="mt-1 block break-all text-ink-gray-8">{{ plaintextKey }}</code>
      </div>
      <ul class="divide-y divide-outline-gray-1 rounded-md border border-outline-gray-2">
        <li
          v-for="k in keys.data || []"
          :key="k.name"
          class="flex items-center justify-between gap-3 px-3 py-2 text-p-sm"
        >
          <div>
            <div class="font-medium text-ink-gray-9">{{ k.label }}</div>
            <div class="text-ink-gray-5">
              {{ k.key_prefix }}… · {{ k.user }}
              <span v-if="k.disabled"> · {{ __('Disabled') }}</span>
            </div>
          </div>
          <Button
            variant="outline"
            :label="k.disabled ? __('Enable') : __('Disable')"
            @click="toggleKey(k)"
          />
        </li>
      </ul>
    </section>

    <section class="flex flex-col gap-3">
      <div>
        <h2 class="text-lg-semibold text-ink-gray-9">{{ __('Outbound webhooks') }}</h2>
        <p class="mt-1 text-p-sm text-ink-gray-6">
          {{
            __(
              'Signed HTTPS callbacks for CRM events. Create rows in CRM Outbound Webhook.',
            )
          }}
        </p>
      </div>
      <ul class="divide-y divide-outline-gray-1 rounded-md border border-outline-gray-2">
        <li
          v-for="w in webhooks.data || []"
          :key="w.name"
          class="px-3 py-2 text-p-sm"
        >
          <div class="font-medium text-ink-gray-9">
            {{ w.title }}
            <span v-if="!w.enabled" class="text-ink-gray-5"> ({{ __('off') }})</span>
          </div>
          <div class="text-ink-gray-5">{{ w.endpoint_url }}</div>
          <div class="text-ink-gray-5">{{ w.events }}</div>
        </li>
        <li v-if="!(webhooks.data || []).length" class="px-3 py-2 text-p-sm text-ink-gray-5">
          {{ __('No outbound webhooks yet.') }}
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup>
import { call, createResource, FormControl, toast } from 'frappe-ui'
import { ref } from 'vue'

const newLabel = ref('')
const plaintextKey = ref('')
const creating = ref(false)

const keys = createResource({
  url: 'crm.fcrm.doctype.crm_api_key.crm_api_key.list_api_keys',
  auto: true,
})

const webhooks = createResource({
  url: 'crm.fcrm.doctype.crm_outbound_webhook.crm_outbound_webhook.list_outbound_webhooks',
  auto: true,
})

async function createKey() {
  if (!newLabel.value.trim()) {
    toast.error(__('Label is required'))
    return
  }
  creating.value = true
  try {
    const res = await call('crm.fcrm.doctype.crm_api_key.crm_api_key.create_api_key', {
      label: newLabel.value.trim(),
    })
    plaintextKey.value = res.api_key
    newLabel.value = ''
    keys.reload()
    toast.success(__('API key created — copy it now'))
  } catch (e) {
    toast.error(e.message || __('Could not create key'))
  } finally {
    creating.value = false
  }
}

async function toggleKey(k) {
  await call('crm.fcrm.doctype.crm_api_key.crm_api_key.set_api_key_disabled', {
    name: k.name,
    disabled: k.disabled ? 0 : 1,
  })
  keys.reload()
}
</script>
