<template>
  <article
    class="flex min-h-[118px] cursor-pointer flex-col gap-[7px] rounded-crm-card border border-crm-border bg-crm-card p-[10px_11px] text-[12px] transition-shadow"
    :class="{
      'rotate-[-1.5deg] shadow-crm-drag ring-[1.5px] ring-crm-primary': dragging,
      'opacity-40 [border-style:dashed]': faded,
    }"
    role="button"
    tabindex="0"
    @click="$emit('click')"
    @keydown.enter.prevent="$emit('click')"
    @keydown.space.prevent="$emit('activate')"
  >
    <div class="text-[12.5px] font-semibold leading-[1.2] text-crm-fg">
      {{ title }}
    </div>
    <div v-if="value" class="text-[13px] font-bold leading-[1.2] text-crm-fg">
      {{ value }}
    </div>

    <!-- Owner row: icon + name ··· avatar (Figma .dc .f) -->
    <div
      v-if="owner || $slots.owner"
      class="flex h-[18px] items-center gap-2 text-[11.5px] text-crm-muted-fg"
    >
      <slot name="owner">
        <svg
          class="size-3.5 shrink-0"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          aria-hidden="true"
        >
          <circle cx="12" cy="8" r="4" />
          <path d="M4 21a8 8 0 0 1 16 0" />
        </svg>
        <span class="min-w-0 truncate">{{ owner }}</span>
        <span class="flex-1" />
        <AstraAvatar :name="avatarName || owner" size="sm" />
      </slot>
    </div>

    <!-- Date + chips row -->
    <div
      v-if="date || chips.length || badge || $slots.badge || $slots.chips || movingLabel"
      class="flex h-[18px] items-center gap-2 text-[11.5px] text-crm-muted-fg"
    >
      <template v-if="movingLabel">
        <svg
          class="size-3.5 shrink-0 text-crm-primary"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          aria-hidden="true"
        >
          <path
            d="M5 9l-3 3 3 3M9 5l3-3 3 3M15 19l-3 3-3-3M19 9l3 3-3 3M2 12h20M12 2v20"
          />
        </svg>
        <span class="min-w-0 truncate font-medium text-crm-primary">{{
          movingLabel
        }}</span>
      </template>
      <template v-else>
        <svg
          v-if="date"
          class="size-3.5 shrink-0"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          aria-hidden="true"
        >
          <rect x="3" y="4" width="18" height="18" rx="2" />
          <path d="M16 2v4M8 2v4M3 10h18" />
        </svg>
        <span v-if="date" class="shrink-0 tabular-nums">{{ date }}</span>
        <span class="flex-1" />
        <slot name="chips">
          <span
            v-for="chip in chips"
            :key="chip.label"
            class="inline-flex h-[18px] items-center gap-1 whitespace-nowrap rounded px-1.5 text-[10.5px] font-semibold"
            :class="miniToneClass(chip.tone)"
          >
            {{ chip.label }}
          </span>
        </slot>
        <slot name="badge">
          <span
            v-if="badge"
            class="inline-flex h-[18px] items-center whitespace-nowrap rounded px-1.5 text-[10.5px] font-semibold"
            :class="miniToneClass(badgeTone)"
          >
            {{ badge }}
          </span>
        </slot>
      </template>
    </div>
  </article>
</template>

<script setup>
import AstraAvatar from '@/components/astra/AstraAvatar.vue'

defineProps({
  title: { type: String, required: true },
  value: { type: String, default: '' },
  owner: { type: String, default: '' },
  /** Avatar initials source (deal owner); defaults to owner text. */
  avatarName: { type: String, default: '' },
  /** @deprecated Prefer owner row; kept for callers that still pass meta. */
  ownerRight: { type: Boolean, default: false },
  meta: { type: String, default: '' },
  date: { type: String, default: '' },
  badge: { type: String, default: '' },
  badgeTone: { type: String, default: 'mute' },
  chips: { type: Array, default: () => [] },
  dragging: { type: Boolean, default: false },
  /** Source-column placeholder while a card is mid-drag (parity / DnD). */
  faded: { type: Boolean, default: false },
  /** Drag helper caption, e.g. "Moving to Negotiation · 70%". */
  movingLabel: { type: String, default: '' },
})

defineEmits(['click', 'activate'])

function miniToneClass(tone) {
  const map = {
    ok: 'bg-crm-success-soft text-crm-success',
    success: 'bg-crm-success-soft text-crm-success',
    warn: 'bg-crm-warning-soft text-crm-warning',
    warning: 'bg-crm-warning-soft text-crm-warning',
    bad: 'bg-crm-danger-soft text-crm-danger',
    danger: 'bg-crm-danger-soft text-crm-danger',
    info: 'bg-crm-teal-soft text-crm-teal',
    teal: 'bg-crm-teal-soft text-crm-teal',
    call: 'bg-crm-teal-soft text-crm-teal',
    blue: 'bg-crm-blue-soft text-crm-blue',
    note: 'bg-crm-warning-soft text-crm-warning',
    mute: 'bg-crm-neutral-soft text-crm-muted-fg',
    primary: 'bg-crm-primary-soft text-crm-primary',
  }
  return map[tone] || map.mute
}
</script>
