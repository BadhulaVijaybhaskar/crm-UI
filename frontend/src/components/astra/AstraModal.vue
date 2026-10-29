<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[200] flex items-start justify-center px-4 pt-[10vh]"
      role="presentation"
    >
      <div
        class="absolute inset-0 bg-[color:var(--crm-overlay)]"
        aria-hidden="true"
        @click="onOverlay"
      />
      <div
        role="dialog"
        aria-modal="true"
        :aria-label="title || 'Dialog'"
        class="relative z-[1] w-full overflow-hidden rounded-crm-modal border border-crm-border bg-crm-card shadow-crm-modal"
        :class="sizeClass"
      >
        <header
          v-if="title || $slots.header || closable"
          class="flex items-center justify-between gap-3 px-[18px] py-3.5"
        >
          <slot name="header">
            <h2 class="m-0 text-crm-dialog font-semibold text-crm-fg">{{ title }}</h2>
          </slot>
          <AstraButton
            v-if="closable"
            variant="ghost"
            size="sm"
            icon-only
            aria-label="Close"
            @click="close"
          >
            <template #prefix>
              <span class="lucide-x size-4" aria-hidden="true" />
            </template>
          </AstraButton>
        </header>
        <div class="px-[18px] pb-4">
          <slot />
        </div>
        <footer
          v-if="$slots.footer"
          class="flex items-center justify-end gap-2 border-t border-crm-border px-[18px] py-3"
        >
          <slot name="footer" />
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import AstraButton from '@/components/astra/AstraButton.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  size: { type: String, default: 'md' },
  closable: { type: Boolean, default: true },
  closeOnOverlay: { type: Boolean, default: true },
})

const emit = defineEmits(['update:open', 'close'])

const sizeClass = computed(() => {
  if (props.size === 'sm') return 'max-w-md'
  if (props.size === 'lg') return 'max-w-2xl'
  return 'max-w-lg'
})

function close() {
  emit('update:open', false)
  emit('close')
}

function onOverlay() {
  if (props.closeOnOverlay) close()
}
</script>
