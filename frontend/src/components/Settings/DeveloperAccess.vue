<template>
  <div class="flex flex-col gap-8 p-5">
    <section class="flex flex-col gap-3">
      <div>
        <h2 class="text-lg-semibold text-ink-gray-9">{{ __('API keys') }}</h2>
        <p class="mt-1 text-p-sm text-ink-gray-6">
          {{
            __(
              'Keys are hashed at rest. Authenticate with Authorization: Bearer <key>, Authorization: token <key>, or X-API-Key. The full key is shown only once.',
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
              'Signed HTTPS callbacks for lead, deal, and contact create/update and deal stage changes. Independent of Astra Connect.',
            )
          }}
        </p>
      </div>

      <div class="flex flex-col gap-3 rounded-md border border-outline-gray-2 p-3">
        <FormControl v-model="hookForm.title" type="text" :label="__('Title')" />
        <FormControl v-model="hookForm.endpoint_url" type="text" :label="__('Endpoint URL')" />
        <FormControl
          v-model="hookForm.secret"
          type="password"
          :label="__('Signing secret')"
        />
        <div>
          <p class="mb-2 text-p-sm font-medium text-ink-gray-8">{{ __('Events') }}</p>
          <div class="flex flex-col gap-1.5">
            <label
              v-for="ev in EVENT_OPTIONS"
              :key="ev"
              class="flex items-center gap-2 text-p-sm text-ink-gray-8"
            >
              <input v-model="hookForm.events" type="checkbox" :value="ev" class="rounded" />
              {{ ev }}
            </label>
          </div>
        </div>
        <label class="flex items-center gap-2 text-p-sm text-ink-gray-8">
          <input v-model="hookForm.enabled" type="checkbox" class="rounded" />
          {{ __('Enabled') }}
        </label>
        <div class="flex flex-wrap gap-2">
          <Button
            variant="solid"
            :label="hookForm.name ? __('Update webhook') : __('Create webhook')"
            :loading="savingHook"
            @click="saveHook"
          />
          <Button
            v-if="hookForm.name"
            variant="outline"
            :label="__('Cancel edit')"
            @click="resetHookForm"
          />
        </div>
      </div>

      <ul class="divide-y divide-outline-gray-1 rounded-md border border-outline-gray-2">
        <li
          v-for="w in webhooks.data || []"
          :key="w.name"
          class="flex items-start justify-between gap-3 px-3 py-2 text-p-sm"
        >
          <div>
            <div class="font-medium text-ink-gray-9">
              {{ w.title }}
              <span v-if="!w.enabled" class="text-ink-gray-5"> ({{ __('off') }})</span>
            </div>
            <div class="text-ink-gray-5">{{ w.endpoint_url }}</div>
            <div class="text-ink-gray-5">{{ w.events }}</div>
          </div>
          <div class="flex shrink-0 gap-1">
            <Button variant="outline" :label="__('Edit')" @click="editHook(w)" />
            <Button variant="outline" :label="__('Delete')" @click="removeHook(w)" />
          </div>
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
import { reactive, ref } from 'vue'

const EVENT_OPTIONS = [
  'lead.created',
  'lead.updated',
  'deal.created',
  'deal.updated',
  'deal.stage_changed',
  'contact.created',
  'contact.updated',
]

const newLabel = ref('')
const plaintextKey = ref('')
const creating = ref(false)
const savingHook = ref(false)

const emptyHook = () => ({
  name: '',
  title: '',
  endpoint_url: '',
  secret: '',
  events: [],
  enabled: true,
})

const hookForm = reactive(emptyHook())

const keys = createResource({
  url: 'crm.fcrm.doctype.crm_api_key.crm_api_key.list_api_keys',
  auto: true,
})

const webhooks = createResource({
  url: 'crm.fcrm.doctype.crm_outbound_webhook.crm_outbound_webhook.list_outbound_webhooks',
  auto: true,
})

function resetHookForm() {
  Object.assign(hookForm, emptyHook())
}

function editHook(w) {
  hookForm.name = w.name
  hookForm.title = w.title
  hookForm.endpoint_url = w.endpoint_url
  hookForm.secret = ''
  hookForm.events = (w.events || '')
    .split(',')
    .map((e) => e.trim())
    .filter(Boolean)
  hookForm.enabled = !!w.enabled
}

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

async function saveHook() {
  if (!hookForm.title.trim() || !hookForm.endpoint_url.trim()) {
    toast.error(__('Title and endpoint URL are required'))
    return
  }
  if (!hookForm.events.length) {
    toast.error(__('Select at least one event'))
    return
  }
  savingHook.value = true
  try {
    await call(
      'crm.fcrm.doctype.crm_outbound_webhook.crm_outbound_webhook.save_outbound_webhook',
      {
        name: hookForm.name || undefined,
        title: hookForm.title.trim(),
        endpoint_url: hookForm.endpoint_url.trim(),
        secret: hookForm.secret || undefined,
        events: hookForm.events,
        enabled: hookForm.enabled ? 1 : 0,
      },
    )
    toast.success(hookForm.name ? __('Webhook updated') : __('Webhook created'))
    resetHookForm()
    webhooks.reload()
  } catch (e) {
    toast.error(e.message || __('Could not save webhook'))
  } finally {
    savingHook.value = false
  }
}

async function removeHook(w) {
  try {
    await call(
      'crm.fcrm.doctype.crm_outbound_webhook.crm_outbound_webhook.delete_outbound_webhook',
      { name: w.name },
    )
    if (hookForm.name === w.name) resetHookForm()
    webhooks.reload()
    toast.success(__('Webhook deleted'))
  } catch (e) {
    toast.error(e.message || __('Could not delete webhook'))
  }
}
</script>
