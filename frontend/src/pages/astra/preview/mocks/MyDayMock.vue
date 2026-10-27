<template>
  <div class="flex flex-col gap-4">
    <header>
      <h1 class="text-[2rem] font-bold tracking-tight text-[var(--astra-text)]">
        Good morning, Vijay
      </h1>
      <p class="astra-muted mt-1 text-sm">Wed, 28 Oct</p>
    </header>
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-12">
      <AstraCard class="xl:col-span-3 xl:row-span-2" title="Today">
        <ul class="flex flex-col gap-2">
          <li v-for="t in tasks" :key="t" class="flex items-start gap-2.5 text-sm font-medium">
            <span class="mt-0.5 size-4 rounded-[4px] border border-[var(--astra-border)]" />
            {{ t }}
          </li>
        </ul>
      </AstraCard>
      <AstraCard class="xl:col-span-3" title="Target">
        <AstraEmptyState
          title="No sales target configured"
          body="A monthly target gauge will appear here when a sales target field is available on your CRM settings."
        />
      </AstraCard>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3 xl:col-span-6">
        <AstraCard v-for="k in kpis" :key="k.label" class="!p-4">
          <p class="astra-label">{{ k.label }}</p>
          <p class="astra-value mt-1">{{ k.value }}</p>
          <div class="mt-3 flex items-end justify-between">
            <AstraSparkline :values="k.spark" />
            <span class="astra-badge astra-badge--success">{{ k.delta }}</span>
          </div>
        </AstraCard>
      </div>
      <AstraCard class="xl:col-span-5" title="Upcoming calls">
        <ul>
          <li v-for="c in calls" :key="c.name" class="astra-row">
            <AstraAvatar :name="c.name" :seed="c.name" size="sm" />
            <div class="min-w-0 flex-1">
              <p class="text-sm font-semibold">{{ c.time }} · {{ c.name }}</p>
            </div>
            <button type="button" class="astra-btn astra-btn--primary">Call</button>
          </li>
        </ul>
      </AstraCard>
      <AstraCard class="xl:col-span-7" title="Hot leads">
        <ul>
          <li v-for="l in leads" :key="l.name" class="astra-row">
            <AstraAvatar :name="l.name" :seed="l.name" size="sm" />
            <div class="min-w-0 flex-1 text-sm font-semibold">{{ l.name }}</div>
            <span class="font-bold tabular-nums">{{ l.score }}</span>
            <button type="button" class="astra-btn astra-btn--outline">Open</button>
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
