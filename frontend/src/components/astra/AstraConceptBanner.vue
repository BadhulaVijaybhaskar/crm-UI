<template>
  <div
    class="flex h-[30px] shrink-0 items-center gap-2.5 border-b border-dashed border-[color:var(--crm-border-strong,#d0d9e0)] bg-[color:var(--crm-muted,#f6f8fa)] px-crm-page-x text-[12px] text-[color:var(--crm-muted-fg,#5b6478)]"
    role="note"
  >
    <LucideTriangleAlert
      class="size-3.5 shrink-0 text-[color:var(--crm-fg,#0b1324)]"
      aria-hidden="true"
    />
    <span class="font-bold text-[color:var(--crm-fg,#0b1324)]">{{ label }}</span>
    <span class="min-w-0 flex-1 truncate">
      <slot>{{ text }}</slot>
    </span>
  </div>
</template>

<script setup>
import LucideTriangleAlert from '~icons/lucide/triangle-alert'

defineProps({
  label: { type: String, default: 'Concept' },
  text: { type: String, default: '' },
})
</script>
