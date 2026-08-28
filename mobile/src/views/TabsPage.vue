<template>
  <ion-page>
    <ion-tabs>
      <ion-router-outlet />
      <ion-tab-bar slot="bottom">
        <ion-tab-button tab="lessons" href="/app/lessons">
          <ion-icon :icon="calendarClearOutline" />
          <ion-label>Уроки</ion-label>
        </ion-tab-button>
        <ion-tab-button v-if="showGroups" tab="groups" href="/app/groups">
          <ion-icon :icon="peopleOutline" />
          <ion-label>Групи</ion-label>
        </ion-tab-button>
        <ion-tab-button v-if="showChildren" tab="children" href="/app/children">
          <ion-icon :icon="schoolOutline" />
          <ion-label>Діти</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="payments" href="/app/payments">
          <ion-icon :icon="walletOutline" />
          <ion-label>Оплати</ion-label>
        </ion-tab-button>
        <ion-tab-button v-if="isAdmin" tab="users" href="/app/users">
          <ion-icon :icon="personAddOutline" />
          <ion-label>Користувачі</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="profile" href="/app/profile">
          <ion-icon :icon="personCircleOutline" />
          <ion-label>Профіль</ion-label>
        </ion-tab-button>
      </ion-tab-bar>
    </ion-tabs>
  </ion-page>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { IonIcon, IonLabel, IonPage, IonRouterOutlet, IonTabBar, IonTabButton, IonTabs } from '@ionic/vue'
import {
  calendarClearOutline,
  peopleOutline,
  personAddOutline,
  personCircleOutline,
  schoolOutline,
  walletOutline,
} from 'ionicons/icons'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const isAdmin = computed(() => Boolean(auth.me?.is_staff || auth.me?.role === 'admin'))
const showGroups = computed(() => auth.me?.role === 'teacher' || auth.me?.role === 'admin' || auth.me?.is_staff)
const showChildren = computed(() => auth.me?.role === 'parent')
</script>
