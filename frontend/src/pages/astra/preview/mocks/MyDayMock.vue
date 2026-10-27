<template>
  <div class="flex min-w-0 flex-col gap-4 overflow-x-hidden">
    <header class="min-w-0">
      <h1
        class="truncate text-[1.75rem] font-bold tracking-tight text-[var(--astra-text)] sm:text-[2rem]"
      >
        Good morning, Vijay
      </h1>
      <p class="astra-muted mt-1 text-sm">Wed, 28 Oct</p>
    </header>
    <div class="grid min-w-0 grid-cols-1 gap-4 lg:grid-cols-12">
      <AstraCard class="min-w-0 lg:col-span-3" title="Today">
        <ul class="flex flex-col gap-2">
          <li
            v-for="t in tasks"
            :key="t"
            class="flex min-w-0 items-start gap-2.5 text-sm font-medium"
          >
            <span
              class="mt-0.5 size-4 shrink-0 rounded-[4px] border border-[var(--astra-border)]"
            />
            <span class="min-w-0 truncate">{{ t }}</span>
          </li>
        </ul>
      </AstraCard>
      <AstraCard class="min-w-0 lg:col-span-3" title="Target">
        <AstraEmptyState
          title="No sales target configured"
          body="A monthly target gauge will appear here when a sales target field is available on your CRM settings."
        />
      </AstraCard>
      <div class="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-3 lg:col-span-6">
        <AstraCard v-for="k in kpis" :key="k.label" class="min-w-0 !p-4">
          <p class="astra-label">{{ k.label }}</p>
          <p class="astra-value mt-1 truncate">{{ k.value }}</p>
          <div class="mt-3 flex min-w-0 items-end justify-between gap-2">
            <div class="min-w-0 flex-1">
              <AstraSparkline :values="k.spark" />
            </div>
            <span class="astra-badge astra-badge--success shrink-0">{{
              k.delta
            }}</span>
          </div>
        </AstraCard>
      </div>
      <AstraCard class="min-w-0 lg:col-span-5" title="Upcoming calls">
        <ul>
          <li v-for="c in calls" :key="c.name" class="astra-row min-w-0">
            <AstraAvatar :name="c.name" :seed="c.name" size="sm" />
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold">
                {{ c.time }} · {{ c.name }}
              </p>
            </div>
            <button type="button" class="astra-btn astra-btn--outline shrink-0">
              Open
            </button>
          </li>
        </ul>
      </AstraCard>
      <AstraCard class="min-w-0 lg:col-span-7" title="Hot leads">
        <ul>
          <li v-for="l in leads" :key="l.name" class="astra-row min-w-0">
            <AstraAvatar :name="l.name" :seed="l.name" size="sm" />
            <div class="min-w-0 flex-1 truncate text-sm font-semibold">
              {{ l.name }}
            </div>
            <span class="shrink-0 font-bold tabular-nums">{{ l.score }}</span>
            <button type="button" class="astra-btn astra-btn--outline shrink-0">
              Open
            </button>
          </li>
        </ul>
      </AstraCard>
    </div>
  </div>
</template>

<script setup>
import AstraCard from '@/components/astra/AstraCard.vue'
import AstraEmptyState from '@/components/astra/AstraEmptyState.vue'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import AstraSparkline from '@/components/astra/AstraSparkline.vue'

const tasks = ['Call Infosys', 'Send quote to HDFC', 'Demo with Zomato', 'Renew Wipro']
const kpis = [
  { label: 'Pipeline', value: '₹3.2Cr', delta: '+12%', spark: [1, 2, 2.4, 3, 2.8, 3.2] },
  { label: 'Won', value: '₹45L', delta: '+8%', spark: [1, 1.2, 1.8, 2.1, 2.4, 2.6] },
  { label: 'Calls', value: '38', delta: '+5%', spark: [4, 8, 12, 18, 28, 38] },
]
const calls = [
  { time: '11:30', name: 'Rahul Mehta' },
  { time: '14:00', name: 'Priya Nair' },
  { time: '16:15', name: 'Ankit Rao' },
]
const leads = [
  { name: 'Infosys', score: 92 },
  { name: 'HDFC', score: 88 },
  { name: 'Zomato', score: 81 },
]
</script>
