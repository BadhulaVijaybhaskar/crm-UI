<template>
  <div>
    <Checkbox
      :model-value="enabled"
      :disabled="saving"
      :label="__('Share usage data')"
      @update:model-value="savePreference"
    />
    <ErrorMessage class="mt-1" :message="error" />
  </div>
</template>

<script setup>
import { Checkbox, ErrorMessage, call } from 'frappe-ui'
import { ref } from 'vue'

// Telemetry is disabled product-wide (no pulse.m.frappe.cloud).
const enabled = ref(false)
const saving = ref(false)
const error = ref('')

async function persistPreference(share) {
  await call('frappe.client.set_value', {
    doctype: 'System Settings',
    name: 'System Settings',
    fieldname: 'enable_telemetry',
    value: 0,
  })
  enabled.value = false
}

async function savePreference(share) {
  if (saving.value) return false
  saving.value = true
  error.value = ''
  try {
    await persistPreference(share)
    enabled.value = false
    return true
  } catch (err) {
    error.value = __('Could not save your preference. Please try again.')
    console.error('Failed to save telemetry preference', err)
    return false
  } finally {
    saving.value = false
  }
}

defineExpose({ confirm: () => savePreference(enabled.value) })
</script>
