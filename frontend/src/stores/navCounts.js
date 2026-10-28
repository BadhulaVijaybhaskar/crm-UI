import { createResource } from 'frappe-ui'
import { computed } from 'vue'

/**
 * One cached request for sidebar counts (my open leads/deals/tasks, work queue).
 * Missing keys mean "don't show a badge" — never invent numbers.
 */
export const navCounts = createResource({
  url: 'crm.api.nav.get_nav_counts',
  auto: true,
  cache: 'crm-nav-counts',
})

export const navCountMap = computed(() => navCounts.data || {})

export function useNavCounts() {
  return {
    navCounts,
    navCountMap,
    reload: () => navCounts.reload(),
  }
}
