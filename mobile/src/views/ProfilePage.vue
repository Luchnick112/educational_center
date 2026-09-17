<template>
  <ion-page>
    <MobileHeader
      title="Профіль"
      :refresh="isAdmin ? loadStatistics : undefined"
      :loading="statisticsLoading"
    />
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

        <section v-if="isAdmin" class="info-section">
          <h2>Статистика</h2>

          <div v-if="statisticsLoading" class="profile-statistics-state" aria-live="polite">
            <ion-spinner name="crescent" />
            <span>Завантаження...</span>
          </div>

          <div v-else-if="statisticsError" class="profile-statistics-state profile-statistics-state--error" role="alert">
            <span>{{ statisticsError }}</span>
            <ion-button fill="outline" size="small" @click="loadStatistics">Спробувати ще</ion-button>
          </div>

          <div v-else class="profile-statistics-grid">
            <article v-for="(value, label) in statistics" :key="label" class="profile-statistic">
              <strong>{{ value }}</strong>
              <span>{{ label }}</span>
            </article>
          </div>
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
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { IonButton, IonContent, IonIcon, IonPage, IonSpinner } from '@ionic/vue'
import { logOutOutline } from 'ionicons/icons'
import MobileHeader from '@/components/MobileHeader.vue'
import { ApiError, apiRequest, errorMessage } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import type { DashboardResponse } from '@/types/api'
import { roleLabel } from '@/utils/format'

const auth = useAuthStore()
const router = useRouter()
const statistics = ref<Record<string, number>>({})
const statisticsLoading = ref(false)
const statisticsError = ref('')
const isAdmin = computed(() => Boolean(auth.me?.is_staff || auth.me?.role === 'admin'))
const initials = computed(() =>
  [auth.me?.first_name, auth.me?.last_name].filter(Boolean).map((part) => part?.[0]).join('').toUpperCase() || 'H',
)

async function loadStatistics() {
  if (!isAdmin.value) return

  statisticsLoading.value = true
  statisticsError.value = ''
  try {
    const dashboard = await apiRequest<DashboardResponse>('/api/users/dashboard/')
    statistics.value = dashboard.stats ?? {}
  } catch (caught) {
    statisticsError.value = caught instanceof ApiError
      ? errorMessage(caught.payload, 'Не вдалося завантажити статистику')
      : 'Не вдалося завантажити статистику'
  } finally {
    statisticsLoading.value = false
  }
}

async function logout() {
  await auth.logout()
  await router.replace({ name: 'login' })
}

onMounted(loadStatistics)
</script>

<style scoped>
.profile-statistics-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.profile-statistic {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 13px;
  border-radius: 7px;
  background: var(--app-soft);
}

.profile-statistic strong {
  color: var(--app-ink);
  font-size: 22px;
  line-height: 1;
}

.profile-statistic span {
  color: var(--app-muted);
  font-size: 11px;
  line-height: 1.35;
}

.profile-statistics-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  min-height: 84px;
  color: var(--app-muted);
  font-size: 12px;
  text-align: center;
}

.profile-statistics-state ion-spinner {
  width: 20px;
  height: 20px;
}

.profile-statistics-state--error {
  flex-direction: column;
  color: #9b4032;
}
</style>
