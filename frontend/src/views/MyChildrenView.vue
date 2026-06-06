<template>
  <AppShell title="Мої діти">
    <div class="panel">
      <div class="panel__title">Учні</div>
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

type StudentProfile = {
  id: number
  grade: string | null
  notes: string | null
  user_detail?: { first_name: string; last_name: string; telegram_username: string }
}

const loading = ref(true)
const rows = ref<StudentProfile[]>([])

const columns = [
  { key: 'id', label: 'ID' },
  {
    key: 'name',
    label: "Ім'я",
    render: (r: StudentProfile) => {
      const u = r.user_detail
      if (!u) return '-'
      return `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.telegram_username || '-'
    },
  },
  { key: 'grade', label: 'Клас', render: (r: StudentProfile) => r.grade || '-' },
]

onMounted(async () => {
  loading.value = true
  try {
    rows.value = await apiRequest<StudentProfile[]>('/api/my/children/')
  } finally {
    loading.value = false
  }
})
</script>
