<template>
  <div class="flex h-full min-h-0 flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <div>
          <ViewBreadcrumbs routeName="Reports" />
          <p class="mt-0.5 text-[12.5px] text-[color:var(--crm-muted-fg,#64748b)]">
            {{
              __(
                'Build dashboards from your CRM data. Each person or team can keep several.',
              )
            }}
          </p>
        </div>
      </template>
      <template #right-header>
        <Dropdown
          :options="periodOptions"
          :button="{
            label: periodLabel,
            variant: 'outline',
            iconLeft: 'lucide-calendar',
            iconRight: 'lucide-chevron-down',
          }"
        />
        <Link
          v-if="isAdmin() || isManager()"
          class="form-control w-44"
          variant="outline"
          :value="userFilter && getUser(userFilter).full_name"
          doctype="User"
          :filters="{
            name: ['in', users.data.crmUsers?.map((u) => u.name)],
            ignore_user_type: 1,
          }"
          :placeholder="__('Sales user')"
          :hideMe="true"
          @change="(v) => ((userFilter = v), reloadDashboard())"
        />
        <Button
          v-if="!editing"
          :label="__('Edit')"
          :iconLeft="LucidePenLine"
          @click="startEdit"
        />
      </template>
    </LayoutHeader>

    <div class="flex flex-wrap items-center gap-2 px-5 pb-2 pt-3">
      <Dropdown
        :options="dashboardMenuOptions"
        :button="{
          label: current?.title || __('Dashboards'),
          variant: 'outline',
          iconRight: 'lucide-chevron-down',
        }"
      />
      <button
        type="button"
        class="rounded-md px-2.5 py-1.5 text-[12.5px]"
        :class="tab === 'personal' ? 'bg-[color:var(--crm-muted,#f1f5f9)] font-semibold' : 'text-[color:var(--crm-muted-fg,#64748b)]'"
        @click="tab = 'personal'"
      >
        {{ __('My dashboards') }} ({{ lists.personal.length }})
      </button>
      <button
        type="button"
        class="rounded-md px-2.5 py-1.5 text-[12.5px]"
        :class="tab === 'team' ? 'bg-[color:var(--crm-muted,#f1f5f9)] font-semibold' : 'text-[color:var(--crm-muted-fg,#64748b)]'"
        @click="tab = 'team'"
      >
        {{ __('Team') }} ({{ lists.team.length }})
      </button>
      <Button :label="__('New dashboard')" iconLeft="lucide-plus" @click="createDashboard" />
      <span
        v-if="current?.is_default"
        class="text-[11.5px] text-[color:var(--crm-muted-fg,#64748b)]"
      >
        {{ __('Default') }}
        <template v-if="current.shared_role">
          · {{ __('shared with') }} {{ current.shared_role }}
        </template>
      </span>
    </div>

    <div
      v-if="editing"
      class="mx-5 mb-2 flex flex-wrap items-center gap-2 rounded-md bg-[color:var(--crm-primary-soft,#e6f4f8)] px-3 py-2"
    >
      <span
        class="inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-[color:var(--crm-fg,#0f172a)]"
      >
        <span class="size-1.5 rounded-full bg-[color:var(--crm-success,#16a34a)]" />
        {{ __('Editing') }}: {{ current?.title }}
      </span>
      <span class="text-[12px] text-[color:var(--crm-muted-fg,#64748b)]">
        {{
          __(
            'Drag a tile to move it, drag a corner to resize. Tiles snap to a 12-column grid.',
          )
        }}
      </span>
      <div class="ml-auto flex flex-wrap gap-2">
        <Button :label="__('Add tile')" iconLeft="lucide-plus" @click="showAddTile = true" />
        <Button :label="__('Reset to default')" @click="resetLayout" />
        <Button :label="__('Cancel')" @click="cancelEdit" />
        <Button
          variant="solid"
          :label="__('Save dashboard')"
          :loading="saving"
          @click="saveLayout"
        />
      </div>
    </div>

    <ReportGrid
      v-model="tiles"
      :editing="editing"
      :selected-id="selectedId"
      @select="(t) => (selectedId = t.id)"
      @edit="openEditTile"
      @duplicate="duplicateTile"
      @add="showAddTile = true"
    />

    <AddTileModal
      v-model="showAddTile"
      :dashboard-title="current?.title || ''"
      @continue="onTileTypeChosen"
      @template="addFromTemplate"
    />
    <KpiBuilderModal
      v-model="showKpiBuilder"
      :meta="meta"
      :initial="editingTileConfig"
      @save="addKpiTile"
    />
    <ChartBuilderModal
      v-model="showChartBuilder"
      :meta="meta"
      :initial-type="pendingChartType"
      :initial="editingTileConfig"
      @save="addChartTile"
    />
  </div>
