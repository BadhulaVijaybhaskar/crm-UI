import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import router from '@/router'
import { ref, computed } from 'vue'

export const sessionStore = defineStore('crm-session', () => {
  function sessionUser() {
    let cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
    let _sessionUser = cookies.get('user_id')
    if (_sessionUser === 'Guest') {
      _sessionUser = null
    }
    return _sessionUser
  }

  let user = ref(sessionUser())
  const isLoggedIn = computed(() => !!user.value)

  const login = createResource({
    url: 'login',
    onError(error) {
      const status = error?.httpStatus || error?.status || error?.response?.status
      const err = new Error(
        status === 429 || error?.exc_type === 'SecurityException'
          ? __('Too many failed attempts. Please try again after some time.')
          : __('Invalid Email or Password'),
      )
      err.status = status
      err.httpStatus = status
      err.exc_type = error?.exc_type
      throw err
    },
    onSuccess() {
      user.value = sessionUser()
      login.reset()
      router.replace({ path: '/' })
    },
  })

  const logout = createResource({
    url: 'logout',
    onSuccess() {
      user.value = null
      window.location.href = '/login?redirect-to=/crm'
    },
  })

  return {
    user,
    isLoggedIn,
    login,
    logout,
  }
})
