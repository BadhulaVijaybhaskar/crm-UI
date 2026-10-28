<template>
  <div class="astra-shell astra-shell--mobile">
    <MobileSidebar />
    <div class="astra-shell__main">
      <div class="astra-shell__topbar astra-shell__topbar--mobile">
        <MobileAppHeader />
      </div>
      <div class="astra-shell__content">
        <slot />
      </div>
    </div>
    <!-- Outside the drawer so Settings survives drawer close. -->
    <Settings />
    <GlobalModals />
  </div>
</template>
<script setup>
import MobileSidebar from '@/components/Mobile/MobileSidebar.vue'
import MobileAppHeader from '@/components/Mobile/MobileAppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
import Settings from '@/components/Settings/Settings.vue'
import { availabilityStore } from '@/stores/availability'

// listen for status changes from the start, not only once a picker opens
availabilityStore()
</script>
