<template>
  <AppShell title="Вчителі">
    <div class="panel">
      <div class="panel__title">Список</div>
      <div v-if="loading" class="muted">Завантаження...</div>
      <DataTable v-else :columns="columns" :rows="rows" />
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppShell from '@/components/AppShell.vue'
import DataTable from '@/components/DataTable.vue'
import { apiRequest } from '@/lib/api'

type Teacher = {
  id: number
  hourly_rate: string | number | null
  bio: string | null
  user_detail?: { first_name: string; last_name: string; telegram_username: string }
}

const loading = ref(true)
const rows = ref<Teacher[]>([])

const columns = [
  { key: 'id', label: 'ID' },
  {
    key: 'name',
    label: "Ім'я",
    render: (r: Teacher) => {
      const u = r.user_detail
      if (!u) return '-'
      return `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.telegram_username || '-'
    },
  },
  { key: 'telegram', label: 'Telegram', render: (r: Teacher) => r.user_detail?.telegram_username || '-' },
  { key: 'hourly_rate', label: 'Ставка', render: (r: Teacher) => (r.hourly_rate ?? '-') as any },
]

onMounted(async () => {
  loading.value = true
  try {
    rows.value = await apiRequest<Teacher[]>('/api/users/teachers/')
  } finally {
    loading.value = false
  }
})
</script>
