<template>
  <div class="flex h-full min-h-0 flex-col overflow-hidden bg-crm-bg">
    <AstraPageHeader
      :title="__('Call logs')"
      :description="__('Calls logged by Astra Connect or by hand.')"
    >
      <template #actions>
        <CustomActions
          v-if="callLogsListView?.customListActions"
          :actions="callLogsListView.customListActions"
        />
        <AstraButton
          variant="secondary"
          :label="__('Log a call')"
          @click="createCallLog"
        />
      </template>
    </AstraPageHeader>

    <ViewControls
      ref="viewControls"
      v-model="callLogs"
      v-model:loadMore="loadMore"
      v-model:resizeColumn="triggerResize"
      v-model:updatedPageCount="updatedPageCount"
      doctype="CRM Call Log"
    />
    <CallLogsListView
      v-if="callLogs.data && rows.length"
      ref="callLogsListView"
      v-model="callLogs.data.page_length_count"
      v-model:list="callLogs"
      :rows="rows"
      :columns="columns"
      :options="{
        showTooltip: false,
        resizeColumn: true,
        rowCount: callLogs.data.row_count,
        totalCount: callLogs.data.total_count,
      }"
      @showCallLog="showCallLog"
      @loadMore="() => loadMore++"
      @columnWidthUpdated="() => triggerResize++"
      @updatePageCount="(count) => (updatedPageCount = count)"
      @applyFilter="(data) => viewControls.applyFilter(data)"
      @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
      @likeDoc="(data) => viewControls.likeDoc(data)"
      @selectionsChanged="
        (selections) => viewControls.updateSelections(selections)
      "
    />
    <AstraEmptyState
      v-else-if="callLogs.data && !rows.length"
      :title="__('No call logs yet')"
      :body="
        __(
          'Calls made through Astra Connect are logged here, along with calls you log by hand on a lead or deal.',
        )
      "
    >
      <AstraButton
        variant="primary"
        :label="__('Log a call')"
        @click="createCallLog()"
      />
    </AstraEmptyState>
    <CallLogDetailModal
      v-model="showCallLogDetailModal"
      v-model:callLog="callLog"
    />
  </div>
</template>

<script setup>
import CustomActions from '@/components/CustomActions.vue'
import ViewControls from '@/components/ViewControls.vue'
import CallLogsListView from '@/components/ListViews/CallLogsListView.vue'
import CallLogDetailModal from '@/components/Modals/CallLogDetailModal.vue'
import { AstraButton, AstraEmptyState, AstraPageHeader } from '@/components/astra'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { getCallLogDetail } from '@/utils/callLog'
import { useTelemetry } from '@framework/ui/telemetry'
import { createResource, usePageMeta } from 'frappe-ui'
import { computed, ref, onMounted } from 'vue'
import { getSettings } from '@/stores/settings'
import { ASTRA_FAVICON } from '@/assets/brand'

const { brand } = getSettings()
const callLogsListView = ref(null)

const callLogs = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !callLogs.value?.data?.data ||
    !['list', 'group_by'].includes(callLogs.value.data.view_type)
  )
    return []
  return callLogs.value?.data.data.map((callLog) => {
    let _rows = {}
    callLogs.value?.data.rows.forEach((row) => {
      _rows[row] = getCallLogDetail(row, callLog, callLogs.value?.data.columns)
    })
    return _rows
  })
})

const columns = computed(() => {
  let _columns = callLogs.value?.data?.columns || []

  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})

const showCallLogDetailModal = ref(false)
const callLog = ref({})

function showCallLog(name) {
  showCallLogDetailModal.value = true
  callLog.value = createResource({
    url: 'crm.fcrm.doctype.crm_call_log.crm_call_log.get_call_log',
    params: { name },
    cache: ['call_log', name],
    auto: true,
  })
}

const { showModal } = useDoctypeModal()
const { capture } = useTelemetry()

function createCallLog() {
  showModal({
    doctype: 'CRM Call Log',
    title: 'Call Log',
    callbacks: {
      afterInsert: () => {
        capture('call_log_created')
        callLogs.value.reload()
      },
    },
  })
}

const openCallLogFromURL = () => {
  const searchParams = new URLSearchParams(window.location.search)
  const callLogName = searchParams.get('open')

  if (callLogName) {
    showCallLog(callLogName)
    searchParams.delete('open')
    window.history.replaceState(null, '', window.location.pathname)
  }
}

onMounted(() => {
  openCallLogFromURL()
})

usePageMeta(() => ({
  title: __('Call logs'),
  icon: brand?.favicon || ASTRA_FAVICON,
}))
</script>
