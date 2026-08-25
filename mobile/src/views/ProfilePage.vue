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
