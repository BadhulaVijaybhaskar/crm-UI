import { globalStore } from '@/stores/global'
import { createResource } from 'frappe-ui'
import { ref } from 'vue'

// White-label: do not hardcode upstream cloud hosts or "Login to Cloud?" copy.
const baseEndpoint = ref('')
const siteName = ref('')

export const currentSiteInfo = createResource({
  url: 'frappe.integrations.frappe_providers.frappecloud_billing.current_site_info',
  cache: 'currentSiteInfo',
  onSuccess: (data) => {
    baseEndpoint.value = data?.base_url || ''
    siteName.value = data?.site_name || ''
  },
})

export const confirmLoginToFrappeCloud = () => {
  // No-op for Astra CRM white-label builds — cloud billing UI is not offered.
  const { $dialog } = globalStore()
  if (!$dialog) return
  $dialog({
    title: __('Not available'),
    message: __('Cloud billing is not available in this deployment.'),
    actions: [
      {
        label: __('OK'),
        variant: 'solid',
        onClick({ close }) {
          close()
        },
      },
    ],
  })
}

const loginToFrappeCloud = () => {
  if (!baseEndpoint.value || !siteName.value) return
  window.open(
    `${baseEndpoint.value}/dashboard/sites/${siteName.value}`,
    '_blank',
  )
}

// Keep export for any residual imports; unused in white-label UI.
export { loginToFrappeCloud }
