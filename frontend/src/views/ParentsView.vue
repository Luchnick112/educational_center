<template>
  <AppShell title="Батьки">
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

type Parent = {
  id: number
  billing_notes: string | null
  user_detail?: { first_name: string; last_name: string; telegram_username: string }
}

const loading = ref(true)
const rows = ref<Parent[]>([])

const columns = [
  { key: 'id', label: 'ID' },
  {
    key: 'name',
    label: "Ім'я",
    render: (r: Parent) => {
      const u = r.user_detail
      if (!u) return '-'
      return `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.telegram_username || '-'
    },
  },
  { key: 'telegram', label: 'Telegram', render: (r: Parent) => r.user_detail?.telegram_username || '-' },
  { key: 'billing_notes', label: 'Нотатки', render: (r: Parent) => r.billing_notes || '-' },
]

onMounted(async () => {
  loading.value = true
  try {
    rows.value = await apiRequest<Parent[]>('/api/users/parents/')
  } finally {
    loading.value = false
  }
})
</script>
