import { call } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/**
 * View tabs + list/board switch for Astra records list pages.
 * Counts come from the live list total for the active view, and
 * frappe.client.get_count for other saved views' filters.
 */
export function useRecordsViews({
  doctype,
  list,
  viewControls,
  defaultFilters = () => ({}),
  allLabel,
}) {
  const route = useRoute()
  const router = useRouter()
  const viewCounts = ref({})

  const viewType = computed(() => route.params.viewType || 'list')
  const activeView = computed(() => String(route.query.view || 'list'))

  const savedViews = computed(() => {
    const views = list.value?.data?.views || []
    return views.filter((v) => v && v.name)
  })

  const viewTabs = computed(() => {
    const tabs = [
      {
        value: 'list',
        label: allLabel || __('All'),
        view: null,
        type: 'list',
        // Prefer the unfiltered get_count so chips/filters don't rewrite the All tab.
        count:
          viewCounts.value.__all ??
          (activeView.value === 'list'
            ? list.value?.data?.total_count
            : undefined),
      },
    ]
    for (const view of savedViews.value) {
      tabs.push({
        value: String(view.name),
        label: view.label || view.name,
        view,
        type: view.type || 'list',
        count:
          activeView.value === String(view.name)
            ? list.value?.data?.total_count
            : viewCounts.value[view.name],
      })
    }
    return tabs
  })

  async function refreshViewCounts() {
    const next = { ...viewCounts.value }
    try {
      next.__all = await call('frappe.client.get_count', {
        doctype,
        filters: defaultFilters(),
      })
    } catch {
      /* keep prior */
    }
    await Promise.all(
      savedViews.value.map(async (view) => {
        let filters = view.filters || {}
        if (typeof filters === 'string') {
          try {
            filters = JSON.parse(filters)
          } catch {
            filters = {}
          }
        }
        try {
          next[view.name] = await call('frappe.client.get_count', {
            doctype,
            filters: { ...defaultFilters(), ...filters },
          })
        } catch {
          /* keep prior */
        }
      }),
    )
    viewCounts.value = next
  }

  watch(
    () => [list.value?.data?.views, list.value?.data?.total_count],
    () => {
      refreshViewCounts()
    },
    { immediate: true },
  )

  function selectView(tab) {
    if (!tab) return
    if (tab.value === 'list' || !tab.view) {
      router.push({ name: route.name, params: { viewType: 'list' }, query: {} })
      return
    }
    router.push({
      name: route.name,
      params: { viewType: tab.type || 'list' },
      query: { view: tab.view.name },
    })
  }

  function setViewType(type) {
    const query = { ...route.query }
    router.push({
      name: route.name,
      params: { viewType: type },
      query,
    })
  }

  function saveView() {
    const options = viewControls.value?.viewsDropdownOptions || []
    for (const group of options) {
      for (const opt of group.options || []) {
        if (
          typeof opt.onClick === 'function' &&
          (opt.label === __('Create View') ||
            opt.label === 'Create View' ||
            opt.label === __('Save view'))
        ) {
          opt.onClick()
          return
        }
      }
    }
  }

  function filterChipsFromList() {
    const filters = { ...(list.value?.params?.filters || {}) }
    const defaults = defaultFilters()
    const chips = []
    for (const [key, value] of Object.entries(filters)) {
      if (key in defaults && JSON.stringify(defaults[key]) === JSON.stringify(value)) {
        continue
      }
      if (value == null || value === '') continue
      const display = Array.isArray(value)
        ? value.filter((v) => v !== 'in' && v !== 'like' && v !== '=').join(', ')
        : String(value)
      chips.push({
        id: key,
        key: __(key.replace(/_/g, ' ')),
        value: display,
        fieldname: key,
      })
    }
    return chips
  }

  function removeFilterChip(chip) {
    if (!list.value?.params?.filters || !chip?.fieldname) return
    const next = { ...list.value.params.filters }
    delete next[chip.fieldname]
    list.value.params.filters = next
    list.value.reload?.()
  }

  return {
    viewType,
    activeView,
    viewTabs,
    selectView,
    setViewType,
    saveView,
    filterChipsFromList,
    removeFilterChip,
    refreshViewCounts,
  }
}
