<template>
  <ion-page>
    <MobileHeader title="Оплати" :refresh="load" :loading="loading" />
    <ion-content :fullscreen="true">
      <div class="page-intro page-intro--compact">
        <p class="eyebrow">Фінанси</p>
        <h1>{{ isTeacher ? 'Мої виплати' : 'Стан оплат' }}</h1>
        <p>Актуальні нарахування та заборгованість.</p>
      </div>
      <div class="page-body">
        <PageState :loading="loading" :error="error" :empty="items.length === 0" :retry="load" empty-text="Фінансових операцій немає">
          <div v-if="summary" class="finance-summary">
            <span>{{ isTeacher ? 'До виплати' : 'До сплати' }}</span>
            <strong>{{ formatMoney(summary.debt_amount) }}</strong>
            <small>{{ summaryName }}</small>
          </div>
          <div class="item-list">
            <article v-for="item in items" :key="item.id" class="data-item finance-item">
              <div class="data-item__main">
                <div class="data-item__topline">
                  <h2>{{ itemName(item) }}</h2>
                  <strong class="money">{{ formatMoney(item.amount) }}</strong>
                </div>
                <p>{{ formatDateTime(item.lesson_starts_at || ('issued_at' in item ? item.issued_at : undefined)) }}</p>
              </div>
              <span class="status" :data-status="item.status">{{ statusLabel(item.status) }}</span>
            </article>
          </div>
        </PageState>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { IonContent, IonPage } from '@ionic/vue'
import MobileHeader from '@/components/MobileHeader.vue'
import PageState from '@/components/PageState.vue'
import { apiRequest } from '@/services/api'
import { usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import type { Charge, PaymentsResponse, Payout, StudentSummary, TeacherSummary } from '@/types/api'
import { formatDateTime, formatMoney, statusLabel } from '@/utils/format'

const auth = useAuthStore()
const data = ref<PaymentsResponse>({})
const { loading, error, run } = usePageData()
const isTeacher = computed(() => auth.me?.role === 'teacher')
const items = computed<Array<Charge | Payout>>(() => (isTeacher.value ? data.value.payouts ?? [] : data.value.charges ?? []))
const summary = computed<StudentSummary | TeacherSummary | undefined>(() =>
  isTeacher.value ? data.value.teacher_summaries?.[0] : data.value.student_summaries?.[0],
)
const summaryName = computed(() => {
  const value = summary.value
  if (!value) return ''
  return 'teacher_name' in value ? value.teacher_name : value.student_name
})
const itemName = (item: Charge | Payout) =>
  'teacher_name' in item ? item.teacher_name || item.student_name || 'Виплата за урок' : item.student_name || 'Оплата за урок'
const load = () => run(async () => { data.value = await apiRequest<PaymentsResponse>('/api/my/payments/') })
onMounted(load)
</script>
