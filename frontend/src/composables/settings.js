import { computed, ref } from 'vue'
import router from '@/router'

export const mobileSidebarOpened = ref(false)

export const isMobileView = computed(() => window.innerWidth < 768)

// Slug of the settings section in the URL. Empty when another page is open.
export const activeSettingsPage = computed(() => {
  const route = router.currentRoute.value
  if (route.name !== 'Settings') return ''
  const section = route.params.section
  if (Array.isArray(section)) return section[0] || ''
  return section || ''
})

export function openSettings(page) {
  return import('@/components/Settings/settingsSections').then(
    ({ slugFromLabel }) => {
      const slug = slugFromLabel(page)
      return router.push({
        name: 'Settings',
        params: slug ? { section: slug } : {},
      })
    },
  )
}
