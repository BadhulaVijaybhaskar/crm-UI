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
      <span v-if="meta" class="min-w-0 truncate">{{ meta }}</span>
      <span v-else-if="owner && !ownerRight" class="min-w-0 truncate">{{ owner }}</span>
      <span v-if="date" class="shrink-0" :class="{ 'ml-auto': !ownerRight }">
        {{ date }}
      </span>
      <AstraAvatar
        v-if="owner && ownerRight"
        class="ml-auto"
        :name="owner"
        size="sm"
      />
      <AstraAvatar
        v-else-if="owner && !ownerRight"
        :name="owner"
        size="sm"
      />
    </div>
    <div
      v-if="chips.length || badge || $slots.badge || $slots.chips"
      class="mt-0.5 flex flex-wrap gap-1"
    >
      <slot name="chips">
        <AstraBadge
          v-for="chip in chips"
          :key="chip.label"
          :label="chip.label"
          :tone="chip.tone || 'mute'"
          :dot="chip.dot !== false"
        />
      </slot>
      <slot name="badge">
        <AstraBadge v-if="badge" :label="badge" :tone="badgeTone" dot />
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
  /** Put owner avatar on the right (Deals board QA). */
  ownerRight: { type: Boolean, default: false },
  /** Secondary meta text when owner is avatar-only on the right. */
  meta: { type: String, default: '' },
  date: { type: String, default: '' },
  badge: { type: String, default: '' },
  badgeTone: { type: String, default: 'mute' },
  chips: { type: Array, default: () => [] },
  dragging: { type: Boolean, default: false },
})

defineEmits(['click', 'activate'])
</script>
