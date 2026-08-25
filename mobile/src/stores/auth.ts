import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { ApiError, apiRequest, errorMessage, type AuthTokens } from '@/services/api'
import { tokenStorage } from '@/services/tokenStorage'
import type { MeResponse } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  const me = ref<MeResponse | null>(null)
  const ready = ref(false)
  const loading = ref(false)
  const error = ref('')

  const isAuthenticated = computed(() => Boolean(me.value))
  const displayName = computed(() => {
    if (!me.value) return ''
    return [me.value.first_name, me.value.last_name].filter(Boolean).join(' ') || me.value.telegram_username || me.value.email
  })

  async function bootstrap() {
    if (ready.value) return
    try {
      const tokens = await tokenStorage.get()
      if (tokens) me.value = await apiRequest<MeResponse>('/api/me/')
    } catch {
      await tokenStorage.clear()
      me.value = null
    } finally {
      ready.value = true
    }
  }

  async function login(loginValue: string, password: string) {
    loading.value = true
    error.value = ''
    try {
      const tokens = await apiRequest<AuthTokens>('/api/users/token/', {
        method: 'POST',
        auth: false,
        body: { login: loginValue.trim(), password },
      })
      await tokenStorage.set(tokens)
      me.value = await apiRequest<MeResponse>('/api/me/')
    } catch (caught) {
      await tokenStorage.clear()
      me.value = null
      error.value = caught instanceof ApiError
        ? errorMessage(caught.payload, 'Перевірте логін і пароль')
        : 'Не вдалося підключитися до сервера. Перевірте адресу API та USB-з’єднання.'
      throw caught
    } finally {
      loading.value = false
    }
  }

  async function refreshMe() {
    me.value = await apiRequest<MeResponse>('/api/me/')
  }

  async function logout() {
    await tokenStorage.clear()
    me.value = null
  }

  return { me, ready, loading, error, isAuthenticated, displayName, bootstrap, login, refreshMe, logout }
})
