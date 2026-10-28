<template>
  <button
    type="button"
    class="inline-flex size-[30px] items-center justify-center rounded-crm-control-sm text-crm-nav-faint shadow-[inset_0_0_0_1px_var(--crm-nav-border)] hover:text-white"
    :aria-label="isDark ? __('Switch to light theme') : __('Switch to dark theme')"
    @click="toggle"
  >
    <span
      :class="isDark ? 'lucide-sun' : 'lucide-moon'"
      class="size-4"
      aria-hidden="true"
    />
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useColorScheme } from 'frappe-ui'

const { resolvedColorScheme, toggleColorScheme } = useColorScheme()

const isDark = computed(() => resolvedColorScheme.value === 'dark')

function toggle() {
  toggleColorScheme()
}
</script>
