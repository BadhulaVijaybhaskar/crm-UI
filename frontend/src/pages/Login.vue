<template>
  <!-- In-app login for local Vite + parity. Production website auth uses
       crm/www/login.html with the same .astra-login-* chrome. Auth calls
       session.login so redirects and 429 lockouts match production. -->
  <div
    class="astra-login"
    :class="{ 'astra-login--dark': resolvedColorScheme === 'dark' }"
    data-testid="astra-login"
  >
    <aside class="astra-login__panel" aria-hidden="true">
      <p class="astra-login__eyebrow">{{ __('ASTRA CRM') }}</p>
      <h2 class="astra-login__headline">
        {{ __('Every lead, deal and customer conversation in one place.') }}
      </h2>
      <ul class="astra-login__features">
        <li>
          <span class="astra-login__feature-icon" aria-hidden="true">
            <svg
              viewBox="0 0 24 24"
              width="16"
              height="16"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
            </svg>
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
            <svg
              viewBox="0 0 24 24"
              width="16"
              height="16"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <path d="M3 9h18M9 21V9" />
            </svg>
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
            <svg
              viewBox="0 0 24 24"
              width="16"
              height="16"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"
              />
            </svg>
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
          class="astra-login__form"
          @submit.prevent="onSubmit"
        >
          <div class="astra-login__field">
            <label class="astra-login__label" for="login_email">{{
              __('Work email')
            }}</label>
            <input
              id="login_email"
              v-model="email"
              type="email"
              autocomplete="username"
              required
              autofocus
            />
          </div>
          <div class="astra-login__field">
            <div class="astra-login__label-row">
              <label class="astra-login__label" for="login_password">{{
                __('Password')
              }}</label>
              <button
                type="button"
                class="astra-login__forgot"
                @click="mode = 'forgot'"
              >
                {{ __('Forgot password?') }}
              </button>
            </div>
            <div class="astra-login__password">
              <input
                id="login_password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
              />
              <button
                type="button"
                class="astra-login__toggle"
                :aria-label="
                  showPassword ? __('Hide password') : __('Show password')
                "
                @click="showPassword = !showPassword"
              >
                <svg
                  viewBox="0 0 24 24"
                  width="16"
                  height="16"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  aria-hidden="true"
                >
                  <path
                    d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"
                  />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              </button>
            </div>
          </div>
          <p v-if="errorMessage" class="astra-login__error" role="alert">
            {{ errorMessage }}
          </p>
          <button class="btn-primary" type="submit" :disabled="submitting">
            {{ submitting ? __('Signing in…') : __('Sign in') }}
          </button>
        </form>

        <form v-else class="astra-login__form" @submit.prevent="onForgot">
          <div class="astra-login__field">
            <label class="astra-login__label" for="login_email_forgot">{{
              __('Work email')
            }}</label>
            <input
              id="login_email_forgot"
              v-model="email"
              type="email"
              autocomplete="username"
              required
            />
          </div>
          <p v-if="errorMessage" class="astra-login__error" role="alert">
            {{ errorMessage }}
          </p>
          <p v-if="forgotSent" class="astra-login__status" role="status">
            {{ __('If that account exists, a reset link is on its way.') }}
          </p>
          <button class="btn-primary" type="submit" :disabled="submitting">
            {{ submitting ? __('Sending…') : __('Reset Password') }}
          </button>
          <button
            type="button"
            class="astra-login__forgot astra-login__back"
            @click="mode = 'login'"
          >
            {{ __('Back to Login') }}
          </button>
        </form>

        <p v-if="mode === 'login'" class="astra-login__lockout" role="note">
          <span class="astra-login__lock-icon" aria-hidden="true">
            <svg
              viewBox="0 0 24 24"
              width="14"
              height="14"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
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
import { usePageMeta, useColorScheme } from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import {
  ASTRA_FAVICON,
  ASTRA_LOGO,
  ASTRA_LOGO_ON_DARK,
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
    return __('Too many failed attempts. Please try again after some time.')
  }
  return (
    error?.messages?.[0] || error?.message || __('Invalid Email or Password')
  )
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
    const { call } = await import('frappe-ui')
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
  background: var(--crm-bg, #f3f6f8);
  font-family: var(--font-sans);
  color: var(--crm-fg, #0b1324);
  -webkit-font-smoothing: antialiased;
}

.astra-login__form-pane {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  min-width: 0;
  background: var(--crm-bg, #f3f6f8);
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
  font: 600 11px/1.3 var(--font-sans);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--crm-teal, #0e8f83);
}

.astra-login__headline {
  margin: 0;
  max-width: 22ch;
  font-family: var(--font-sans);
  font-style: normal;
  font-weight: 600;
  font-size: 32px;
  line-height: 1.2;
  letter-spacing: -0.02em;
  font-feature-settings: "cv11", "ss01";
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
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: var(--crm-nav-active, #0f2a36);
  /* Beat .astra-login__features span color (this node is also a span). */
  color: var(--crm-teal, #0e8f83);
}

.astra-login__feature-icon svg {
  display: block;
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
}

.astra-login__features strong {
  display: block;
  font: 600 14px/1.35 var(--font-sans);
  color: #fff;
}

.astra-login__features li > div > span {
  display: block;
  margin-top: 2px;
  font: 400 13px/1.45 var(--font-sans);
  /* Panel muted — not --crm-muted-fg (that is form-pane gray). */
  color: #97a9b4;
}

.astra-login__card {
  width: min(100%, 380px);
}

.astra-login__head {
  margin-bottom: 28px;
  text-align: left;
}

.astra-login__head h1 {
  margin: 20px 0 6px;
  font: 600 28px/1.2 var(--font-sans);
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
  margin: 0;
}

.astra-login__form {
  display: flex;
  flex-direction: column;
}

.astra-login__field {
  margin-bottom: 16px;
}

.astra-login__label {
  display: block;
  margin-bottom: 6px;
  font: 600 12px/1.3 var(--font-sans);
  color: var(--crm-fg);
}

.astra-login__label-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.astra-login__label-row .astra-login__label {
  margin-bottom: 0;
}

.astra-login__forgot {
  border: 0;
  background: transparent;
  padding: 0;
  font: 500 12.5px/1.3 var(--font-sans);
  color: var(--crm-primary);
  cursor: pointer;
  text-decoration: none;
}

.astra-login__forgot:hover {
  text-decoration: underline;
}

.astra-login__back {
  margin-top: 12px;
  text-align: center;
  width: 100%;
}

.astra-login__password {
  position: relative;
}

.astra-login__card input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid var(--crm-border-strong);
  background: var(--crm-card);
  color: var(--crm-fg);
  font: 400 13px/1.45 var(--font-sans);
  box-sizing: border-box;
  box-shadow: none;
  caret-color: transparent;
}

.astra-login__password input {
  padding-right: 36px;
}

.astra-login__card input:focus {
  outline: none;
  border-color: var(--crm-primary);
  box-shadow: var(--crm-input-focus);
}

.astra-login__toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  display: grid;
  place-items: center;
  width: 16px;
  height: 16px;
  border: 0;
  background: transparent;
  padding: 0;
  color: var(--crm-muted-fg);
  cursor: pointer;
  line-height: 0;
}

.astra-login__card .btn-primary {
  display: block;
  width: 100%;
  min-height: 40px;
  margin-top: 8px;
  border: 0;
  border-radius: 8px;
  color: var(--crm-primary-fg);
  font: 600 13px/1.3 var(--font-sans);
  background: var(--crm-primary);
  cursor: pointer;
  box-shadow: none;
}

.astra-login__card .btn-primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.astra-login__error {
  margin: 0 0 8px;
  font: 500 12.5px/1.4 var(--font-sans);
  color: var(--crm-danger);
}

.astra-login__status {
  margin: 0 0 8px;
  font: 400 12.5px/1.4 var(--font-sans);
  color: var(--crm-muted-fg);
}

.astra-login__lockout {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin: 20px 0 0;
  padding: 12px 14px;
  border-radius: 8px;
  /* Match astra-login.css --astra-lockout-bg / --astra-border (not --crm-neutral-soft). */
  background: #eef1f6;
  border: 1px solid #e1e7ec;
  font: 400 12.5px/1.45 var(--font-sans);
  color: var(--crm-muted-fg);
}

.astra-login__lock-icon {
  flex: 0 0 14px;
  margin-top: 2px;
  color: var(--crm-muted-fg);
  line-height: 0;
}

.astra-login--dark .astra-login__lockout {
  background: #11212b;
  border-color: #1a2c37;
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
