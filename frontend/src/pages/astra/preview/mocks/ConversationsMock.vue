<template>
  <div class="grid min-h-[70vh] grid-cols-1 gap-3 lg:grid-cols-12">
    <AstraCard class="flex flex-col lg:col-span-3" flush>
      <div class="border-b border-[var(--astra-border)] px-4 pb-3 pt-4">
        <h2 class="astra-card__title">Conversations</h2>
        <div class="mt-3 flex flex-wrap gap-1.5">
          <button class="astra-pill astra-pill--active">All</button>
          <button class="astra-pill">Calls</button>
          <button class="astra-pill">Email</button>
        </div>
      </div>
      <ul class="p-2">
        <li v-for="(t, i) in threads" :key="t.name">
          <div
            class="flex gap-2.5 rounded-[12px] px-2 py-2.5"
            :class="i === 0 ? 'bg-[color-mix(in_srgb,var(--astra-primary)_10%,transparent)] ring-1 ring-[var(--astra-primary)]/40' : ''"
          >
            <AstraAvatar :name="t.name" :seed="t.name" size="sm" />
            <div class="min-w-0 flex-1">
              <div class="flex justify-between gap-2">
                <p class="truncate text-sm font-semibold">{{ t.name }}</p>
                <span class="astra-muted text-[11px]">{{ t.time }}</span>
              </div>
              <p class="astra-muted truncate text-xs">{{ t.snippet }}</p>
            </div>
          </div>
        </li>
      </ul>
    </AstraCard>

    <AstraCard class="flex flex-col lg:col-span-6" flush>
      <div class="border-b border-[var(--astra-border)] px-4 py-3">
        <h2 class="text-base font-bold">Priya Nair - HDFC</h2>
        <p class="astra-muted text-xs">Read-only · calls, emails and notes</p>
      </div>
      <div class="flex flex-1 flex-col gap-3 p-4">
        <div class="rounded-[12px] border border-[var(--astra-border)] p-3">
          <div class="flex items-center gap-2">
            <span class="text-sm font-semibold">AI call 3m 40s</span>
            <span class="astra-badge astra-badge--success">Interested</span>
          </div>
          <p class="astra-muted mt-2 text-xs">Discussed the proposal and next steps.</p>
        </div>
        <div class="max-w-[85%] rounded-[14px] border border-[var(--astra-border)] px-3 py-2 text-sm">
          Can you share pricing?
          <p class="astra-muted mt-1 text-[11px]">10:40</p>
        </div>
        <div class="ml-auto max-w-[85%] rounded-[14px] bg-[var(--astra-teal)] px-3 py-2 text-sm text-white">
          Sent the quote
          <p class="mt-1 text-[11px] text-white/80">10:41</p>
        </div>
      </div>
      <div class="border-t border-[var(--astra-border)] px-4 py-3">
        <p class="astra-muted text-xs">
          Replies and WhatsApp compose open in Astra Connect. This view does not send messages.
        </p>
      </div>
    </AstraCard>

    <AstraCard class="lg:col-span-3" flush>
      <div class="flex flex-col items-start gap-3 px-4 py-5">
        <AstraAvatar name="Priya Nair" seed="PN" size="lg" />
        <div>
          <h3 class="text-lg font-bold">Priya Nair</h3>
          <p class="astra-muted text-sm">HDFC</p>
        </div>
        <p class="text-sm font-medium">+91 98765 43210</p>
        <div class="w-full rounded-[12px] border border-[var(--astra-border)] p-3">
          <p class="text-base font-bold">₹22L Proposal</p>
          <div class="mt-2 flex gap-1.5">
            <span class="astra-badge astra-badge--med">Hot</span>
            <span class="astra-badge astra-badge--med">VIP</span>
          </div>
        </div>
      </div>
    </AstraCard>
  </div>
</template>

<script setup>
import AstraCard from '@/components/astra/AstraCard.vue'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'

const threads = [
  { name: 'Priya Nair', time: '10:42', snippet: 'Call · Interested' },
  { name: 'Rahul Mehta', time: 'Yesterday', snippet: 'Email · Send the brochure' },
  { name: 'Ankit Rao', time: 'Mon', snippet: 'Note · Follow up Friday' },
]
</script>
