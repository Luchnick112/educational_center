<template>
  <AppShell title="Панель">
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
      <div class="panel__title">Статистика</div>
      <div v-if="loading" class="muted">Завантаження...</div>
      <div v-else class="cards">
        <div v-for="(v, k) in stats" :key="k" class="card">
          <div class="card__k">{{ k }}</div>
          <div class="card__v">{{ v }}</div>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppShell from '@/components/AppShell.vue'
import { useAuthStore } from '@/stores/auth'
import { apiRequest } from '@/lib/api'

const auth = useAuthStore()
const loading = ref(true)
const stats = ref<Record<string, number>>({})

type DashboardResponse = { user: any; role: string; stats: Record<string, number> }
const dashboardUrl = computed(() => '/api/users/dashboard/')

onMounted(async () => {
  loading.value = true
  try {
    const res = await apiRequest<DashboardResponse>(dashboardUrl.value)
    stats.value = res.stats ?? {}
  } finally {
    loading.value = false
  }
})
</script>
