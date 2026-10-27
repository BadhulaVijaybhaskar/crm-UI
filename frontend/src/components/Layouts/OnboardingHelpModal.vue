<template>
  <!--
    Wrapper around framework HelpModal.
    Always uses the internal onboarding key (frappecrm) — never the branded
    "crm" slug — and never forwards a 0/0 · NaN% progress label.
  -->
  <HelpModal
    v-bind="forwardedAttrs"
    :appName="ONBOARDING_APP_NAME"
    :progress-label="safeProgressLabel"
    :progressLabel="safeProgressLabel"
  />
</template>

<script setup>
import { computed, useAttrs, unref } from 'vue'
import { HelpModal, useOnboarding } from '@framework/ui/components/Onboarding'
import {
  ONBOARDING_APP_NAME,
  formatOnboardingProgressLabel,
} from '@/components/astra/myday/myDayHelpers'

defineOptions({ inheritAttrs: false })

const attrs = useAttrs()

// Drop any caller-supplied appName so branding cannot reopen the key mismatch.
const forwardedAttrs = computed(() => {
  const next = { ...attrs }
  delete next.appName
  delete next['app-name']
  delete next.progressLabel
  delete next['progress-label']
  return next
})

const onboarding = useOnboarding(ONBOARDING_APP_NAME)
const safeProgressLabel = computed(() => {
  const label = formatOnboardingProgressLabel(
    unref(onboarding.stepsCompleted),
    unref(onboarding.totalSteps),
  )
  // Belt-and-suspenders: never hand HelpModal a NaN% string.
  if (!label || /NaN/i.test(label)) return undefined
  return label
})
</script>
