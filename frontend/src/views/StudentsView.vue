<template>
  <AppShell title="Учні">
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

type Student = {
  id: number
  grade: string | null
  user_detail?: { id: number; first_name: string; last_name: string; telegram_username: string; role: string; phone: string | null }
}

const loading = ref(true)
const rows = ref<Student[]>([])

const columns = [
  { key: 'id', label: 'ID' },
  {
    key: 'name',
    label: "Ім'я",
    render: (r: Student) => {
      const u = r.user_detail
      if (!u) return '-'
      return `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.telegram_username || `User #${u.id}`
    },
  },
  { key: 'grade', label: 'Клас', render: (r: Student) => r.grade || '-' },
  { key: 'telegram', label: 'Telegram', render: (r: Student) => r.user_detail?.telegram_username || '-' },
]

onMounted(async () => {
  loading.value = true
  try {
    rows.value = await apiRequest<Student[]>('/api/users/students/')
  } finally {
    loading.value = false
  }
})
</script>
