<template>
  <ion-page>
    <MobileHeader title="Профіль" />
    <ion-content :fullscreen="true">
      <div class="profile-hero">
        <div class="avatar avatar--large">{{ initials }}</div>
        <div>
          <h1>{{ auth.displayName }}</h1>
          <p>{{ roleLabel(auth.me?.role) }}</p>
        </div>
      </div>

      <div class="page-body profile-body">
        <section class="info-section">
          <h2>Контакти</h2>
          <dl>
            <div><dt>Email</dt><dd>{{ auth.me?.email || 'Не вказано' }}</dd></div>
            <div><dt>Телефон</dt><dd>{{ auth.me?.phone || 'Не вказано' }}</dd></div>
            <div><dt>Telegram</dt><dd>{{ auth.me?.telegram_username || 'Не вказано' }}</dd></div>
          </dl>
        </section>

        <ion-button
          href="https://helper-lesson.net/privacy/"
          target="_blank"
          rel="noopener noreferrer"
          expand="block"
          fill="clear"
        >
          Політика конфіденційності
        </ion-button>

        <ion-button
          href="mailto:hello@helper-lesson.net?subject=%D0%92%D0%B8%D0%B4%D0%B0%D0%BB%D0%B5%D0%BD%D0%BD%D1%8F%20%D0%B0%D0%BA%D0%B0%D1%83%D0%BD%D1%82%D0%B0%20%D1%96%20%D0%B4%D0%B0%D0%BD%D0%B8%D1%85%20Helper"
          expand="block"
          fill="clear"
          color="danger"
        >
          Видалити акаунт і дані
        </ion-button>

        <ion-button expand="block" fill="outline" color="danger" @click="logout">
          <ion-icon slot="start" :icon="logOutOutline" />
          Вийти з акаунта
        </ion-button>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { IonButton, IonContent, IonIcon, IonPage } from '@ionic/vue'
import { logOutOutline } from 'ionicons/icons'
import MobileHeader from '@/components/MobileHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { roleLabel } from '@/utils/format'

const auth = useAuthStore()
const router = useRouter()
const initials = computed(() =>
  [auth.me?.first_name, auth.me?.last_name].filter(Boolean).map((part) => part?.[0]).join('').toUpperCase() || 'H',
)

async function logout() {
  await auth.logout()
  await router.replace({ name: 'login' })
}
</script>
