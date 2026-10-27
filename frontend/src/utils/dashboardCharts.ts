// Chart resolvers (CRM's and contributed apps') return the experimental config shape; these map it to frappe-ui/charts props.
import type {
  BarChartProps,
  ChartValueAxisOptions,
  DonutChartProps,
  NumberCardProps,
  SeriesStyle,
  TimeGrain,
} from 'frappe-ui/charts'

type Row = Record<string, unknown>

interface ValueAxisConfig {
  title?: string
  yMin?: number
  yMax?: number
  echartOptions?: Row
}

interface SeriesConfig {
  name: string
  type: 'bar' | 'line' | 'area'
  color?: string
  axis?: 'y' | 'y2'
  showDataLabels?: boolean
  showDataPoints?: boolean
  lineType?: 'solid' | 'dashed' | 'dotted'
  stackName?: string
  echartOptions?: Row
}

export interface AxisChartConfig {
  data?: Row[]
  title?: string
  subtitle?: string
  colors?: string[]
  xAxis?: {
    key: string
    type?: 'category' | 'time' | 'value'
    timeGrain?: TimeGrain
    title?: string
    echartOptions?: Row
  }
  yAxis?: ValueAxisConfig
  y2Axis?: ValueAxisConfig
  swapXY?: boolean
  stacked?: boolean
  series?: SeriesConfig[]
  echartOptions?: Row
}

export interface DonutChartConfig {
  data?: Row[]
  title?: string
  subtitle?: string
  colors?: string[]
  categoryColumn: string
  valueColumn: string
  maxSliceCount?: number
  showInlineLabels?: boolean
  echartOptions?: Row
}

export type NumberChartConfig = NumberCardProps & { tooltip?: string }

export type DashboardChartConfig = Partial<
  NumberChartConfig & AxisChartConfig & DonutChartConfig
>

export type AxisChartKind = 'line' | 'area' | 'bar'

/** Astra brand chart palette (replaces upstream default blues/greens/purples). */
export const ASTRA_CHART_PALETTE = [
  '#145CF6',
  '#09B5A4',
  '#0E8BD6',
  '#7FA6FF',
] as const

function withAstraPalette(colors?: string[]) {
  return colors?.length ? colors : [...ASTRA_CHART_PALETTE]
}

function hideEmptyDelta<T extends Record<string, unknown>>(props: T): T {
  const delta = props.delta ?? props.change ?? props.percentageChange
  if (delta === 0 || delta === '0' || delta === '0%' || delta == null) {
    const next = { ...props }
    delete next.delta
    delete next.change
    delete next.percentageChange
    delete next.deltaLabel
    return next
  }
  return props
}

export function toNumberCardProps(config: NumberChartConfig): NumberCardProps {
  const props = { ...config } as Record<string, unknown>
  delete props.tooltip
  return hideEmptyDelta(props) as NumberCardProps
}

export function toDonutChartProps(config: DonutChartConfig): DonutChartProps {
  return {
    title: config.title,
    subtitle: config.subtitle,
    data: config.data || [],
    category: config.categoryColumn,
    value: config.valueColumn,
    maxSlices: config.maxSliceCount,
    showDataLabels: config.showInlineLabels,
    palette: withAstraPalette(config.colors),
    echartOptions: config.echartOptions,
  }
}

export function getAxisChartKind(config: AxisChartConfig): AxisChartKind {
  const types = new Set((config.series || []).map((s) => s.type))
  if (types.size === 1 && types.has('line')) return 'line'
  if (types.size === 1 && types.has('area')) return 'area'
  return 'bar'
}

function toValueAxis(
  axis?: ValueAxisConfig,
): ChartValueAxisOptions | undefined {
  return (
    axis && {
      title: axis.title,
      min: axis.yMin,
      max: axis.yMax,
      echartOptions: axis.echartOptions,
    }
  )
}

export function toAxisChartProps(config: AxisChartConfig): BarChartProps {
  const series = config.series || []
  const seriesConfig: Record<string, SeriesStyle> = {}
  const colors = withAstraPalette(config.colors)
  series.forEach((s, i) => {
    seriesConfig[s.name] = {
      type: s.type,
      color: s.color || colors[i % colors.length],
      showDataLabels: s.showDataLabels,
      showDataPoints: s.showDataPoints,
      dashed: s.lineType === 'dashed' || s.lineType === 'dotted' || undefined,
      stackName: s.stackName,
      echartOptions: s.echartOptions,
    }
  })

  const y2 = series.filter((s) => s.axis === 'y2').map((s) => s.name)

  return {
    title: config.title,
    subtitle: config.subtitle,
    data: config.data || [],
    x: config.xAxis?.key as string,
    y: series.filter((s) => s.axis !== 'y2').map((s) => s.name),
    y2: y2.length ? y2 : undefined,
    seriesConfig,
    stacked: config.stacked,
    xAxis: {
      title: config.xAxis?.title,
      type: config.xAxis?.type,
      timeGrain: config.xAxis?.timeGrain,
      echartOptions: config.xAxis?.echartOptions,
    },
    yAxis: toValueAxis(config.yAxis),
    y2Axis: toValueAxis(config.y2Axis),
    echartOptions: config.echartOptions,
    ...(getAxisChartKind(config) === 'bar' && { horizontal: config.swapXY }),
  }
}
