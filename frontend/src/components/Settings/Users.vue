<template>
  <div class="flex h-full flex-col gap-6 p-6 text-ink-gray-8">
    <!-- Header -->
    <div class="flex items-start justify-between gap-3 px-2 pt-2">
      <div class="flex min-w-0 flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Users') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Who can sign in and what they can see.') }}
        </p>
      </div>
      <div class="flex shrink-0 flex-wrap items-center justify-end gap-2">
        <Button
          :label="__('Add existing user')"
          variant="outline"
          @click="showAddExistingModal = true"
        />
        <Button
          :label="__('Invite new user')"
          variant="solid"
          icon-left="lucide-plus"
          @click="openSettings('invite-user')"
        />
      </div>
    </div>

    <!-- loading state -->
    <div v-if="users.loading" class="flex mt-28 justify-between w-full h-full">
      <Button
        :loading="users.loading"
        variant="ghost"
        class="w-full"
        size="2xl"
      />
    </div>

    <!-- Empty State -->
    <EmptyState
      v-if="!users.loading && users.data?.crmUsers?.length == 1"
      name="Users"
      :description="__('Add one to get started.')"
      icon="user"
    />

    <!-- Users List -->
    <div
      v-if="!users.loading && users.data?.crmUsers?.length > 1"
      class="flex flex-col overflow-hidden"
    >
      <div class="mb-4 flex flex-col gap-3 px-2 pt-0.5">
        <div class="flex flex-wrap gap-1.5" role="group" :aria-label="__('Role')">
          <button
            v-for="chip in roleFilters"
            :key="chip.value"
            type="button"
            class="h-7 rounded-full px-3 text-sm"
            :class="
              currentRole === chip.value
                ? 'bg-surface-gray-7 text-ink-white'
                : 'bg-surface-gray-2 text-ink-gray-7'
            "
            :aria-pressed="currentRole === chip.value"
            @click="currentRole = chip.value"
          >
            {{ chip.label }} {{ chip.count }}
          </button>
        </div>
        <TextInput
          v-if="users.data?.crmUsers?.length > 10"
          ref="searchRef"
          v-model="search"
          :placeholder="__('Search User')"
          class="w-full"
          :debounce="300"
        >
          <template #prefix>
            <span
              class="lucide-search h-4 w-4 text-ink-gray-6"
              aria-hidden="true"
            />
          </template>
        </TextInput>
      </div>
      <p v-if="!usersList.length" class="px-2 py-6 text-p-sm text-ink-gray-5">
        {{ __('No users match this filter.') }}
      </p>
      <ul
        v-else
        class="divide-y divide-outline-elevation-2 overflow-y-auto px-2"
      >
        <template v-for="user in usersList" :key="user.name">
          <li class="flex items-center justify-between py-2">
            <div class="flex items-center">
              <div class="relative shrink-0">
                <Avatar
                  :image="user.user_image"
                  :label="user.full_name"
                  size="xl"
                />
                <div
                  class="absolute -bottom-0.5 -right-0.5 flex rounded-full bg-surface-elevation-2 p-0.5"
                >
                  <AvailabilityDot :user="user.name" class="!size-2.5" />
                </div>
              </div>
              <div class="flex flex-col ml-3">
                <div class="flex items-center text-p-base text-ink-gray-8">
                  {{ user.full_name }}
                </div>
                <div class="text-p-sm text-ink-gray-5">
                  {{ user.name }}
                </div>
              </div>
            </div>
            <div class="flex gap-2 items-center flex-row-reverse">
              <Dropdown
                :options="getMoreOptions(user)"
                :button="{
                  icon: 'lucide-more-horizontal',
                  onblur: (e) => {
                    e.stopPropagation()
                    confirmRemove = false
                  },
                }"
                align="end"
              />
              <Tooltip
                v-if="isManager() && user.role == 'System Manager'"
                :text="__('Cannot change role of user with Admin access')"
              >
                <Button :label="__('Admin')" icon-left="lucide-shield" />
              </Tooltip>
              <Dropdown
                v-else
                :options="getDropdownOptions(user)"
                :button="{
                  label: roleMap[user.role],
                  iconRight: 'lucide-chevron-down',
                  iconLeft:
                    user.role === 'System Manager'
                      ? 'lucide-shield'
                      : user.role === 'Sales Manager'
                        ? 'lucide-briefcase'
                        : 'lucide-user-check',
                }"
                align="end"
              />
            </div>
          </li>
        </template>
      </ul>
      <div
        v-if="!users.loading && users.hasNextPage"
        class="flex justify-center"
      >
        <Button
          class="mt-3.5 p-2"
          :loading="users.loading"
          :label="__('Load More')"
          icon-left="lucide-refresh-cw"
          @click="() => users.next()"
        />
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
import AvailabilityDot from '@/components/AvailabilityDot.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { openSettings } from '@/composables/settings'
import { usersStore } from '@/stores/users'
import {
  Dropdown,
  Avatar,
  TextInput,
  toast,
  call,
  Tooltip,
  Button,
} from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'
import { ConfirmDelete } from '../../utils'

const { users, isAdmin, isManager } = usersStore()

const showAddExistingModal = ref(false)
const searchRef = ref(null)
const search = ref('')
const currentRole = ref('All')

const roleMap = {
  'System Manager': __('Admin'),
  'Sales Manager': __('Manager'),
  'Sales User': __('Sales User'),
}

const countableUsers = computed(
  () =>
    users.data?.crmUsers?.filter((user) => user.name !== 'Administrator') ||
    [],
)

const roleFilters = computed(() => {
  const counts = {
    All: countableUsers.value.length,
    'System Manager': 0,
    'Sales Manager': 0,
    'Sales User': 0,
  }
  for (const user of countableUsers.value) {
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
  let filteredUsers =
    users.data?.crmUsers?.filter((user) => user.name !== 'Administrator') || []

  return filteredUsers
    .filter(
      (user) =>
        user.name?.includes(search.value) ||
        user.full_name?.includes(search.value),
    )
    .filter((user) => {
      if (currentRole.value === 'All') return true
      return user.role === currentRole.value
    })
})

const confirmRemove = ref(false)

function getMoreOptions(user) {
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

  return options.filter((option) => option.condition?.() || true)
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

onMounted(() => {
  if (searchRef.value) {
    searchRef.value.focus()
  }
})
</script>
