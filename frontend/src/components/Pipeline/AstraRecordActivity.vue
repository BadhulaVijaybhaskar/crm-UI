<template>
  <div class="flex min-h-0 flex-1 flex-col overflow-auto bg-crm-bg">
    <div
      class="mx-crm-page-x mt-3.5 flex items-center gap-1.5 rounded-[9px] border border-crm-border bg-crm-card p-1.5"
    >
      <button
        v-for="opt in composeOpts"
        :key="opt.id"
        type="button"
        class="inline-flex h-[30px] items-center gap-1.5 rounded-md px-2.5 text-crm-label font-semibold"
        :class="
          composeMode === opt.id
            ? 'bg-crm-primary-soft text-crm-primary'
            : 'text-crm-muted-fg'
        "
        @click="composeMode = opt.id"
      >
        <span :class="opt.icon" class="size-3.5" aria-hidden="true" />
        {{ opt.label }}
      </button>
      <span class="mx-1 flex-1 truncate px-2 text-crm-label text-crm-faint">{{
        placeholder
      }}</span>
      <AstraButton
        variant="primary"
        size="sm"
        :label="actionLabel || (composeMode === 'email' ? __('Compose') : __('Save'))"
      />
    </div>

    <div class="flex flex-col px-crm-page-x py-3.5">
      <template v-for="(group, gi) in groups" :key="group.label">
        <div
          class="pb-2.5 pl-[42px] text-[11px] font-bold uppercase tracking-[0.06em] text-crm-faint"
          :class="gi ? 'pt-1' : ''"
        >
          {{ group.label }}
        </div>
        <article
          v-for="(item, ii) in group.items"
          :key="item.id"
          class="relative grid grid-cols-[30px_minmax(0,1fr)] gap-3 pb-3.5"
        >
          <span
            v-if="!(gi === groups.length - 1 && ii === group.items.length - 1)"
            class="absolute bottom-0 left-[14px] top-[30px] w-[1.5px] bg-crm-border"
            aria-hidden="true"
          />
          <span
            class="inline-flex size-[30px] items-center justify-center rounded-lg"
            :class="toneClass[item.tone] || toneClass.mute"
          >
            <span :class="item.icon" class="size-3.5" aria-hidden="true" />
          </span>
          <div class="min-w-0">
            <div
              class="flex min-h-[30px] flex-wrap items-center gap-2 text-crm-label"
            >
              <b class="font-semibold text-crm-fg">{{ item.title }}</b>
              <span v-if="item.subtitle" class="text-crm-muted-fg">{{
                item.subtitle
              }}</span>
              <span
                v-if="item.chip"
                class="inline-flex h-[22px] items-center rounded-md bg-crm-teal-soft px-2 text-[11.5px] font-semibold text-crm-teal"
              >
                {{ item.chip }}
              </span>
              <span
                v-if="item.fromChip"
                class="inline-flex h-[22px] items-center gap-1 rounded-md bg-crm-neutral-soft px-2 text-[11.5px] font-semibold text-crm-muted-fg"
              >
                <i class="size-1.5 rounded-full bg-crm-faint" />
                {{ item.fromChip }}
              </span>
              <span v-if="item.fromChip && item.toChip" class="text-crm-faint"
                >→</span
              >
              <span
                v-if="item.toChip"
                class="inline-flex h-[22px] items-center gap-1 rounded-md bg-crm-warning-soft px-2 text-[11.5px] font-semibold text-crm-warning"
              >
                <i class="size-1.5 rounded-full bg-crm-warning" />
                {{ item.toChip }}
              </span>
              <span
                v-if="item.time"
                class="ml-auto whitespace-nowrap text-[11.5px] text-crm-faint"
              >
                {{ item.time }}
              </span>
            </div>
            <div
              v-if="item.card"
              class="mt-1 rounded-lg border border-crm-border bg-crm-card px-3 py-2.5 text-crm-label"
            >
              <div
                v-if="item.card.rows?.length"
                class="flex flex-wrap items-center gap-2"
              >
                <span
                  v-for="row in item.card.rows"
                  :key="row"
                  class="text-crm-muted-fg"
                  >{{ row }}</span
                >
              </div>
              <p
                v-if="item.card.body"
                class="m-0 mt-1 leading-relaxed text-crm-muted-fg"
              >
                {{ item.card.body }}
              </p>
              <a
                v-if="item.card.link"
                class="mt-1 inline-flex text-crm-primary"
                href="#"
                @click.prevent
              >
                {{ item.card.link }}
              </a>
            </div>
          </div>
        </article>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import AstraButton from '@/components/astra/AstraButton.vue'

const props = defineProps({
  /** Pre-grouped Figma-style timeline from fixtures / adapters. */
  groups: { type: Array, default: () => [] },
  /** Initial composer chip (note | email | task | call). */
  initialCompose: { type: String, default: 'note' },
  /** Override composer placeholder (Figma deal: email recipient line). */
  composePlaceholder: { type: String, default: '' },
  /** Override primary action label (Figma deal email: Compose). */
  actionLabel: { type: String, default: '' },
})

const composeMode = ref(props.initialCompose || 'note')
const composeOpts = [
  { id: 'note', label: __('Note'), icon: 'lucide-file-text' },
  { id: 'email', label: __('Email'), icon: 'lucide-mail' },
  { id: 'task', label: __('Task'), icon: 'lucide-square-check' },
  { id: 'call', label: __('Log call'), icon: 'lucide-phone' },
]

const placeholder = computed(() => {
  if (props.composePlaceholder) return props.composePlaceholder
  if (composeMode.value === 'email') return __('Write an email…')
  if (composeMode.value === 'task') return __('Describe the task…')
  if (composeMode.value === 'call') return __('Log call notes…')
  return __('Write a note for the team…')
})

const toneClass = {
  task: 'bg-crm-success-soft text-crm-success',
  call: 'bg-crm-teal-soft text-crm-teal',
  mail: 'bg-crm-blue-soft text-crm-blue',
  note: 'bg-crm-warning-soft text-crm-warning',
  stg: 'bg-crm-primary-soft text-crm-primary',
  mute: 'bg-crm-neutral-soft text-crm-muted-fg',
}
</script>
