<template>
  <div class="auth">
    <div class="auth__card">
      <h1 class="auth__title">Вхід</h1>

      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span class="field__label">Email або Telegram username</span>
          <input v-model.trim="login" class="input" autocomplete="username" placeholder="email@example.com або @username" />
        </label>

        <label class="field">
          <span class="field__label">Пароль</span>
          <input v-model="password" class="input" type="password" autocomplete="current-password" />
        </label>

        <div class="row">
          <button class="btn" type="submit" :disabled="auth.isLoading || !password">Увійти</button>
          <RouterLink class="link" to="/register">Створити акаунт</RouterLink>
        </div>

        <div v-if="auth.error" class="error">{{ auth.error }}</div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const login = ref('')
const password = ref('')

function isEmail(value: string) {
  return value.includes('@') && value.includes('.')
}

async function onSubmit() {
  const value = login.value.trim()
  const payload: { email?: string; telegram_username?: string; password: string } = { password: password.value }
  if (value) {
    if (isEmail(value) && !value.startsWith('@')) payload.email = value
    else payload.telegram_username = value
  }

  await auth.logIn(payload)
  const next = typeof route.query.next === 'string' ? route.query.next : '/me'
  await router.push(next)
}
</script>
