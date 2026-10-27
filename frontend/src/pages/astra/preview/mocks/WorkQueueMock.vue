<template>
  <div>
    <header class="mb-4">
      <h1 class="text-[1.75rem] font-bold text-[var(--astra-text)]">
        Work queue
        <span class="ml-2">{{ summary.total }}</span>
        <span class="astra-muted ml-1 text-base font-medium">actions today</span>
      </h1>
      <div class="mt-3 flex flex-wrap gap-1.5">
        <button class="astra-pill astra-pill--active">All</button>
        <button class="astra-pill">Calls</button>
        <button class="astra-pill">Follow-ups</button>
      </div>
    </header>
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-12">
      <aside class="flex flex-col gap-4 lg:col-span-3">
        <AstraCard title="Type">
          <ul>
            <li class="astra-row">
              <span class="flex-1 text-sm">Calls</span>
              <strong>{{ summary.byType.calls }}</strong>
            </li>
            <li class="astra-row">
              <span class="flex-1 text-sm">Follow-ups</span>
              <strong>{{ summary.byType.follow_ups }}</strong>
            </li>
          </ul>
        </AstraCard>
        <AstraCard title="Priority">
          <ul>
            <li class="astra-row">
              <span class="size-2 rounded-full bg-[var(--astra-danger)]" />
              <span class="flex-1 text-sm">High</span>
              <strong>{{ summary.byPriority.high }}</strong>
            </li>
            <li class="astra-row">
              <span class="size-2 rounded-full bg-[var(--astra-warn)]" />
              <span class="flex-1 text-sm">Medium</span>
              <strong>{{ summary.byPriority.med }}</strong>
            </li>
            <li class="astra-row">
              <span class="size-2 rounded-full bg-[var(--astra-muted)]" />
              <span class="flex-1 text-sm">Low</span>
              <strong>{{ summary.byPriority.low }}</strong>
            </li>
          </ul>
        </AstraCard>
      </aside>
      <section class="flex flex-col gap-2 lg:col-span-9">
        <div
          v-for="(item, i) in items"
          :key="item.title"
          class="astra-card !p-3"
          :class="i === 0 ? 'ring-1 ring-[var(--astra-primary)]/30' : ''"
        >
          <div class="flex flex-wrap items-center gap-3">
            <span class="astra-badge" :class="`astra-badge--${item.pri}`">{{ item.badge }}</span>
            <AstraAvatar :name="item.title" :seed="item.title" size="sm" />
            <div class="min-w-0 flex-1">
              <p class="text-sm font-semibold">{{ item.title }}</p>
              <p class="astra-muted text-xs">{{ item.reason }}</p>
            </div>
            <button type="button" class="astra-btn" :class="item.btn">{{ item.label }}</button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AstraCard from '@/components/astra/AstraCard.vue'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import { summarizeWorkQueue } from '@/components/astra/workqueue/queueSummary'

/** Fixture list — header / Type / Priority all derive from this same array. */
const items = [
  {
    type: 'call',
    action: 'call',
    priority: 'High',
    badge: 'High',
    pri: 'high',
    title: 'Rahul Mehta - Infosys',
    reason: 'Opened quote 3x',
    label: 'Call',
    btn: 'astra-btn--primary',
  },
  {
    type: 'follow_up',
    action: 'follow_up',
    priority: 'Med',
    badge: 'Med',
    pri: 'med',
    title: 'Sneha Kapoor - HDFC',
    reason: 'Replied to email',
    label: 'Follow up',
    btn: 'astra-btn--outline',
  },
  {
    type: 'follow_up',
    action: 'follow_up',
    priority: 'High',
    badge: 'High',
    pri: 'high',
    title: 'Zomato renewal',
    reason: 'Missed deadline',
    label: 'Follow up',
    btn: 'astra-btn--outline',
  },
  {
    type: 'follow_up',
    action: 'open',
    priority: 'Low',
    badge: 'Low',
    pri: 'low',
    title: 'Wipro intro',
    reason: 'New lead added',
    label: 'Open',
    btn: 'astra-btn--primary',
  },
]

const summary = computed(() => summarizeWorkQueue(items, { showWhatsApp: false }))
</script>
