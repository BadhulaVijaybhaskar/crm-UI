<template>
  <nav
    class="flex h-[60px] shrink-0 items-stretch border-t border-crm-border bg-crm-card"
    :aria-label="__('Primary')"
  >
    <template v-for="item in items" :key="item.key">
      <router-link
        v-if="item.to"
        :to="item.to"
        class="astra-mobile-tab"
        :class="isActive(item) ? 'font-semibold text-crm-primary' : 'font-medium text-crm-muted-fg'"
      >
        <component :is="item.icon" class="size-[18px]" />
        {{ item.label }}
      </router-link>
      <button
        v-else
        type="button"
        class="astra-mobile-tab"
        :class="isActive(item) ? 'font-semibold text-crm-primary' : 'font-medium text-crm-muted-fg'"
        @click="item.action && item.action()"
      >
        <component :is="item.icon" class="size-[18px]" />
        {{ item.label }}
      </button>
    </template>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import LucideMenu from '~icons/lucide/menu'
import {
  FigmaDealsIcon,
  FigmaHomeIcon,
  FigmaLeadsIcon,
  FigmaWorkQueueIcon,
} from '@/components/Icons/FigmaNavIcons'
import { mobileSidebarOpened as sidebarOpened } from '@/composables/settings'

const route = useRoute()

const items = computed(() => [
  { key: 'home', label: __('Home'), icon: FigmaHomeIcon, to: { name: 'Dashboard' }, routes: ['Dashboard'] },
  { key: 'queue', label: __('Queue'), icon: FigmaWorkQueueIcon, to: { name: 'Work Queue' }, routes: ['Work Queue'] },
  { key: 'deals', label: __('Deals'), icon: FigmaDealsIcon, to: { name: 'Deals' }, routes: ['Deals', 'Deal'] },
  { key: 'leads', label: __('Leads'), icon: FigmaLeadsIcon, to: { name: 'Leads' }, routes: ['Leads', 'Lead'] },
  {
    key: 'more',
    label: __('More'),
    icon: LucideMenu,
    action: () => (sidebarOpened.value = !sidebarOpened.value),
    routes: [],
  },
])

function isActive(item) {
  return item.routes.includes(route.name)
}
</script>

<style scoped>
.astra-mobile-tab {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding-bottom: 1px;
  padding: 0;
  border: 0;
  background: transparent;
  font-family: var(--font-sans);
  font-size: 11px;
  line-height: 1.45;
  text-decoration: none;
}
</style>
