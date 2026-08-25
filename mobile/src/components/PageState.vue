<template>
  <div v-if="loading" class="page-state" aria-live="polite">
    <ion-spinner name="crescent" />
    <p>Завантаження...</p>
  </div>
  <div v-else-if="error" class="page-state page-state--error" role="alert">
    <ion-icon :icon="alertCircleOutline" />
    <p>{{ error }}</p>
    <ion-button v-if="retry" fill="outline" size="small" @click="retry">Спробувати ще</ion-button>
  </div>
  <div v-else-if="empty" class="page-state">
    <ion-icon :icon="fileTrayOutline" />
    <p>{{ emptyText }}</p>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { IonButton, IonIcon, IonSpinner } from '@ionic/vue'
import { alertCircleOutline, fileTrayOutline } from 'ionicons/icons'

withDefaults(
  defineProps<{ loading?: boolean; error?: string; empty?: boolean; emptyText?: string; retry?: () => void }>(),
  { emptyText: 'Тут поки немає даних' },
)
</script>
