<template>
  <div class="flex h-full min-h-0 w-full flex-1 flex-col overflow-hidden bg-crm-bg">
    <div
      v-if="showConceptBar"
      class="flex h-[30px] shrink-0 items-center gap-2 border-b border-dashed border-crm-border-strong bg-crm-muted px-6 text-[12px] leading-none text-crm-muted-fg"
    >
      <Icon icon="triangle-alert" class="size-3.5 shrink-0 text-crm-warning" />
      <b class="font-semibold text-crm-fg">{{ __('Concept') }}</b>
      <span>
        {{
          __(
            'In-app stage editor. Stages are real, configurable records today; this editor screen is new and needs backend work.',
          )
        }}
      </span>
    </div>
    <div
      class="settings-page flex min-h-0 w-full flex-1 flex-col overflow-hidden sm:grid sm:grid-cols-crm-settings"
    >
      <nav
        ref="navEl"
        class="flex max-h-40 shrink-0 flex-col gap-px overflow-y-auto border-b border-crm-border bg-crm-card px-2.5 py-3 sm:max-h-none sm:border-b-0 sm:border-r"
        :aria-label="__('Settings')"
      >
        <template v-for="group in groups" :key="group.id">
          <div
            class="px-2.5 pb-1 pt-2.5 text-[10.5px] font-bold uppercase leading-[1.45] tracking-[0.06em] text-crm-faint"
          >
            {{ __(group.label) }}
          </div>
          <button
            v-for="item in group.items"
            :key="item.slug"
            type="button"
            class="flex h-[30px] w-full shrink-0 items-center rounded-crm-chip border-0 px-2.5 text-left text-[12.5px] leading-none font-medium text-crm-muted-fg focus-visible:outline-none focus-visible:shadow-crm-focus"
            :class="
              item.slug === active?.slug
                ? 'bg-crm-primary-soft font-semibold text-crm-primary'
                : 'bg-transparent hover:bg-crm-muted'
            "
            :data-section="item.slug"
            :aria-current="item.slug === active?.slug ? 'page' : undefined"
            @click="open(item.slug)"
          >
            <span class="truncate">{{ __(item.label) }}</span>
          </button>
        </template>
      </nav>
      <div class="min-h-0 min-w-0 flex-1 overflow-y-auto bg-crm-bg">
        <component :is="active.component" v-if="ready && active" />
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  accessibleSettingsGroups,
  visibleSettingsGroups,
} from '@/components/Settings/settingsSections'
import Icon from '@/components/Icon.vue'
import { usersStore } from '@/stores/users'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  section: { type: String, default: '' },
})

const router = useRouter()
const navEl = ref(null)
const { users } = usersStore()
const ready = computed(() => Boolean(users.fetched))
const groups = computed(() => visibleSettingsGroups())
const active = computed(() => {
  const items = accessibleSettingsGroups().flatMap((group) => group.items)
  const wanted = props.section || ''
  return items.find((item) => item.slug === wanted) || items[0] || null
})
const showConceptBar = computed(
  () => ready.value && active.value?.slug === 'pipeline-stages',
)

function open(slug) {
  if (slug === props.section) return
  router.push({ name: 'Settings', params: { section: slug } })
}

function syncSection() {
  if (!ready.value || !active.value) return
  if ((props.section || '') === active.value.slug) return
  router.replace({
    name: 'Settings',
    params: { section: active.value.slug },
  })
}

watch(() => [props.section, ready.value, active.value?.slug], syncSection)
onMounted(syncSection)

watch(
  () => active.value?.slug,
  (slug) => {
    if (!slug) return
    nextTick(() => {
      navEl.value
        ?.querySelector(`[data-section="${slug}"]`)
        ?.scrollIntoView({ block: 'nearest' })
    })
  },
  { immediate: true },
)
</script>
