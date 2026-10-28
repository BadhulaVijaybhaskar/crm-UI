<template>
  <div class="flex h-full min-h-0 flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Reports" />
      </template>
      <template #right-header>
        <Button
          :label="__('Refresh')"
          :iconLeft="LucideRefreshCcw"
          @click="reports.reload()"
        />
      </template>
    </LayoutHeader>

    <div class="flex flex-wrap items-center gap-4 px-5 pb-2 pt-5">
      <DateRangePicker
        class="!w-56"
        :model-value="period ? parseDateRange(period) : []"
        variant="outline"
        :placeholder="__('Period')"
        :formatter="formatRange"
        @change="(v) => onPeriod(v)"
      >
        <template #prefix>
          <LucideCalendar class="mr-2 size-4 text-ink-gray-5" />
        </template>
      </DateRangePicker>
      <Link
        v-if="isAdmin() || isManager()"
        class="form-control w-48"
        variant="outline"
        :value="userFilter && getUser(userFilter).full_name"
        doctype="User"
        :filters="{
          name: ['in', users.data.crmUsers?.map((u) => u.name)],
          ignore_user_type: 1,
        }"
        :placeholder="__('Sales User')"
        :hideMe="true"
        @change="(v) => ((userFilter = v), reports.reload())"
      />
    </div>

    <div class="min-h-0 flex-1 overflow-y-auto px-5 pb-8">
      <p v-if="reports.loading" class="text-p-sm text-ink-gray-5">
        {{ __('Loading…') }}
      </p>
      <div v-else class="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <DashboardItem
          v-for="(item, index) in reports.data || []"
          :key="item.name"
          :index="index"
          :item="item"
          class="min-h-64 rounded-md border border-outline-gray-2 bg-surface-white p-3"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import DashboardItem from '@/components/Dashboard/DashboardItem.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import Link from '@/components/Controls/Link.vue'
import LucideRefreshCcw from '~icons/lucide/refresh-ccw'
import LucideCalendar from '~icons/lucide/calendar'
import { usersStore } from '@/stores/users'
import { getSettings } from '@/stores/settings'
import {
  getLastXDays,
  formatRange,
  parseDateRange,
} from '@/utils/dashboard'
import { createResource, DateRangePicker, usePageMeta } from 'frappe-ui'
import { ref } from 'vue'

const { brand } = getSettings()
const { getUser, isAdmin, isManager, users } = usersStore()

usePageMeta(() => ({
  title: __('Reports'),
  icon: brand?.favicon,
}))

const period = ref(getLastXDays())
const userFilter = ref(null)

function onPeriod(v) {
  if (!v) {
    period.value = getLastXDays()
  } else if (Array.isArray(v)) {
    period.value = v.join(',')
  } else {
    period.value = v
  }
  reports.reload()
}

const reports = createResource({
  url: 'crm.api.dashboard.get_reports',
  auto: true,
  makeParams() {
    const [from_date, to_date] = parseDateRange(period.value)
    return {
      from_date,
      to_date,
      user: userFilter.value || undefined,
    }
  },
})
</script>
