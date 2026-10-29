<template>
  <div v-if="configured" class="flex gap-1.5">
    <Button
      :tooltip="callLabel"
      :label="showLabels ? callLabel : undefined"
      :icon="showLabels ? undefined : LucidePhone"
      :iconLeft="showLabels ? LucidePhone : undefined"
      :iconRight="showLabels && shortLabels ? LucideExternalLink : undefined"
      :size="size"
      @click="openCall"
    />
    <Button
      v-if="!shortLabels"
      :tooltip="__('Message with AI')"
      :label="showLabels ? __('Message with AI') : undefined"
      :icon="showLabels ? undefined : LucideMessagesSquare"
      :iconLeft="showLabels ? LucideMessagesSquare : undefined"
      :size="size"
      @click="openMessage"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Button } from 'frappe-ui'
import LucidePhone from '~icons/lucide/phone'
import LucideMessagesSquare from '~icons/lucide/messages-square'
import LucideExternalLink from '~icons/lucide/external-link'
import {
  isAstraConnectConfigured,
  openConnectCompose,
} from '@/utils/astraConnect'

const props = defineProps({
  recordType: { type: String, required: true },
  recordId: { type: String, required: true },
  phone: { type: String, default: '' },
  size: { type: String, default: 'md' },
  showLabels: { type: Boolean, default: false },
  /** Figma record chrome: "Call" + external affordance, no Message button. */
  shortLabels: { type: Boolean, default: false },
})

const configured = computed(() => isAstraConnectConfigured())
const callLabel = computed(() =>
  props.shortLabels ? __('Call') : __('Call with AI'),
)

function openCall() {
  openConnectCompose('calls', {
    recordType: props.recordType,
    recordId: props.recordId,
    phone: props.phone || undefined,
  })
}

function openMessage() {
  openConnectCompose('messages', {
    recordType: props.recordType,
    recordId: props.recordId,
    phone: props.phone || undefined,
  })
}
</script>
