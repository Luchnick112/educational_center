import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { apiRequest, clearTokens, setTokens } from '@/lib/api'

export type Role = 'admin' | 'staff' | 'teacher' | 'student' | 'parent' | string

export type MeResponse = {
  id: number
  first_name: string
  last_name: string
  telegram_username: string
  email: string
  role: Role
  is_staff: boolean
  my: Array<{ key: string; url: string }>
}

function errorMessage(e: any, fallback: string) {
  const payload = e?.payload
  if (payload?.detail) return String(payload.detail)
  if (payload && typeof payload === 'object') {
    return Object.entries(payload)
      .map(([field, messages]) => {
        const text = Array.isArray(messages) ? messages.join(', ') : String(messages)
        return `${field}: ${text}`
      })
      .join('; ')
  }
  return e?.message || fallback
}

export const useAuthStore = defineStore('auth', () => {
  const me = ref<MeResponse | null>(null)
  const bootstrapped = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // localStorage is not reactive; keep an explicit reactive flag in sync with token writes.
  const isAuthed = ref(!!localStorage.getItem('access'))
  const displayName = computed(() => {
    if (!me.value) return ''
    const fn = me.value.first_name?.trim()
    const ln = me.value.last_name?.trim()
    return [fn, ln].filter(Boolean).join(' ') || me.value.telegram_username || me.value.email || `User #${me.value.id}`
  })

  async function bootstrap() {
    if (bootstrapped.value) return
    bootstrapped.value = true

    isAuthed.value = !!localStorage.getItem('access')
    if (!isAuthed.value) return

    try {
      me.value = await apiRequest<MeResponse>('/api/me/')
      isAuthed.value = true
    } catch {
      // Tokens may be invalid; wipe and continue unauthenticated.
      clearTokens()
      me.value = null
      isAuthed.value = false
    }
  }

  async function refreshMe() {
    isAuthed.value = !!localStorage.getItem('access')
    if (!isAuthed.value) {
      me.value = null
      return
    }

    try {
      me.value = await apiRequest<MeResponse>('/api/me/')
      isAuthed.value = true
    } catch {
      clearTokens()
      me.value = null
      isAuthed.value = false
      throw new Error('Session refresh failed')
    }
  }

  async function logIn(payload: { email?: string; telegram_username?: string; password: string }) {
    isLoading.value = true
    error.value = null
    try {
      const tokens = await apiRequest<{ access: string; refresh: string }>('/api/users/token/', {
        method: 'POST',
        auth: false,
        body: payload,
      })
      setTokens(tokens)
      isAuthed.value = true
      me.value = await apiRequest<MeResponse>('/api/me/')
    } catch (e: any) {
      error.value = errorMessage(e, 'Login failed')
      clearTokens()
      me.value = null
      isAuthed.value = false
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function register(payload: {
    first_name: string
    last_name: string
    telegram_username: string
    email?: string
    role: Role
    phone?: string
    password: string
  }) {
    isLoading.value = true
    error.value = null
    try {
      await apiRequest('/api/users/register/', { method: 'POST', auth: false, body: payload })
      // After register, log in by the available identifier.
      if (payload.telegram_username) {
        await logIn({ telegram_username: payload.telegram_username, password: payload.password })
      } else {
        await logIn({ email: payload.email, password: payload.password })
      }
    } catch (e: any) {
      error.value = errorMessage(e, 'Registration failed')
      throw e
    } finally {
      isLoading.value = false
    }
  }

  function logOut() {
    clearTokens()
    me.value = null
    isAuthed.value = false
  }

  return {
    me,
    bootstrapped,
    isAuthed,
    isLoading,
    error,
    displayName,
    bootstrap,
    refreshMe,
    logIn,
    register,
    logOut,
  }
})
