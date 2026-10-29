<template>
  <TasksBoard v-if="$route.params.viewType === 'kanban'" />
  <TaskQueue v-else @create="createTask" />
</template>

<script setup>
import { usePageMeta } from 'frappe-ui'
import TaskQueue from '@/components/Tasks/TaskQueue.vue'
import TasksBoard from '@/pages/TasksBoard.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { getSettings } from '@/stores/settings'
import { ASTRA_FAVICON } from '@/assets/brand'

const { brand } = getSettings()
const { showModal } = useDoctypeModal()

function createTask() {
  showModal({
    doctype: 'CRM Task',
    title: 'Task',
    defaults: { status: 'Backlog', priority: 'Low' },
  })
}

usePageMeta(() => ({
  title: __('Tasks'),
  icon: brand?.favicon || ASTRA_FAVICON,
}))
</script>
