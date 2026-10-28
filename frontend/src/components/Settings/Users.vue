<template>
  <div class="flex h-full min-h-0 flex-col bg-crm-bg text-crm-fg">
    <AstraPageHeader
      :title="__('Users')"
      :description="__('Who can sign in and what they can see.')"
    >
      <template #actions>
        <ExampleDataTag />
        <AstraButton
          :label="__('Add existing user')"
          @click="showAddExistingModal = true"
        />
        <AstraButton
          variant="primary"
          :label="__('Invite new user')"
          @click="openSettings('invite-user')"
        >
          <template #prefix>
            <Icon icon="plus" class="size-3.5" />
          </template>
        </AstraButton>
      </template>
    </AstraPageHeader>

    <div
      v-if="showDirectory"
      class="flex flex-wrap items-center gap-2 px-crm-page-x pb-3"
    >
      <AstraInput
        v-model="search"
        class="w-full max-w-xs"
        :placeholder="__('Search user')"
      >
        <template #prefix>
          <Icon icon="search" class="size-4" />
        </template>
      </AstraInput>
      <div class="flex flex-wrap gap-1.5" role="group" :aria-label="__('Role')">
        <button
          v-for="chip in roleFilters"
          :key="chip.value"
          type="button"
          class="inline-flex h-7 items-center gap-1 rounded-full px-2.5 text-crm-meta font-medium"
          :class="
            currentRole === chip.value
              ? 'bg-crm-card font-semibold text-crm-fg shadow-[inset_0_0_0_1px_var(--crm-border-strong)]'
              : 'bg-crm-muted text-crm-muted-fg'
          "
          :aria-pressed="currentRole === chip.value"
          @click="currentRole = chip.value"
        >
          {{ chip.label }}
          <span class="text-crm-micro font-semibold text-crm-faint">
            {{ chip.count }}
          </span>
        </button>
      </div>
    </div>

    <div class="min-h-0 flex-1 overflow-y-auto px-crm-page-x pb-6">
      <div
        v-if="users.loading && !users.data?.crmUsers"
        class="py-16 text-center text-crm-body text-crm-muted-fg"
      >
        {{ __('Loading…') }}
      </div>

      <AstraEmptyState
        v-else-if="!showDirectory"
        :title="__('Users')"
        :body="__('Add one to get started.')"
      />

      <div v-else class="flex items-start gap-4">
        <div
          class="min-w-0 flex-1 overflow-hidden rounded-crm-panel border border-crm-border bg-crm-card"
        >
          <div class="overflow-x-auto">
            <div class="min-w-0">
              <div
                class="grid h-crm-th grid-cols-[minmax(180px,1.6fr)_120px_96px_100px_32px] items-center gap-2 bg-crm-muted px-4 text-crm-meta font-semibold text-crm-muted-fg"
              >
                <span>{{ __('Name') }}</span>
                <span>{{ __('Role') }}</span>
                <span>{{ __('Status') }}</span>
                <span>{{ __('Last active') }}</span>
                <span />
              </div>
              <p
                v-if="!usersList.length"
                class="px-3 py-8 text-crm-body text-crm-muted-fg"
              >
                {{ __('No users match this filter.') }}
              </p>
              <ul v-else>
                <li
                  v-for="user in usersList"
                  :key="user.invited ? `invite-${user.name}` : user.name"
                  class="grid h-[46px] grid-cols-[minmax(180px,1.6fr)_120px_96px_100px_32px] items-center gap-2 border-t border-crm-border px-4"
                >
                  <div class="flex min-w-0 items-center gap-2.5">
                    <AstraAvatar
                      :name="user.full_name"
                      :seed="user.email || user.name"
                      :src="user.user_image || ''"
                    />
                    <div class="min-w-0">
                      <div
                        class="truncate text-crm-label font-medium text-crm-fg"
                      >
                        {{ displayName(user) }}
                      </div>
                      <div
                        v-if="user.email && user.email !== user.full_name"
                        class="truncate text-crm-micro text-crm-faint"
                      >
                        {{ user.email }}
                      </div>
                    </div>
                  </div>

                  <div>
                    <span
                      v-if="user.invited || isLockedAdmin(user)"
                      class="inline-flex h-7 items-center gap-1 rounded-full px-2.5 text-crm-meta font-semibold"
                      :class="
                        user.role === 'System Manager'
                          ? 'bg-crm-primary-soft text-crm-primary'
                          : 'bg-crm-muted text-crm-fg'
                      "
                    >
                      {{ roleMap[user.role] || user.role }}
                      <Icon
                        v-if="isLockedAdmin(user)"
                        icon="lock"
                        class="size-3"
                      />
                    </span>
                    <Dropdown
                      v-else
                      :options="getDropdownOptions(user)"
                      align="end"
                    >
                      <template #default>
                        <button
                          type="button"
                          class="inline-flex h-7 items-center gap-1 rounded-full bg-crm-muted px-2.5 text-crm-meta font-semibold text-crm-fg"
                        >
                          {{ roleMap[user.role] || user.role }}
                          <Icon
                            icon="chevron-down"
                            class="size-3 text-crm-faint"
                          />
                        </button>
                      </template>
                    </Dropdown>
                  </div>

                  <div>
                    <span
                      class="inline-flex h-[22px] items-center gap-1.5 rounded-full px-2 text-crm-micro font-semibold"
                      :class="
                        user.invited
                          ? 'bg-crm-warning-soft text-crm-warning'
                          : 'bg-crm-success-soft text-crm-success'
                      "
                    >
                      <span class="size-1.5 rounded-full bg-current" />
                      {{ user.invited ? __('Invited') : __('Active') }}
                    </span>
                  </div>

                  <span class="text-crm-label text-crm-muted-fg">
                    {{ lastActiveLabel(user) }}
                  </span>

                  <Dropdown :options="getMoreOptions(user)" align="end">
                    <template #default>
                      <button
                        type="button"
                        class="inline-flex size-7 items-center justify-center rounded-crm-chip text-crm-faint hover:bg-crm-muted"
                        :aria-label="__('More')"
                      >
                        <Icon icon="more-horizontal" class="size-4" />
                      </button>
                    </template>
                  </Dropdown>
                </li>
              </ul>
            </div>
          </div>
          <div
            v-if="!users.loading && users.hasNextPage"
            class="flex justify-center border-t border-crm-border py-3"
          >
            <AstraButton
              :label="__('Load More')"
              :loading="users.loading"
              @click="() => users.next()"
            />
          </div>
        </div>

        <aside class="hidden w-[260px] shrink-0 lg:block">
          <div
            class="rounded-crm-panel border border-crm-border bg-crm-card p-4"
          >
            <h2 class="text-crm-panel font-semibold text-crm-fg">
              {{ __('What each role sees') }}
            </h2>
            <dl class="mt-3 flex flex-col gap-3">
              <div
                v-for="note in roleNotes"
                :key="note.role"
                class="grid grid-cols-[92px_minmax(0,1fr)] gap-2 text-crm-label"
              >
                <dt class="text-crm-muted-fg">{{ note.role }}</dt>
                <dd class="text-crm-fg">{{ note.detail }}</dd>
              </div>
            </dl>
            <p
              class="mt-4 flex gap-2 border-t border-crm-border pt-3 text-crm-meta text-crm-muted-fg"
            >
              <Icon icon="lock" class="mt-0.5 size-3.5 shrink-0" />
              <span>
                {{
                  __(
                    "The role of a user with Admin access can't be changed here.",
                  )
                }}
              </span>
            </p>
          </div>
        </aside>
      </div>
    </div>
  </div>
  <AddExistingUserModal
    v-if="showAddExistingModal"
    v-model="showAddExistingModal"
  />
