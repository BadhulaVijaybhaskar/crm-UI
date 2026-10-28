import { createDocumentResource } from 'frappe-ui'
import { reactive, ref } from 'vue'
import { ASTRA_FAVICON, ASTRA_LOGO } from '@/assets/brand'

const settings = ref({})
const brand = reactive({})

const _settings = createDocumentResource({
  doctype: 'FCRM Settings',
  name: 'FCRM Settings',
  onSuccess: (data) => {
    settings.value = data
    getSettings().setupBrand()
    return data
  },
})

export function getSettings() {
  function setupBrand() {
    brand.name = settings.value?.brand_name || 'Astra CRM'
    brand.logo = settings.value?.brand_logo || ASTRA_LOGO
    brand.favicon = settings.value?.favicon || ASTRA_FAVICON
  }

  return {
    _settings,
    settings,
    brand,
    setupBrand,
  }
}
