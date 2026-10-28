<template>
  <header
    class="flex flex-col gap-3.5 border-b border-crm-border bg-crm-card px-crm-page-x pb-3.5 pt-4"
  >
    <div class="flex items-start gap-3">
      <AstraAvatar
        :name="title"
        :src="avatarSrc"
        size="lg"
        :squared="squaredAvatar"
      />
      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-center gap-2">
          <h1 class="m-0 text-crm-record font-semibold tracking-crm-tight text-crm-fg">
            {{ title }}
          </h1>
          <AstraBadge v-if="status" :label="status" :tone="statusTone" dot />
          <div class="ml-auto flex flex-wrap items-center gap-2">
            <slot name="actions" />
          </div>
        </div>
        <div
          v-if="meta.length || $slots.meta"
          class="mt-0.5 flex flex-wrap items-center gap-2.5 whitespace-nowrap text-crm-label text-crm-muted-fg"
        >
          <slot name="meta">
            <template v-for="(item, index) in meta" :key="item">
              <span v-if="index" class="size-[3px] rounded-full bg-crm-faint" aria-hidden="true" />
              <span>{{ item }}</span>
            </template>
          </slot>
        </div>
      </div>
    </div>
    <slot name="stage" />
  </header>
</template>

<script setup>
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import AstraBadge from '@/components/astra/AstraBadge.vue'

defineProps({
  title: { type: String, required: true },
  avatarSrc: { type: String, default: '' },
  squaredAvatar: { type: Boolean, default: false },
  status: { type: String, default: '' },
  statusTone: { type: String, default: 'mute' },
  meta: { type: Array, default: () => [] },
})
</script>