</template>

<script setup>
import AddExistingUserModal from '@/components/Modals/AddExistingUserModal.vue'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import AstraButton from '@/components/astra/AstraButton.vue'
import AstraEmptyState from '@/components/astra/AstraEmptyState.vue'
import AstraInput from '@/components/astra/AstraInput.vue'
import AstraPageHeader from '@/components/astra/AstraPageHeader.vue'
import ExampleDataTag from '@/components/astra/ExampleDataTag.vue'
import Icon from '@/components/Icon.vue'
import { openSettings } from '@/composables/settings'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { Dropdown, createListResource, dayjs, call, toast } from 'frappe-ui'
import { ref, computed } from 'vue'
import { ConfirmDelete } from '../../utils'

const { users, isAdmin, isManager } = usersStore()
const session = sessionStore()

const showAddExistingModal = ref(false)
const search = ref('')
const currentRole = ref('All')

const roleMap = {
  'System Manager': __('Admin'),
  'Sales Manager': __('Manager'),
  'Sales User': __('Sales User'),
}

const roleNotes = [
  {
    role: __('Sales User'),
    detail: __('Own leads, deals and activity'),
  },
  {
    role: __('Manager'),
    detail: __('Their team via Sales hierarchy'),
  },
  {
    role: __('Admin'),
    detail: __('Everything, plus Settings'),
  },
]

const pendingInvitations = createListResource({
  type: 'list',
  doctype: 'CRM Invitation',
  filters: { status: 'Pending' },
  fields: ['name', 'email', 'role'],
  pageLength: 999,
  auto: true,
})

