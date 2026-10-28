<template>
  <div
    class="settings-page flex h-full min-h-0 w-full flex-1 flex-col overflow-hidden sm:grid sm:grid-cols-[220px_minmax(0,1fr)]"
  >
    <nav
      ref="navEl"
      class="settings-nav flex max-h-40 shrink-0 flex-col overflow-y-auto border-b border-outline-gray-2 bg-surface-elevation-1 sm:max-h-none sm:border-b-0 sm:border-r"
      :aria-label="__('Settings')"
    >
      <div v-for="(group, index) in groups" :key="group.id">
        <div
          class="settings-nav-label text-ink-gray-5"
          :class="index === 0 ? 'mt-0' : 'mt-3'"
        >
          {{ __(group.label) }}
        </div>
        <div class="flex flex-col gap-0.5">
          <button
            v-for="item in group.items"
            :key="item.slug"
            type="button"
            class="settings-nav-item flex w-full items-center gap-2 px-2 text-left text-sm text-ink-gray-7 hover:bg-surface-gray-2"
            :class="{ 'is-active': item.slug === active?.slug }"
            :data-section="item.slug"
            :aria-current="item.slug === active?.slug ? 'page' : undefined"
            @click="open(item.slug)"
          >
            <Avatar
              v-if="item.slug === 'profile'"
              size="xs"
              :label="user.full_name"
              :image="user.user_image"
            />
            <Icon
              v-else
              :icon="item.icon"
              class="size-4 shrink-0"
              :class="item.iconClass"
            />
            <span class="truncate">{{ __(item.label) }}</span>
          </button>
        </div>
      </div>
    </nav>
    <div class="min-h-0 min-w-0 flex-1 overflow-y-auto bg-surface-elevation-2">
      <component :is="active.component" v-if="ready && active" />
    </div>
  </div>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import { visibleSettingsGroups } from '@/components/Settings/settingsSections'
import { usersStore } from '@/stores/users'
import { Avatar } from 'frappe-ui'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  section: { type: String, default: '' },
})

const router = useRouter()
const navEl = ref(null)
const { getUser, users } = usersStore()
const user = computed(() => getUser() || {})
const ready = computed(() => Boolean(users.fetched))
const groups = computed(() => visibleSettingsGroups())
const active = computed(() => {
  const items = groups.value.flatMap((group) => group.items)
  const wanted = props.section || ''
  return items.find((item) => item.slug === wanted) || items[0] || null
})

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

<style scoped>
.settings-nav {
  padding: 12px 10px;
}

.settings-nav-label {
  padding: 4px 8px;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.settings-nav-item {
  height: 30px;
  border-radius: 6px;
}

.settings-nav-item.is-active {
  background: var(--crm-primary-soft, var(--surface-gray-3));
  color: var(--crm-primary, var(--ink-gray-8));
}
</style>
