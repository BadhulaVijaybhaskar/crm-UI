<template>
  <div class="flex w-full min-w-0 items-center gap-1">
    <button
      type="button"
      class="inline-flex size-[34px] shrink-0 items-center justify-center rounded-crm-control text-crm-muted-fg hover:bg-crm-muted hover:text-crm-fg"
      :aria-label="__('Open navigation')"
      @click="sidebarOpened = !sidebarOpened"
    >
      <Icon icon="lucide-menu" class="size-4" aria-hidden="true" />
    </button>
    <div id="app-header" class="min-w-0 flex-1" />
    <CallUI class="shrink-0" />
  </div>
</template>

<script setup>
import CallUI from '@/components/Telephony/CallUI.vue'
import Icon from '@/components/Icon.vue'
import { mobileSidebarOpened as sidebarOpened } from '@/composables/settings'
</script>
