<template>
  <section
    class="flex shrink-0 flex-col overflow-hidden rounded-crm-panel border border-crm-border bg-crm-muted"
    :class="[{ 'h-full min-h-0': fillHeight }, widthClass]"
    :style="widthStyle"
  >
    <header class="flex shrink-0 flex-col gap-1 border-b border-crm-border px-3 pb-2 pt-2.5">
      <div class="flex items-center gap-2">
        <slot name="title">
          <!-- crm.css .st — stage pill with square marker -->
          <span
            v-if="title"
            class="inline-flex h-[22px] min-w-0 items-center gap-1.5 truncate rounded-md bg-crm-neutral-soft px-2 text-[11.5px] font-semibold text-crm-fg"
          >
            <span
              v-if="color"
              class="size-[7px] shrink-0 rounded-[2px]"
              :style="{ backgroundColor: color }"
              aria-hidden="true"
            />
            <span class="truncate">{{ title }}</span>
          </span>
          <AstraBadge v-else-if="badgeTitle" :label="badgeTitle" :tone="tone" />
        </slot>
        <span class="ml-auto shrink-0 text-xs tabular-nums text-crm-muted-fg">{{
          count
        }}</span>
      </div>
      <div
        v-if="subtitle || subtitleRight"
        class="flex justify-between text-[11.5px] text-crm-muted-fg"
      >
        <span class="tabular-nums">{{ subtitle }}</span>
        <span v-if="subtitleRight" class="tabular-nums">{{
          subtitleRight
        }}</span>
      </div>
    </header>
    <div class="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto p-2">
      <slot />
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import AstraBadge from '@/components/astra/AstraBadge.vue'

const props = defineProps({
  title: { type: String, default: '' },
  /** Legacy filled-pill title; prefer `title` + `color` for stage headers. */
  badgeTitle: { type: String, default: '' },
  tone: { type: String, default: 'mute' },
  /** CSS colour for the stage dot (e.g. var(--crm-c6)). */
  color: { type: String, default: '' },
  count: { type: [Number, String], default: 0 },
  subtitle: { type: String, default: '' },
  /** Right-aligned subtitle fragment (e.g. probability %). */
  subtitleRight: { type: String, default: '' },
  fillHeight: { type: Boolean, default: false },
  /**
   * Column width. Figma deals board capture uses 192px (inline override of
   * crm.css 258px default). Pass a number (px) or CSS length.
   */
  width: { type: [Number, String], default: null },
})

const widthClass = computed(() =>
  props.width == null ? 'w-crm-kanban-col' : '',
)
const widthStyle = computed(() => {
  if (props.width == null) return undefined
  const w =
    typeof props.width === 'number' ? `${props.width}px` : String(props.width)
  return { width: w }
})
</script>
