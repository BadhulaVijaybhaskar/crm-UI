<template>
  <div class="flex h-full min-h-0 flex-col overflow-hidden bg-[color:var(--crm-bg,#f3f6f8)]">
    <AstraConceptBanner
      :text="
        __(
          'Dashboard builder. Edit mode, chart tiles, Reset to default and Save exist today; resizing, custom KPIs, formulas and several saved dashboards per user or team are new.',
        )
      "
    />

    <AstraPageHeader
      :title="__('Reports')"
      :description="
        __(
          'Build dashboards from your CRM data. Each person or team can keep several.',
        )
      "
    >
      <span
        class="inline-flex h-6 items-center gap-1.5 rounded-md border border-dashed border-[color:var(--crm-border-strong,#d0d9e0)] px-2.5 text-[11.5px] font-medium text-[color:var(--crm-muted-fg,#5b6478)]"
        data-parity-mask="example-data"
      >
        <i
          class="block size-1.5 rounded-full bg-[color:var(--crm-warning,#a86a0b)]"
          aria-hidden="true"
        />
        {{ __('Example data') }}
      </span>
    </AstraPageHeader>

    <div
      class="flex h-11 shrink-0 items-center gap-0.5 border-b border-[color:var(--crm-border,#e1e7ec)] px-crm-page-x"
    >
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
        class="inline-flex h-[34px] items-center gap-1.5 rounded-lg px-3 text-[12.5px] font-medium"
        :class="
          tab === 'personal'
            ? 'border border-[color:var(--crm-border-strong,#d0d9e0)] bg-[color:var(--crm-card,#fff)] font-semibold text-[color:var(--crm-fg,#0b1324)]'
            : 'text-[color:var(--crm-muted-fg,#5b6478)]'
        "
        @click="tab = 'personal'"
      >
        {{ __('My dashboards') }}
        <em
          class="not-italic"
          :class="
            tab === 'personal'
              ? 'text-[color:var(--crm-primary,#0a7393)]'
              : 'text-[color:var(--crm-faint,#8a94a6)]'
          "
          >{{ lists.personal.length }}</em
        >
      </button>
      <button
        type="button"
        class="inline-flex h-[34px] items-center gap-1.5 rounded-lg px-3 text-[12.5px] font-medium"
        :class="
          tab === 'team'
            ? 'bg-[color:var(--crm-muted,#f6f8fa)] font-semibold text-[color:var(--crm-fg,#0b1324)]'
            : 'text-[color:var(--crm-muted-fg,#5b6478)]'
        "
        @click="tab = 'team'"
      >
        {{ __('Team') }}
        <em class="not-italic text-[color:var(--crm-faint,#8a94a6)]">{{
          lists.team.length
        }}</em>
      </button>
      <button
        type="button"
        class="inline-flex h-[34px] items-center gap-1 px-2 text-[12.5px] font-semibold text-[color:var(--crm-primary,#0a7393)]"
        @click="createDashboard"
      >
        <LucidePlus class="size-3.5" aria-hidden="true" />
        {{ __('New dashboard') }}
      </button>

      <div
        class="ml-auto flex flex-wrap items-center gap-3.5 text-[12px] text-[color:var(--crm-muted-fg,#5b6478)]"
      >
        <span v-if="current?.is_default">
          {{ __('Default') }}
          <template v-if="current.shared_role">
            · {{ __('shared with') }} {{ current.shared_role }}
          </template>
        </span>
        <Dropdown
          :options="periodOptions"
          :button="{
            label: `${__('Date')} ${periodLabel}`,
            variant: 'outline',
            iconRight: 'lucide-chevron-down',
          }"
        />
        <Dropdown
          v-if="isAdmin() || isManager()"
          :options="salesUserOptions"
          :button="{
            label: `${__('Sales user')} ${salesUserLabel}`,
            variant: 'outline',
            iconRight: 'lucide-chevron-down',
          }"
        />
        <Button
          v-if="!editing"
          size="sm"
          :label="__('Edit')"
          :iconLeft="LucidePenLine"
          @click="startEdit"
        />
      </div>
    </div>

    <div
      v-if="editing"
      class="mx-crm-page-x mt-0 flex h-[46px] shrink-0 items-center gap-2.5 rounded-lg border border-[color:var(--crm-primary,#0a7393)] bg-[color:var(--crm-primary-soft,#e4f2f6)] px-3"
    >
      <i
        class="block size-1.5 shrink-0 rounded-full bg-[color:var(--crm-success,#0f8a5f)]"
        aria-hidden="true"
      />
      <span
        class="shrink-0 text-[12.5px] font-semibold text-[color:var(--crm-primary,#0a7393)]"
      >
        {{ __('Editing') }}
      </span>
      <span class="min-w-0 truncate text-[12.5px] text-[color:var(--crm-muted-fg,#5b6478)]">
        <b class="font-semibold text-[color:var(--crm-fg,#0b1324)]">{{
          current?.title || __('Dashboard')
        }}</b>
        {{
          __(
            'Drag a tile to move it, drag a corner to resize. Tiles snap to a 12-column grid.',
          )
        }}
      </span>
      <span class="flex-1" />
      <Button
        size="sm"
        :label="__('Add tile')"
        iconLeft="lucide-plus"
        @click="showAddTile = true"
      />
      <Button
        size="sm"
        variant="ghost"
        :label="__('Reset to default')"
        @click="resetLayout"
      />
      <Button size="sm" :label="__('Cancel')" @click="cancelEdit" />
      <AstraButton
        size="sm"
        variant="primary"
        :loading="saving"
        @click="saveLayout"
      >
        {{ __('Save dashboard') }}
      </AstraButton>
    </div>

    <ReportGrid
      v-model="tiles"
      :editing="editing"
      :selected-id="selectedId"
      :dragging-id="draggingId"
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
import AstraButton from '@/components/astra/AstraButton.vue'
import AstraConceptBanner from '@/components/astra/AstraConceptBanner.vue'
import AstraPageHeader from '@/components/astra/AstraPageHeader.vue'
import LucidePenLine from '~icons/lucide/pen-line'
import LucidePlus from '~icons/lucide/plus'
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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const { brand } = getSettings()
const { isAdmin, isManager } = usersStore()
const route = useRoute()

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
/** Parity / edit-demo: tile id currently mid-drag (shows drop placeholder). */
const draggingId = ref(null)
const tab = ref('personal')
const period = ref('this_quarter')
const userFilter = ref('West team')
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

