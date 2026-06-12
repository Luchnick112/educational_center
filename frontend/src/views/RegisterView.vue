<template>
  <div class="auth">
    <div class="auth__card">
      <h1 class="auth__title">Створення акаунта</h1>

      <form class="form" @submit.prevent="onSubmit">
        <div class="grid2">
          <label class="field">
            <span class="field__label">Ім'я</span>
            <input v-model.trim="firstName" class="input" autocomplete="given-name" />
          </label>
          <label class="field">
            <span class="field__label">Прізвище</span>
            <input v-model.trim="lastName" class="input" autocomplete="family-name" />
          </label>
        </div>

        <label class="field">
          <span class="field__label">Telegram username</span>
          <input v-model.trim="telegram" class="input" placeholder="@username" autocomplete="username" />
        </label>

        <label class="field">
          <span class="field__label">Email</span>
          <input v-model.trim="email" class="input" type="email" autocomplete="email" />
        </label>

        <label class="field">
          <span class="field__label">Роль</span>
          <select v-model="role" class="input">
            <option value="student">Учень</option>
            <option value="parent">Батько/Мати</option>
            <option value="teacher">Вчитель</option>
          </select>
        </label>

        <label class="field">
          <span class="field__label">Телефон (необов'язково)</span>
          <input v-model.trim="phone" class="input" autocomplete="tel" placeholder="+380501112233" />
        </label>

        <label class="field">
          <span class="field__label">Пароль</span>
          <input v-model="password" class="input" type="password" autocomplete="new-password" />
        </label>

        <div class="row">
          <button class="btn" type="submit" :disabled="auth.isLoading || (!telegram && !email && !phone) || password.length < 8">
            {{ auth.isLoading ? 'Створення...' : 'Створити' }}
          </button>
          <RouterLink class="link" to="/login">Назад до входу</RouterLink>
        </div>

        <div v-if="auth.error" class="error">{{ auth.error }}</div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const firstName = ref('')
const lastName = ref('')
const telegram = ref('')
const email = ref('')
const role = ref<'student' | 'parent' | 'teacher'>('student')
const phone = ref('')
const password = ref('')

async function onSubmit() {
  try {
    await auth.register({
      first_name: firstName.value.trim(),
      last_name: lastName.value.trim(),
      telegram_username: telegram.value.trim(),
      email: email.value.trim() || undefined,
      role: role.value,
      phone: phone.value.trim() || undefined,
      password: password.value,
    })
    router.push({ name: 'dashboard' })
  } catch {
    // auth.error is shown below the form.
  }
}
</script>
