<template>
  <article
    class="flex cursor-pointer flex-col gap-1.5 rounded-crm-card border border-crm-border bg-crm-card p-[10px_11px] text-xs transition-shadow"
    :class="{ 'rotate-[-1.5deg] shadow-crm-drag': dragging }"
    role="button"
    tabindex="0"
    @click="$emit('click')"
    @keydown.enter.prevent="$emit('click')"
    @keydown.space.prevent="$emit('activate')"
  >
    <div class="text-crm-label font-semibold text-crm-fg">{{ title }}</div>
    <div v-if="value" class="text-crm-body font-bold text-crm-fg">{{ value }}</div>
    <div class="flex items-center gap-2 text-crm-meta text-crm-muted-fg">
      <AstraAvatar v-if="owner" :name="owner" size="sm" />
      <span v-if="owner" class="truncate">{{ owner }}</span>
      <span v-if="date" class="ml-auto shrink-0">{{ date }}</span>
    </div>
    <div v-if="badge || $slots.badge" class="mt-0.5">
      <slot name="badge">
        <AstraBadge :label="badge" :tone="badgeTone" dot />
      </slot>
    </div>
  </article>
</template>

<script setup>
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import AstraBadge from '@/components/astra/AstraBadge.vue'

defineProps({
  title: { type: String, required: true },
  value: { type: String, default: '' },
  owner: { type: String, default: '' },
  date: { type: String, default: '' },
  badge: { type: String, default: '' },
  badgeTone: { type: String, default: 'mute' },
  dragging: { type: Boolean, default: false },
})

defineEmits(['click', 'activate'])
</script>
