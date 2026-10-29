<template>
  <button
    type="button"
    class="inline-flex size-[30px] items-center justify-center rounded-crm-control-sm text-crm-nav-fg shadow-[inset_0_0_0_1px_var(--crm-nav-border)] hover:text-white"
    :aria-label="isDark ? __('Switch to light theme') : __('Switch to dark theme')"
    @click="toggle"
  >
    <FigmaMoonIcon v-if="!isDark" class="size-3.5" />
    <span v-else class="lucide-sun size-3.5" aria-hidden="true" />
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useColorScheme } from 'frappe-ui'
import { FigmaMoonIcon } from '@/components/Icons/FigmaNavIcons'

const { resolvedColorScheme, toggleColorScheme } = useColorScheme()

const isDark = computed(() => resolvedColorScheme.value === 'dark')

function toggle() {
  toggleColorScheme()
}
</script>