const salesUserLabel = computed(
  () => userFilter.value || current.value?.shared_role || __('West team'),
)

const salesUserOptions = computed(() => {
  const roles = [
    current.value?.shared_role,
    'West team',
    'All India',
  ].filter(Boolean)
  return [...new Set(roles)].map((label) => ({
    label,
    onClick: () => {
      userFilter.value = label
    },
  }))
})

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
  draggingId.value = null
  if (editing.value) applyEditSelection()
}

async function reloadDashboard() {
  if (current.value?.name) await selectDashboard(current.value.name)
}

function defaultSize(type) {
  if (type === 'kpi') return { w: 3, h: 1, minW: 2, minH: 1 }
  if (type === 'funnel') return { w: 4, h: 3, minW: 3, minH: 2 }
  if (type === 'table') return { w: 6, h: 2, minW: 3, minH: 2 }
  return { w: 8, h: 3, minW: 3, minH: 2 }
}

function normalizeTiles(layout) {
  return layout.map((t, idx) => {
    const id = t.id || t.layout?.i || `tile_${idx}`
    const defaults = defaultSize(t.type)
    return {
      ...t,
      id,
      layout: {
        x: t.layout?.x ?? (idx % 4) * 3,
        y: t.layout?.y ?? Math.floor(idx / 4),
        w: t.layout?.w ?? defaults.w,
        h: t.layout?.h ?? defaults.h,
        i: id,
        minW: defaults.minW,
        minH: defaults.minH,
      },
    }
  })
}

function applyEditSelection() {
  // Figma screen 17: Pipeline by stage selected; Won-value line tile mid-drag
  if (!selectedId.value) {
    const bar = tiles.value.find((t) => t.type === 'bar')
    if (bar) selectedId.value = bar.id
  }
  if (!draggingId.value) {
    const line =
      tiles.value.find((t) => t.config?.dragging) ||
      tiles.value.find((t) => t.type === 'line')
    if (line) draggingId.value = line.id
  }
}

function startEdit() {
  snapshot.value = JSON.parse(JSON.stringify(tiles.value))
  editing.value = true
  applyEditSelection()
}

function cancelEdit() {
  tiles.value = JSON.parse(JSON.stringify(snapshot.value))
  editing.value = false
  draggingId.value = null
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
  const size = defaultSize('kpi')
  const pos = nextPosition(size.w, size.h)
  tiles.value.push({
    id,
    type: 'kpi',
    title: config.title || __('KPI'),
    layout: { ...pos, i: id, minW: size.minW, minH: size.minH },
    config,
    data: null,
  })
  refreshTileData(tiles.value[tiles.value.length - 1])
}

function addChartTile(config) {
  const type = config.chart_type || 'bar'
  const id = `${type}_${Date.now()}`
  const size = defaultSize(type)
  const pos = nextPosition(size.w, size.h)
  tiles.value.push({
    id,
    type,
    title: config.title || __('Chart'),
    layout: { ...pos, i: id, minW: size.minW, minH: size.minH },
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
  copy.layout = {
    ...copy.layout,
    i: id,
    y: (copy.layout?.y || 0) + (copy.layout?.h || 2),
  }
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

/** Test-only convenience: ?parityModal=add|kpi|chart (or #parityModal=…) */
function applyParityModalQuery() {
  const fromQuery = String(route.query.parityModal || '')
  const hash = String(route.hash || '')
  const fromHash = hash.match(/parityModal=([a-z]+)/i)?.[1] || ''
  const modal = (fromQuery || fromHash).toLowerCase()
  if (!modal) return
  startEdit()
  // edit | add | kpi | chart — "edit" only enters edit mode (screen 17)
  if (modal === 'add') showAddTile.value = true
  else if (modal === 'kpi') showKpiBuilder.value = true
  else if (modal === 'chart') showChartBuilder.value = true
}

onMounted(() => {
  applyParityModalQuery()
})

// Tiles often arrive after onMounted startEdit — re-apply Figma selection/drag.
watch(
  () => tiles.value.map((t) => t.id).join(','),
  () => {
    if (editing.value) applyEditSelection()
  },
)

watch(period, () => reloadDashboard())
</script>
