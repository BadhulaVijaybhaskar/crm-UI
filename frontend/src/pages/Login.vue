<template>
  <!-- In-app login mock for local Vite / screenshots. Production uses Frappe /login
       with the same .astra-login-* classes from astra-theme + website CSS. -->
  <div class="astra-login-page" data-testid="astra-login">
    <div class="astra-login-card">
      <img
        class="astra-login-logo"
        :src="logoSrc"
        alt="Astra CRM"
      />
      <form class="flex flex-col gap-3" @submit.prevent="onSubmit">
        <label class="text-sm font-semibold text-ink-gray-7">
          {{ __('Email') }}
          <input
            v-model="email"
            class="mt-1"
            type="email"
            autocomplete="username"
            required
          />
        </label>
        <label class="text-sm font-semibold text-ink-gray-7">
          {{ __('Password') }}
          <input
            v-model="password"
            class="mt-1"
            type="password"
            autocomplete="current-password"
            required
          />
        </label>
        <button class="btn-primary mt-2" type="submit">
          {{ __('Login') }}
        </button>
      </form>
      <p class="mt-4 text-center text-sm text-ink-gray-5">
        {{ __('Astra CRM') }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { usePageMeta, useColorScheme } from 'frappe-ui'
import {
  ASTRA_FAVICON,
  ASTRA_LOGO,
  ASTRA_LOGO_ON_DARK,
} from '@/assets/brand'

const email = ref('')
const password = ref('')
const { resolvedColorScheme } = useColorScheme()

const logoSrc = computed(() =>
  resolvedColorScheme.value === 'dark' ? ASTRA_LOGO_ON_DARK : ASTRA_LOGO,
)

usePageMeta(() => ({
  title: __('Login'),
  icon: ASTRA_FAVICON,
}))

function onSubmit() {
  // Mock only — real auth is Frappe /login
  window.location.href = '/crm'
}
</script>
