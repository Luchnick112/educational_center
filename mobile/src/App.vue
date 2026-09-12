<template>
  <ion-app>
    <ion-router-outlet />
  </ion-app>
</template>

<script setup lang="ts">
import { App as CapacitorApp } from '@capacitor/app'
import type { PluginListenerHandle } from '@capacitor/core'
import { IonApp, IonRouterOutlet, useBackButton, useIonRouter } from '@ionic/vue'
import { onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const ionRouter = useIonRouter()
const route = useRoute()
const router = useRouter()
let resumeListener: PluginListenerHandle | undefined

async function restoreSession() {
  if (auth.isAuthenticated) return
  await auth.bootstrap(true)
  if (auth.isAuthenticated && route.name === 'login') {
    await router.replace({ name: 'lessons' })
  }
}

onMounted(async () => {
  window.addEventListener('online', restoreSession)
  resumeListener = await CapacitorApp.addListener('resume', restoreSession)
})

onBeforeUnmount(() => {
  window.removeEventListener('online', restoreSession)
  void resumeListener?.remove()
})

useBackButton(10, (processNextHandler) => {
  if (ionRouter.canGoBack()) {
    ionRouter.back()
    return
  }

  if (route.path.startsWith('/app/') && route.name !== 'lessons') {
    ionRouter.navigate('/app/lessons', 'back', 'replace')
    return
  }

  processNextHandler()
})
</script>
