<template>
  <button
    type="button"
    class="inline-flex size-[30px] shrink-0 items-center justify-center rounded-crm-control-sm border border-[color:var(--crm-nav-border)] text-[color:var(--crm-nav-fg)] hover:text-white"
    :aria-label="isDark ? __('Switch to light theme') : __('Switch to dark theme')"
    @click="toggle"
  >
    <!-- p-*-light.html: moon · p-*-dark.html: sun -->
    <FigmaSunIcon v-if="isDark" class="size-3.5" />
    <FigmaMoonIcon v-else class="size-3.5" />
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useColorScheme } from 'frappe-ui'
import { FigmaMoonIcon, FigmaSunIcon } from '@/components/Icons/FigmaNavIcons'

const { resolvedColorScheme, toggleColorScheme } = useColorScheme()

const isDark = computed(() => resolvedColorScheme.value === 'dark')

function toggle() {
  toggleColorScheme()
}
</script>
