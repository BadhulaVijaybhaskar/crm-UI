import { expect, it, vi } from 'vitest'
import { createApp, h, nextTick } from 'vue'

const mocks = vi.hoisted(() => ({
  call: vi.fn(),
}))
vi.mock('frappe-ui', () => ({
  call: mocks.call,
  Checkbox: {
    props: ['modelValue', 'disabled', 'label'],
    emits: ['update:modelValue'],
    setup:
      (props, { emit }) =>
      () =>
        h('label', [
          h('input', {
            type: 'checkbox',
            checked: props.modelValue,
            disabled: props.disabled,
            onChange: (event) =>
              emit('update:modelValue', event.target.checked),
          }),
          props.label,
        ]),
  },
  ErrorMessage: {
    props: ['message'],
    setup: (props) => () => h('p', props.message),
  },
}))
import SetupTelemetryConsent from '@/components/Setup/SetupTelemetryConsent.vue'

function mountPreference() {
  mocks.call.mockReset().mockResolvedValue()
  const root = document.createElement('div')
  const app = createApp(SetupTelemetryConsent)
  app.config.globalProperties.__ = (text) => text
  app.mount(root)
  return { root, app, checkbox: root.querySelector('input') }
}

async function settle() {
  await Promise.resolve()
  await Promise.resolve()
  await Promise.resolve()
  await nextTick()
}

it('defaults usage-data sharing off (telemetry disabled product-wide)', () => {
  const { root, app, checkbox } = mountPreference()
  try {
    expect(checkbox.checked).toBe(false)
    expect(root.textContent).toContain('Share usage data')
    expect(mocks.call).not.toHaveBeenCalled()
  } finally {
    app.unmount()
  }
})

it('always persists enable_telemetry=0 when toggled', async () => {
  const { app, checkbox } = mountPreference()
  try {
    checkbox.dispatchEvent(new Event('change'))
    // Force emit path used by the stub
    checkbox.checked = true
    checkbox.dispatchEvent(new Event('change'))
    await settle()
    expect(mocks.call).toHaveBeenCalledWith('frappe.client.set_value', {
      doctype: 'System Settings',
      name: 'System Settings',
      fieldname: 'enable_telemetry',
      value: 0,
    })
  } finally {
    app.unmount()
  }
})

it('shows an error when the preference save fails', async () => {
  const { root, app, checkbox } = mountPreference()
  const log = vi.spyOn(console, 'error').mockImplementation(() => {})
  try {
    mocks.call.mockRejectedValueOnce(new Error('Unable to save'))
    checkbox.checked = true
    checkbox.dispatchEvent(new Event('change'))
    await settle()
    expect(root.textContent).toContain('Could not save your preference')
  } finally {
    app.unmount()
    log.mockRestore()
  }
})
