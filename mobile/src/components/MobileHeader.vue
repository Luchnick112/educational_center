<template>
  <ion-header class="ion-no-border">
    <ion-toolbar>
      <ion-title>{{ title }}</ion-title>
      <ion-buttons slot="end">
        <ion-button v-if="refresh" aria-label="Оновити" :disabled="loading" @click="refresh">
          <ion-icon slot="icon-only" :icon="refreshOutline" />
        </ion-button>
        <ion-button v-if="action" :aria-label="actionLabel" :disabled="loading" @click="action">
          <ion-icon slot="icon-only" :icon="addOutline" />
        </ion-button>
      </ion-buttons>
    </ion-toolbar>
  </ion-header>
</template>

<script setup lang="ts">
import { IonButton, IonButtons, IonHeader, IonIcon, IonTitle, IonToolbar } from '@ionic/vue'
import { addOutline, refreshOutline } from 'ionicons/icons'

defineProps<{
  title: string
  refresh?: () => void | Promise<void>
  loading?: boolean
  action?: () => void | Promise<void>
  actionLabel?: string
}>()
</script>
