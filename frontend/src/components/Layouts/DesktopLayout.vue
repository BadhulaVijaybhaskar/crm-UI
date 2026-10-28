<template>
  <div
    class="astra-shell"
    :data-sidebar-collapsed="isSidebarCollapsed ? 'true' : 'false'"
  >
    <div
      class="astra-shell__sidebar"
      :data-collapsed="isSidebarCollapsed ? 'true' : 'false'"
    >
      <AppSidebar />
    </div>
    <div class="astra-shell__main">
      <AppHeader />
      <div class="astra-shell__content">
        <slot />
      </div>
    </div>
    <GlobalModals />
  </div>
</template>

<script setup>
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
import { availabilityStore } from '@/stores/availability'
import { useStorage } from '@vueuse/core'

availabilityStore()

const isSidebarCollapsed = useStorage('isSidebarCollapsed', false)
</script>
