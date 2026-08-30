<template>
  <ion-app>
    <ion-router-outlet />
  </ion-app>
</template>

<script setup lang="ts">
import { IonApp, IonRouterOutlet, useBackButton, useIonRouter } from '@ionic/vue'
import { useRoute } from 'vue-router'

const ionRouter = useIonRouter()
const route = useRoute()

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
