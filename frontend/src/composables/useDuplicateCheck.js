import { call } from 'frappe-ui'
import { ref, watch } from 'vue'

/**
 * Polls crm.api.dedupe.find_duplicates while the user edits email / phone / website.
 * Returns matches the create dialog can show as a warning (create is still allowed).
 */
export function useDuplicateCheck(doctype, getValues, { debounceMs = 400 } = {}) {
  const matches = ref([])
  const loading = ref(false)
  let timer = null
  let seq = 0

  async function refresh() {
    const values = typeof getValues === 'function' ? getValues() : getValues
    const email = values?.email || values?.email_id || ''
    const phone = values?.mobile_no || values?.phone || ''
    const website = values?.website || ''
    if (!email && !phone && !website) {
      matches.value = []
      return
    }
    const my = ++seq
    loading.value = true
    try {
      const rows = await call('crm.api.dedupe.find_duplicates', {
        doctype,
        email: email || undefined,
        phone: phone || undefined,
        website: website || undefined,
        exclude: values?.name || undefined,
      })
      if (my === seq) matches.value = rows || []
    } catch {
      if (my === seq) matches.value = []
    } finally {
      if (my === seq) loading.value = false
    }
  }

  function schedule() {
    clearTimeout(timer)
    timer = setTimeout(refresh, debounceMs)
  }

  function bind(source) {
    watch(source, schedule, { deep: true })
  }

  return { matches, loading, refresh, schedule, bind }
}
