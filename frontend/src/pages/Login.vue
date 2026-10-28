<template>
  <!-- In-app login for local Vite. Production uses Frappe /login with the
       same .astra-login-* chrome from astra-login.css. Auth calls `login`
       (session store) so redirects and 429 lockouts match production. -->
  <div class="astra-login" data-testid="astra-login">
    <aside class="astra-login__panel" aria-hidden="true">
      <p class="astra-login__eyebrow">{{ __('ASTRA CRM') }}</p>
      <h2 class="astra-login__headline">
        {{ __('Every lead, deal and customer conversation in one place.') }}
      </h2>
      <ul class="astra-login__features">
        <li>
          <span class="astra-login__feature-icon" aria-hidden="true">
            <Icon icon="lucide-list" class="size-4" />
          </span>
          <div>
            <strong>{{ __('Start with your day') }}</strong>
            <span>{{
              __('Due tasks, response deadlines and quiet leads, ranked for you.')
            }}</span>
          </div>
        </li>
        <li>
          <span class="astra-login__feature-icon" aria-hidden="true">
            <Icon icon="lucide-layout-grid" class="size-4" />
          </span>
          <div>
            <strong>{{ __('Stages your team defines') }}</strong>
            <span>{{
              __(
                'Pipeline stages come from Settings, so boards and paths update on their own.',
              )
            }}</span>
          </div>
        </li>
        <li>
          <span class="astra-login__feature-icon" aria-hidden="true">
            <Icon icon="lucide-phone" class="size-4" />
          </span>
          <div>
            <strong>{{ __('Calls and messages through Astra Connect') }}</strong>
            <span>{{
              __(
                'Call outcomes and summaries land on the record automatically.',
              )
            }}</span>
          </div>
        </li>
      </ul>
    </aside>

    <div class="astra-login__form-pane">
      <div class="astra-login__card">
        <div class="astra-login__head">
          <img
            class="astra-login-logo"
            :src="logoSrc"
            :srcset="logoSrcset"
            alt="Astra CRM"
            height="28"
          />
          <h1>{{ mode === 'forgot' ? __('Forgot password') : __('Sign in') }}</h1>
          <p class="astra-login__sub">
            {{
              mode === 'forgot'
                ? __('Enter your work email and we will send a reset link.')
                : __('Use your work email. Your admin manages access.')
            }}
          </p>
        </div>

        <form
          v-if="mode === 'login'"
          class="flex flex-col gap-4"
          @submit.prevent="onSubmit"
        >
          <label class="block text-[12px] font-semibold text-[color:var(--crm-fg)]">
            {{ __('Work email') }}
            <input
              v-model="email"
              class="mt-1.5"
              type="email"
              autocomplete="username"
              required
            />
          </label>
          <div>
            <div class="mb-1.5 flex items-baseline justify-between gap-3">
              <label
                class="text-[12px] font-semibold text-[color:var(--crm-fg)]"
                for="astra-login-password"
              >
                {{ __('Password') }}
              </label>
              <button
                type="button"
                class="text-[12.5px] font-medium text-[color:var(--crm-primary)]"
                @click="mode = 'forgot'"
              >
                {{ __('Forgot password?') }}
              </button>
            </div>
            <div class="relative">
              <input
                id="astra-login-password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
              />
              <button
                type="button"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-[color:var(--crm-muted-fg)]"
                :aria-label="showPassword ? __('Hide password') : __('Show password')"
                @click="showPassword = !showPassword"
              >
                <Icon
                  :icon="showPassword ? 'lucide-eye-off' : 'lucide-eye'"
                  class="size-4"
                />
              </button>
            </div>
          </div>
          <p
            v-if="errorMessage"
            class="text-[12.5px] font-medium text-[color:var(--crm-danger)]"
            role="alert"
          >
            {{ errorMessage }}
          </p>
          <button class="btn-primary mt-1" type="submit" :disabled="submitting">
            {{ submitting ? __('Signing in…') : __('Sign in') }}
          </button>
        </form>

        <form
          v-else
          class="flex flex-col gap-4"
          @submit.prevent="onForgot"
        >
          <label class="block text-[12px] font-semibold text-[color:var(--crm-fg)]">
            {{ __('Work email') }}
            <input
              v-model="email"
              class="mt-1.5"
              type="email"
              autocomplete="username"
              required
            />
          </label>
          <p
            v-if="errorMessage"
            class="text-[12.5px] font-medium text-[color:var(--crm-danger)]"
            role="alert"
          >
            {{ errorMessage }}
          </p>
          <p
            v-if="forgotSent"
            class="text-[12.5px] text-[color:var(--crm-muted-fg)]"
            role="status"
          >
            {{ __('If that account exists, a reset link is on its way.') }}
          </p>
          <button class="btn-primary mt-1" type="submit" :disabled="submitting">
            {{ submitting ? __('Sending…') : __('Reset Password') }}
          </button>
          <button
            type="button"
            class="text-center text-[12.5px] font-medium text-[color:var(--crm-primary)]"
            @click="mode = 'login'"
          >
            {{ __('Back to Login') }}
          </button>
        </form>

        <p v-if="mode === 'login'" class="astra-login__lockout" role="note">
          <span class="astra-login__lock-icon" aria-hidden="true">
            <Icon icon="lucide-lock" class="size-3.5" />
          </span>
          {{
            __(
              'Too many failed attempts locks the account for a short time. Ask your admin if you are locked out.',
            )
          }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { usePageMeta, useColorScheme, call } from 'frappe-ui'
import Icon from '@/components/Icon.vue'
import { sessionStore } from '@/stores/session'
import {
  ASTRA_FAVICON,
  ASTRA_LOGO,
  ASTRA_LOGO_ON_DARK,
  ASTRA_LOCKUP_SRCSET,
  ASTRA_NAV_LOCKUP_SRCSET,
} from '@/assets/brand'

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const mode = ref('login')
const submitting = ref(false)
const errorMessage = ref('')
const forgotSent = ref(false)

const { resolvedColorScheme } = useColorScheme()
const session = sessionStore()

const logoSrc = computed(() =>
  resolvedColorScheme.value === 'dark' ? ASTRA_LOGO_ON_DARK : ASTRA_LOGO,
)
const logoSrcset = computed(() =>
  resolvedColorScheme.value === 'dark'
    ? ASTRA_NAV_LOCKUP_SRCSET
    : ASTRA_LOCKUP_SRCSET,
)

usePageMeta(() => ({
  title: __('Login'),
  icon: ASTRA_FAVICON,
}))

function lockoutMessage(error) {
  const status =
    error?.httpStatus ||
    error?.status ||
    error?.response?.status ||
    error?.exc_type === 'SecurityException'
  if (status === 429 || error?.exc_type === 'SecurityException') {
    return __(
      'Too many failed attempts. Please try again after some time.',
    )
  }
  return error?.messages?.[0] || error?.message || __('Invalid Email or Password')
}

async function onSubmit() {
  errorMessage.value = ''
  submitting.value = true
  try {
    await session.login.submit({
      usr: email.value,
      pwd: password.value,
    })
  } catch (error) {
    errorMessage.value = lockoutMessage(error)
  } finally {
    submitting.value = false
  }
}

async function onForgot() {
  errorMessage.value = ''
  forgotSent.value = false
  submitting.value = true
  try {
    await call('frappe.core.doctype.user.user.reset_password', {
      user: email.value,
    })
    forgotSent.value = true
  } catch (error) {
    // Same generic copy either way — do not leak whether the account exists.
    if (error?.httpStatus === 429 || error?.status === 429) {
      errorMessage.value = lockoutMessage(error)
    } else {
      forgotSent.value = true
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.astra-login {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  min-height: 100dvh;
  width: 100%;
  background: var(--crm-muted, #f6f8fa);
}

.astra-login__form-pane {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  min-width: 0;
  background: var(--crm-muted, #f8f9fb);
}

.astra-login__panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 28px;
  padding: 56px 48px;
  background: var(--crm-nav, #07161f);
  color: var(--crm-nav-fg, #c4d2da);
  order: 2;
}

.astra-login__eyebrow {
  margin: 0;
  font: 700 11px/1.3 var(--font-sans);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--crm-teal, #0e8f83);
}

.astra-login__headline {
  margin: 0;
  max-width: 22ch;
  font: 700 32px/1.2 var(--font-sans);
  letter-spacing: -0.02em;
  color: #fff;
}

.astra-login__features {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.astra-login__features li {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.astra-login__feature-icon {
  flex: 0 0 28px;
  height: 28px;
  display: grid;
  place-items: center;
  color: var(--crm-teal, #2dd4bf);
}

.astra-login__features strong {
  display: block;
  font: 600 14px/1.35 var(--font-sans);
  color: #fff;
}

.astra-login__features span {
  display: block;
  margin-top: 2px;
  font: 400 13px/1.45 var(--font-sans);
  color: var(--crm-muted-fg, #97a9b4);
}

.astra-login__card {
  width: min(100%, 400px);
}

.astra-login__head h1 {
  margin: 20px 0 6px;
  font: 700 28px/1.2 var(--font-sans);
  letter-spacing: -0.02em;
  color: var(--crm-fg);
}

.astra-login__sub {
  margin: 0;
  font: 400 13px/1.45 var(--font-sans);
  color: var(--crm-muted-fg);
}

.astra-login-logo {
  display: block;
  height: 28px;
  width: auto;
  max-width: 180px;
  object-fit: contain;
}

.astra-login__card input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid var(--crm-border-strong);
  background: var(--crm-card);
  color: var(--crm-fg);
  font: 400 13px var(--font-sans);
}

.astra-login__card input:focus {
  outline: none;
  border-color: var(--crm-primary);
  box-shadow: var(--crm-input-focus);
}

.astra-login__card .btn-primary {
  width: 100%;
  min-height: 40px;
  border: 0;
  border-radius: 8px;
  color: var(--crm-primary-fg);
  font: 600 13px var(--font-sans);
  background: var(--crm-primary);
  cursor: pointer;
}

.astra-login__card .btn-primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.astra-login__lockout {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin: 20px 0 0;
  padding: 12px 14px;
  border-radius: 8px;
  background: var(--crm-neutral-soft);
  border: 1px solid var(--crm-border);
  font: 400 12.5px/1.45 var(--font-sans);
  color: var(--crm-muted-fg);
}

.astra-login__lock-icon {
  flex: 0 0 14px;
  margin-top: 2px;
}

@media (max-width: 900px) {
  .astra-login {
    grid-template-columns: 1fr;
  }

  .astra-login__panel {
    display: none;
  }

  .astra-login__form-pane {
    min-height: 100dvh;
  }
}
</style>