const countableUsers = computed(
  () =>
    users.data?.crmUsers?.filter((user) => user.name !== 'Administrator') || [],
)

const inviteRows = computed(() =>
  (pendingInvitations.data || []).map((invite) => ({
    name: invite.name,
    email: invite.email,
    full_name: invite.email,
    role: invite.role,
    invited: true,
    user_image: null,
  })),
)

const showDirectory = computed(() => {
  if (users.loading && !users.data?.crmUsers) return false
  return countableUsers.value.length > 0 || inviteRows.value.length > 0
})

const roleFilters = computed(() => {
  const counts = {
    All: countableUsers.value.length + inviteRows.value.length,
    'System Manager': 0,
    'Sales Manager': 0,
    'Sales User': 0,
  }
  for (const user of [...countableUsers.value, ...inviteRows.value]) {
    if (counts[user.role] != null) counts[user.role] += 1
  }
  return [
    { label: __('All'), value: 'All', count: counts.All },
    {
      label: __('Admin'),
      value: 'System Manager',
      count: counts['System Manager'],
    },
    {
      label: __('Manager'),
      value: 'Sales Manager',
      count: counts['Sales Manager'],
    },
    {
      label: __('Sales User'),
      value: 'Sales User',
      count: counts['Sales User'],
    },
  ]
})

const usersList = computed(() => {
  const query = search.value.trim().toLowerCase()
  return [...countableUsers.value, ...inviteRows.value]
    .filter((user) => {
      if (!query) return true
      return (
        user.name?.toLowerCase().includes(query) ||
        user.full_name?.toLowerCase().includes(query) ||
        user.email?.toLowerCase().includes(query)
      )
    })
    .filter((user) => {
      if (currentRole.value === 'All') return true
      return user.role === currentRole.value
    })
})

const confirmRemove = ref(false)

function isYou(user) {
  return Boolean(user.session_user) || user.name === session.user
}

function displayName(user) {
  if (!isYou(user)) return user.full_name
  return `${user.full_name} · ${__('You')}`
}

function isLockedAdmin(user) {
  return isManager() && user.role === 'System Manager'
}

function lastActiveLabel(user) {
  if (user.invited) return '—'
  const raw = user.last_active || user.last_login
  if (!raw) return '—'
  const date = dayjs(raw)
  if (!date?.isValid?.()) return '—'
  if (date.isSame(dayjs(), 'day')) return __('Today')
  if (date.isSame(dayjs().subtract(1, 'day'), 'day')) return __('Yesterday')
  return date.format('D MMM')
}

function getMoreOptions(user) {
  if (user.invited) {
    return [
      {
        label: __('Remove'),
        icon: 'lucide-trash-2',
        onClick: () => pendingInvitations.delete.submit(user.name),
      },
    ]
  }
  return [
    ...ConfirmDelete({
      onConfirmDelete: () => removeUser(user),
      isConfirmingDelete: confirmRemove,
      label: __('Remove'),
    }),
  ]
}

function getDropdownOptions(user) {
  let options = [
    {
      label: __('Admin'),
      icon: 'lucide-shield',
      selected: user.role === 'System Manager',
      onClick: () => updateRole(user, 'System Manager'),
      condition: () => isAdmin(),
    },
    {
      label: __('Manager'),
      icon: 'lucide-briefcase',
      selected: user.role === 'Sales Manager',
      onClick: () => updateRole(user, 'Sales Manager'),
      condition: () => isAdmin(),
    },
    {
      label: __('Sales User'),
      icon: 'lucide-user-check',
      selected: user.role === 'Sales User',
      onClick: () => updateRole(user, 'Sales User'),
    },
  ]

  return options.filter((option) =>
    option.condition ? option.condition() : true,
  )
}

function updateRole(user, newRole) {
  if (user.role === newRole) return

  call('crm.api.user.update_user_role', {
    user: user.name,
    new_role: newRole,
  })
    .then(() => {
      toast.success(
        __('{0} has been granted {1} access', [
          user.full_name,
          roleMap[newRole],
        ]),
      )
      users.reload()
    })
    .catch((e) => {
      toast.error(e?.messages?.[0] || __('Something went wrong'))
    })
}

function removeUser(user) {
  call('crm.api.user.remove_crm_roles_from_user', {
    user: user.name,
  })
    .then(() => {
      toast.success(__('User {0} has been removed', [user.full_name]))
      users.reload()
    })
    .catch((e) => {
      toast.error(e?.messages?.[0] || __('Something went wrong'))
    })
}
</script>
