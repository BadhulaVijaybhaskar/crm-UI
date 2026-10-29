<template>
  <div class="flex h-screen w-screen flex-col bg-crm-bg">
    <MobileSidebar />
    <MobileTopBar />
    <main class="relative flex min-h-0 flex-1 flex-col overflow-auto">
      <slot />
    </main>
    <button
      type="button"
      class="fixed bottom-[75px] right-[13px] z-10 inline-flex h-[43px] items-center gap-2 rounded-[14px] bg-crm-primary px-[13px] text-[13px] font-semibold text-crm-primary-fg shadow-[0_4px_12px_rgba(10,115,147,0.25)]"
      @click="createLead"
    >
      <LucidePlus class="size-4" aria-hidden="true" />
      {{ __('New') }}
    </button>
    <MobileBottomNav />
    <!-- Outside the drawer so Settings survives drawer close. -->
    <Settings />
    <GlobalModals />
  </div>
</template>
<script setup>
import { nextTick } from 'vue'
import { useRouter } from 'vue-router'
import LucidePlus from '~icons/lucide/plus'
import MobileSidebar from '@/components/Mobile/MobileSidebar.vue'
import MobileTopBar from '@/components/Mobile/MobileTopBar.vue'
import MobileBottomNav from '@/components/Mobile/MobileBottomNav.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
import Settings from '@/components/Settings/Settings.vue'
import { useBroadcast } from '@/composables/useBroadcast.js'
import { availabilityStore } from '@/stores/availability'

// listen for status changes from the start, not only once a picker opens
availabilityStore()

const router = useRouter()
const { send } = useBroadcast()

async function createLead() {
  await router.push({ name: 'Leads' })
  await nextTick()
  send('trigger_lead_create', true)
}
</script>
