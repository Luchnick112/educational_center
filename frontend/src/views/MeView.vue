<template>
  <AppShell title="Профіль">
    <div class="panel">
      <div class="panel__title">Акаунт</div>
      <div class="kv">
        <div class="kv__k">Ім'я</div>
        <div class="kv__v">{{ auth.displayName }}</div>
        <div class="kv__k">Роль</div>
        <div class="kv__v">{{ auth.me?.role }}</div>
        <div class="kv__k">Telegram</div>
        <div class="kv__v">{{ auth.me?.telegram_username || '-' }}</div>
        <div class="kv__k">Email</div>
        <div class="kv__v">{{ auth.me?.email || '-' }}</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel__title">Мої посилання</div>
      <div v-if="!auth.me" class="muted">Завантаження...</div>
      <div v-else class="links">
        <RouterLink
          v-for="item in auth.me.my"
          :key="item.key"
          class="linkrow"
          :to="linkTo(item.url)"
        >
          <span class="linkrow__k">{{ item.key }}</span>
          <span class="linkrow__v">{{ item.url }}</span>
        </RouterLink>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import AppShell from '@/components/AppShell.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

function linkTo(url: string) {
  // url is an API path (e.g. "/api/my/lessons/"). Map to an app route where possible.
  if (url.includes('/api/my/lessons/')) return '/my/lessons'
  if (url.includes('/api/my/confirmations/')) return '/my/confirmations'
  if (url.includes('/api/my/payments/')) return '/my/payments'
  if (url.includes('/api/my/children/')) return '/my/children'
  return '/me'
}
</script>
