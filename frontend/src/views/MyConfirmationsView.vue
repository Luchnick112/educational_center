<template>
  <AppShell title="Мої підтвердження">
    <div class="panel">
      <div class="panel__title">Останні</div>
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

type Confirmation = {
  id: number
  participant: number
  requested_from: string
  status: string
  requested_at: string
  confirmed_at: string | null
}

const loading = ref(true)
const rows = ref<Confirmation[]>([])

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'status', label: 'Статус' },
  { key: 'requested_from', label: 'Від' },
  { key: 'requested_at', label: 'Запит' },
  { key: 'confirmed_at', label: 'Підтверджено', render: (r: Confirmation) => r.confirmed_at || '-' },
  { key: 'participant', label: 'Учасник' },
]

onMounted(async () => {
  loading.value = true
  try {
    rows.value = await apiRequest<Confirmation[]>('/api/my/confirmations/')
  } finally {
    loading.value = false
  }
})
</script>
