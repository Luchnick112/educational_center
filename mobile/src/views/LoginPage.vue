<template>
  <ion-page>
    <ion-content :fullscreen="true" class="login-content">
      <main class="login-shell">
        <section class="login-brand" aria-label="Helper">
          <img src="/logo.png" alt="" class="login-logo" />
          <div>
            <div class="login-brand__name">Helper</div>
            <div class="login-brand__kind">Освітній центр</div>
          </div>
        </section>

        <section class="login-panel">
          <div class="login-heading">
            <p class="eyebrow">Особистий кабінет</p>
            <h1>Вхід</h1>
            <p>Розклад, заняття та оплати в одному місці.</p>
          </div>

          <form class="login-form" @submit.prevent="submit">
            <ion-input
              v-model="loginValue"
              fill="outline"
              label="Телефон, email або Telegram"
              label-placement="floating"
              autocomplete="username"
              inputmode="email"
              required
            />
            <ion-input
              v-model="password"
              fill="outline"
              label="Пароль"
              label-placement="floating"
              type="password"
              autocomplete="current-password"
              required
            />
            <p v-if="auth.error" class="form-error" role="alert">{{ auth.error }}</p>
            <ion-button type="submit" expand="block" size="large" :disabled="auth.loading || !loginValue || !password">
              <ion-spinner v-if="auth.loading" slot="start" name="crescent" />
              {{ auth.loading ? 'Входимо...' : 'Увійти' }}
            </ion-button>
          </form>
        </section>
      </main>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { IonButton, IonContent, IonInput, IonPage, IonSpinner } from '@ionic/vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const loginValue = ref('')
const password = ref('')

async function submit() {
  try {
    await auth.login(loginValue.value, password.value)
    await router.replace({ name: 'lessons' })
  } catch {
    // The store exposes the API validation message in the form.
  }
}
</script>
