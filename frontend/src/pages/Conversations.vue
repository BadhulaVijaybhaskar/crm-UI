<template>
  <div class="flex h-full flex-col">
    <AstraPageHeader
      title="Conversations"
      description="Inbox for Astra Connect messages"
    />
    <div class="flex flex-1 items-center justify-center px-crm-page-x pb-8">
      <AstraEmptyState
        title="No conversations yet"
        body="Messages from Astra Connect will show up here."
      />
    </div>
  </div>
</template>

<script setup>
import AstraEmptyState from '@/components/astra/AstraEmptyState.vue'
import AstraPageHeader from '@/components/astra/AstraPageHeader.vue'
</script>
