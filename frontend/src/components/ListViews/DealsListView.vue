<template>
  <ListView
    class="astra-list-view"
    :class="$attrs.class"
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: (row) => ({
        name: 'Deal',
        params: { dealId: row.name },
        query: { view: route.query.view, viewType: route.params.viewType },
      }),
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
    @update:selections="onSelectionsChanged"
  >
    <ListHeader
      class="astra-list-header sm:mx-5 mx-3"
      @columnWidthUpdated="emit('columnWidthUpdated')"
    >
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        @columnWidthUpdated="(e) => onColumnWidthUpdated(e, column)"
      >
        <Button
          v-if="column.key == '_liked_by'"
          variant="ghost"
          class="!h-4"
          @click="() => emit('applyLikeFilter')"
        >
          <HeartIcon
            class="h-4 w-4"
            :class="isLikeFilterApplied ? 'fill-red-500 text-red-500' : ''"
          />
        </Button>
      </ListHeaderItem>
    </ListHeader>
    <ListRows
      v-slot="{ idx, column, item, row, isVisited }"
      :rows="rows"
      doctype="CRM Deal"
    >
      <ListRowItem :item="item" :align="column.align" class="overflow-hidden">
        <template #prefix>
          <div
            v-if="column.key === '_assign'"
            class="flex items-center truncate"
          >
            <MultipleAvatar
              :avatars="item"
              size="sm"
              :label-class="
                isVisited ? 'text-ink-gray-6' : 'font-medium text-ink-gray-9'
              "
              @click="
                (event) =>
                  emit('applyFilter', {
                    event,
                    idx,
                    column,
                    item,
                    firstColumn: columns[0],
                  })
              "
            />
          </div>
          <div v-else-if="column.key === 'status'" class="hidden" />
          <div v-else-if="column.key === 'organization'">
            <AstraAvatar
              v-if="item.label"
              :name="item.label"
              :src="item.logo"
              size="md"
              squared
            />
          </div>
          <div v-else-if="column.key === 'deal_owner'">
            <UserAvatar
              v-if="item.full_name"
              class="flex items-center"
              :user="item.name"
              size="sm"
            />
          </div>
          <div v-else-if="column.key === 'mobile_no' && item">
            <PhoneIcon class="h-4 w-4" />
          </div>
        </template>
        <template #default="{ label }">
          <div
            v-if="
              [
                'modified',
                'creation',
                'first_response_time',
                'first_responded_on',
                'response_by',
              ].includes(column.key)
            "
            class="truncate text-base"
            :class="
              isVisited ? 'text-ink-gray-6' : 'font-medium text-ink-gray-9'
            "
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            <Tooltip :text="item.label">
              <div>{{ item.timeAgo }}</div>
            </Tooltip>
          </div>
          <div
            v-else-if="column.key === 'status'"
            class="truncate text-base"
          >
            <AstraBadge
              v-if="item.label"
              :label="item.label"
              tone="mute"
              dot
              @click="
                (event) =>
                  emit('applyFilter', {
                    event,
                    idx,
                    column,
                    item,
                    firstColumn: columns[0],
                  })
              "
            />
          </div>
          <div
            v-else-if="column.key === 'sla_status'"
            class="truncate text-base"
          >
            <AstraBadge
              v-if="item.value"
              :label="item.value"
              :tone="slaTone(item.color)"
              @click="
                (event) =>
                  emit('applyFilter', {
                    event,
                    idx,
                    column,
                    item,
                    firstColumn: columns[0],
                  })
              "
            />
          </div>
          <div v-else-if="column.type === 'Check'">
            <FormControl
              type="checkbox"
              :modelValue="item"
              :disabled="true"
              class="text-ink-gray-9"
            />
          </div>
          <div v-else-if="column.key === '_liked_by'">
            <Button
              variant="ghost"
              @click.stop.prevent="
                () => emit('likeDoc', { name: row.name, liked: isLiked(item) })
              "
            >
              <HeartIcon
                class="h-4 w-4"
                :class="
                  isLiked(item)
                    ? isVisited
                      ? 'fill-red-400 text-red-400'
                      : 'fill-red-500 text-red-500'
                    : isVisited
                      ? 'text-ink-gray-6'
                      : 'text-ink-gray-9'
                "
              />
            </Button>
          </div>
          <RatingInput
            v-else-if="column.type === 'Rating'"
            :value="item"
            class="!opacity-100 flex-nowrap overflow-auto"
            :disabled="true"
            :max="column.options || 5"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          />
          <WebsiteLink
            v-else-if="column.key === 'website' && item?.url"
            variant="label"
            :url="item.url"
            :label="getLabel(label, column)"
          />
          <div
            v-else-if="label"
            class="truncate text-base"
            :class="
              isVisited ? 'text-ink-gray-6' : 'font-medium text-ink-gray-9'
            "
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            {{ getLabel(label, column) }}
          </div>
        </template>
        <template #suffix>
          <WebsiteLink
            v-if="column.key === 'website' && item?.url"
            variant="icon"
            :url="item.url"
          />
        </template>
      </ListRowItem>
    </ListRows>
  </ListView>
  <AstraBulkBar
    :count="selectedKeys.length"
    :actions="bulkBarActions"
    @clear="clearSelections"
  />
  <ListFooter
    v-if="pageLengthCount"
    v-model="pageLengthCount"
    class="border-t border-crm-border bg-crm-card sm:px-5 px-3 py-2 text-crm-meta text-crm-muted-fg"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
  <ListBulkActions ref="listBulkActionsRef" v-model="list" doctype="CRM Deal" />
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import RatingInput from '@/components/Controls/RatingInput.vue'
import ListBulkActions from '@/components/ListBulkActions.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import WebsiteLink from '@/components/ListViews/WebsiteLink.vue'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import AstraBadge from '@/components/astra/AstraBadge.vue'
import AstraBulkBar from '@/components/astra/AstraBulkBar.vue'
import { isTranslatable, formatDuration } from '@/utils'
import { canUseCrmCsvExport, crmCsvExportUrl } from '@/utils/csvExport'
import { Tooltip } from 'frappe-ui'
import {
  ListView,
  ListHeader,
  ListHeaderItem,
  ListRowItem,
  ListFooter,
} from 'frappe-ui/experimental'
import { sessionStore } from '@/stores/session'
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'

defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  options: {
    type: Object,
    default: () => ({
      selectable: true,
      showTooltip: true,
      resizeColumn: false,
      totalCount: 0,
      rowCount: 0,
    }),
  },
})

const emit = defineEmits([
  'loadMore',
  'updatePageCount',
  'columnWidthUpdated',
  'applyFilter',
  'applyLikeFilter',
  'likeDoc',
  'selectionsChanged',
])

const route = useRoute()

const pageLengthCount = defineModel({ type: Number })
const list = defineModel('list', { type: Object })

function onColumnWidthUpdated({ width, save }, column) {
  column.width = width
  if (save) emit('columnWidthUpdated', column)
}

function getLabel(label, column) {
  if (column.type === 'Duration') return formatDuration(label)
  if (column.options && isTranslatable(column.options)) return __(label)
  return label
}

const isLikeFilterApplied = computed(() => {
  return list.value.params?.filters?._liked_by ? true : false
})

const { user } = sessionStore()

function isLiked(item) {
  if (item) {
    let likedByMe = JSON.parse(item)
    return likedByMe.includes(user)
  }
}

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const listBulkActionsRef = ref(null)
const selectedKeys = ref([])

function onSelectionsChanged(selections) {
  const keys =
    selections instanceof Set ? [...selections] : [...(selections || [])]
  selectedKeys.value = keys
  emit('selectionsChanged', selections)
}

function clearSelections() {
  selectedKeys.value = []
  emit('selectionsChanged', new Set())
}

function slaTone(color) {
  if (color === 'red') return 'bad'
  if (color === 'green') return 'ok'
  if (color === 'amber') return 'warn'
  return 'mute'
}

const bulkBarActions = computed(() => {
  const selections = new Set(selectedKeys.value)
  const unselectAll = () => clearSelections()
  const all =
    listBulkActionsRef.value?.bulkActions(selections, unselectAll) || []
  const allowed = []
  for (const action of all) {
    const label = String(action.label || '')
    if (label === __('Assign To') || label === 'Assign To') {
      allowed.push({ label: __('Assign'), onClick: action.onClick })
    } else if (label === __('Edit') || label === 'Edit') {
      allowed.push({ label: __('Set status'), onClick: action.onClick })
    } else if (label === __('Delete') || label === 'Delete') {
      allowed.push({ label: __('Delete'), onClick: action.onClick })
    }
  }
  if (canUseCrmCsvExport('CRM Deal') && selectedKeys.value.length) {
    allowed.push({
      label: __('Export'),
      onClick: () => {
        const fields = (list.value?.data?.columns || []).map((c) => c.key)
        window.location.href = crmCsvExportUrl({
          doctype: 'CRM Deal',
          fields,
          filters: {
            ...(list.value?.params?.filters || {}),
            name: ['in', selectedKeys.value],
          },
          orderBy: list.value?.params?.order_by,
          limit: selectedKeys.value.length,
          title: 'CRM Deal',
        })
      },
    })
  }
  return allowed
})

defineExpose({
  customListActions: computed(
    () => listBulkActionsRef.value?.customListActions,
  ),
})
</script>

<style scoped>
.astra-list-view :deep(thead th) {
  height: 34px;
  padding: 0 10px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--crm-muted-fg);
  background: var(--crm-muted);
  border-bottom: 1px solid var(--crm-border);
}
.astra-list-view :deep(tbody td) {
  height: 44px;
  padding: 0 10px;
  font-size: 12.5px;
  border-bottom: 1px solid var(--crm-border);
  white-space: nowrap;
}
.astra-list-view :deep(tbody tr:hover) {
  background: var(--crm-row-hover);
}
.astra-list-view :deep(input[type='checkbox']) {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  accent-color: var(--crm-primary);
}
.astra-list-view :deep(input[type='checkbox']:focus-visible) {
  box-shadow: var(--crm-focus);
  outline: none;
}
</style>
