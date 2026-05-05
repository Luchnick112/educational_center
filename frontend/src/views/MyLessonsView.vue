<template>
  <AppShell title="Мої уроки">
    <div class="panel">
      <div class="panel__title">Останні</div>
      <div v-if="loading" class="muted">Завантаження...</div>
      <DataTable
        v-else
        :columns="columns"
        :rows="rows"
      />
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppShell from '@/components/AppShell.vue'
import DataTable from '@/components/DataTable.vue'
import { apiRequest } from '@/lib/api'

type Lesson = {
  id: number
  status: string
  starts_at: string
  ends_at: string
  topic: string | null
  group: number
}

const loading = ref(true)
const rows = ref<Lesson[]>([])

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'status', label: 'Статус' },
  { key: 'starts_at', label: 'Початок' },
  { key: 'ends_at', label: 'Кінець' },
  { key: 'topic', label: 'Тема', render: (r: Lesson) => r.topic || '-' },
  { key: 'group', label: 'Група' },
]

onMounted(async () => {
  loading.value = true
  try {
    rows.value = await apiRequest<Lesson[]>('/api/my/lessons/')
  } finally {
    loading.value = false
  }
})
</script>