</template>

<script setup>
import AddTileModal from '@/components/reports/AddTileModal.vue'
import ChartBuilderModal from '@/components/reports/ChartBuilderModal.vue'
import KpiBuilderModal from '@/components/reports/KpiBuilderModal.vue'
import ReportGrid from '@/components/reports/ReportGrid.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import Link from '@/components/Controls/Link.vue'
import LucidePenLine from '~icons/lucide/pen-line'
import { usersStore } from '@/stores/users'
import { getSettings } from '@/stores/settings'
import {
  Button,
  Dropdown,
  call,
  createResource,
  toast,
  usePageMeta,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const { brand } = getSettings()
const { getUser, isAdmin, isManager, users } = usersStore()

usePageMeta(() => ({
  title: __('Reports'),
  icon: brand?.favicon,
}))

const editing = ref(false)
const saving = ref(false)
const showAddTile = ref(false)
const showKpiBuilder = ref(false)
const showChartBuilder = ref(false)
const pendingChartType = ref('bar')
const editingTileConfig = ref(null)
const selectedId = ref(null)
const tab = ref('personal')
const period = ref('this_quarter')
const userFilter = ref(null)
const tiles = ref([])
const snapshot = ref([])
const current = ref(null)
const lists = reactive({ personal: [], team: [] })
const meta = ref({ modules: [], fields_by_doctype: {} })

const periodLabel = computed(() => {
  const map = {
    this_quarter: __('This quarter'),
    this_month: __('This month'),
    this_year: __('This year'),
    last_30_days: __('Last 30 days'),
  }
  return map[period.value] || period.value
})

const periodOptions = computed(() =>
  ['this_quarter', 'this_month', 'this_year', 'last_30_days'].map((value) => ({
    label: periodLabelFor(value),
    onClick: () => {
      period.value = value
      reloadDashboard()
    },
  })),
)

function periodLabelFor(value) {
  return (
    {
      this_quarter: __('This quarter'),
      this_month: __('This month'),
      this_year: __('This year'),
      last_30_days: __('Last 30 days'),
    }[value] || value
  )
}

const dashboardMenuOptions = computed(() => {
  const source = tab.value === 'team' ? lists.team : lists.personal
  return source.map((d) => ({
    label: d.title + (d.is_default ? ` (${__('default')})` : ''),
    onClick: () => selectDashboard(d.name),
  }))
})

const dashboardsResource = createResource({
  url: 'crm.api.reports.list_dashboards',
  auto: true,
  onSuccess(data) {
    lists.personal = data.personal || []
    lists.team = data.team || []
    if (!current.value) {
      const def =
        [...lists.personal, ...lists.team].find((d) => d.is_default) ||
        lists.personal[0] ||
        lists.team[0]
      if (def) selectDashboard(def.name)
    }
  },
})

createResource({
  url: 'crm.api.reports.get_builder_meta',
  auto: true,
  onSuccess(data) {
    meta.value = data || { modules: [], fields_by_doctype: {} }
  },
})

async function selectDashboard(name) {
  const data = await call('crm.api.reports.get_dashboard', {
    name,
    period: period.value,
  })
  current.value = data
  tiles.value = normalizeTiles(data.layout || [])
  selectedId.value = null
}

async function reloadDashboard() {
  if (current.value?.name) await selectDashboard(current.value.name)
}

function normalizeTiles(layout) {
  return layout.map((t, idx) => {
    const id = t.id || t.layout?.i || `tile_${idx}`
    return {
      ...t,
      id,
      layout: {
        x: t.layout?.x ?? (idx % 4) * 3,
        y: t.layout?.y ?? Math.floor(idx / 4) * 2,
        w: t.layout?.w ?? (t.type === 'kpi' ? 3 : 6),
        h: t.layout?.h ?? (t.type === 'kpi' ? 2 : 4),
        i: id,
        minW: 2,
        minH: 2,
      },
    }
  })
}

function startEdit() {
  snapshot.value = JSON.parse(JSON.stringify(tiles.value))
  editing.value = true
}

function cancelEdit() {
  tiles.value = JSON.parse(JSON.stringify(snapshot.value))
  editing.value = false
}

async function saveLayout() {
  if (!current.value?.name) return
  saving.value = true
  try {
    await call('crm.api.reports.save_dashboard_layout', {
      name: current.value.name,
      layout: JSON.stringify(tiles.value),
    })
    editing.value = false
    toast.success(__('Dashboard saved'))
    await reloadDashboard()
  } finally {
    saving.value = false
  }
}

async function createDashboard() {
  const title = __('Untitled dashboard')
  const type = tab.value === 'team' ? 'Team' : 'Personal'
  const created = await call('crm.api.reports.create_dashboard', {
    title,
    dashboard_type: type,
    shared_role: type === 'Team' ? 'Sales User' : undefined,
  })
  await dashboardsResource.reload()
  await selectDashboard(created.name)
  startEdit()
}

async function resetLayout() {
  tiles.value = []
}

function onTileTypeChosen(type) {
  showAddTile.value = false
  editingTileConfig.value = null
  if (type === 'kpi') {
    showKpiBuilder.value = true
  } else {
    pendingChartType.value = type
    showChartBuilder.value = true
  }
}

function addFromTemplate(tpl) {
  showAddTile.value = false
  if (tpl.type === 'kpi') {
    addKpiTile({ title: tpl.title, ...tpl.config })
  } else {
    addChartTile({ title: tpl.title, chart_type: tpl.type, ...tpl.config })
  }
}

function nextPosition(w, h) {
  const maxY = tiles.value.reduce(
    (m, t) => Math.max(m, (t.layout?.y || 0) + (t.layout?.h || 0)),
    0,
  )
  return { x: 0, y: maxY, w, h }
}

function addKpiTile(config) {
  const id = `kpi_${Date.now()}`
  const pos = nextPosition(3, 2)
  tiles.value.push({
    id,
    type: 'kpi',
    title: config.title || __('KPI'),
    layout: { ...pos, i: id, minW: 2, minH: 2 },
    config,
    data: null,
  })
  refreshTileData(tiles.value[tiles.value.length - 1])
}

function addChartTile(config) {
  const type = config.chart_type || 'bar'
  const id = `${type}_${Date.now()}`
  const pos = nextPosition(type === 'table' ? 6 : 8, 4)
  tiles.value.push({
    id,
    type,
    title: config.title || __('Chart'),
    layout: { ...pos, i: id, minW: 3, minH: 3 },
    config,
    data: null,
  })
  refreshTileData(tiles.value[tiles.value.length - 1])
}

function openEditTile(tile) {
  editingTileConfig.value = { ...(tile.config || {}), title: tile.title }
  if (tile.type === 'kpi') showKpiBuilder.value = true
  else {
    pendingChartType.value = tile.type
    showChartBuilder.value = true
  }
}

function duplicateTile(tile) {
  const copy = JSON.parse(JSON.stringify(tile))
  const id = `${tile.type}_${Date.now()}`
  copy.id = id
  copy.layout = { ...copy.layout, i: id, y: (copy.layout?.y || 0) + (copy.layout?.h || 2) }
  tiles.value.push(copy)
}

async function refreshTileData(tile) {
  try {
    if (tile.type === 'kpi') {
      tile.data = await call('crm.api.reports.evaluate_kpi', {
        config: JSON.stringify(tile.config),
        period: period.value,
      })
    } else {
      tile.data = await call('crm.api.reports.evaluate_chart', {
        config: JSON.stringify({ ...tile.config, chart_type: tile.type }),
        period: period.value,
      })
    }
  } catch (e) {
    tile.data = null
    tile.error = e.message
  }
}

watch(period, () => reloadDashboard())
</script>
