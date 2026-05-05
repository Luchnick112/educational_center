<template>
  <AppShell title="Мої платежі">
    <div class="panel">
      <div class="panel__title">Нарахування</div>
      <div v-if="loading" class="muted">Завантаження...</div>
      <DataTable v-else :columns="chargeCols" :rows="data.charges" />
    </div>

    <div class="panel">
      <div class="panel__title">Виплати</div>
      <div v-if="loading" class="muted">Завантаження...</div>
      <DataTable v-else :columns="payoutCols" :rows="data.payouts" />
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppShell from '@/components/AppShell.vue'
import DataTable from '@/components/DataTable.vue'
import { apiRequest } from '@/lib/api'

type Charge = Record<string, any>
type Payout = Record<string, any>

const loading = ref(true)
const data = ref<{ charges: Charge[]; payouts: Payout[] }>({ charges: [], payouts: [] })

const chargeCols = [
  { key: 'id', label: 'ID' },
  { key: 'status', label: 'Статус' },
  { key: 'amount', label: 'Сума' },
  { key: 'issued_at', label: 'Створено' },
]

const payoutCols = [
  { key: 'id', label: 'ID' },
  { key: 'status', label: 'Статус' },
  { key: 'amount', label: 'Сума' },
]

onMounted(async () => {
  loading.value = true
  try {
    data.value = await apiRequest('/api/my/payments/')
  } finally {
    loading.value = false
  }
})
</script>
