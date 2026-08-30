<template>
  <ion-page>
    <MobileHeader
      title="Оплати"
      :refresh="load"
      :loading="loading"
      :action="isAdmin ? openPayment : undefined"
      action-label="Внести оплату"
    />
    <ion-content :fullscreen="true">
      <div class="page-intro page-intro--compact">
        <p class="eyebrow">Фінанси</p>
        <h1>{{ showingTeachers ? 'Виплати викладачам' : 'Оплати учнів' }}</h1>
        <p>Актуальні нарахування та заборгованість.</p>
      </div>
      <div class="page-body">
        <ion-segment v-if="isAdmin" v-model="financeMode" class="finance-mode" value="teachers">
          <ion-segment-button value="students"><ion-label>Учні</ion-label></ion-segment-button>
          <ion-segment-button value="teachers"><ion-label>Викладачі</ion-label></ion-segment-button>
        </ion-segment>

        <section class="filter-panel" aria-label="Фільтри оплат">
          <div class="filter-panel__header">
            <h2>Фільтри</h2>
            <ion-button fill="clear" size="small" :disabled="!hasPaymentFilters || loading" @click="clearPaymentFilters">
              Очистити
            </ion-button>
          </div>
          <form class="filter-grid filter-grid--payments" @submit.prevent="load">
            <label class="mobile-field">
              <span>Від</span>
              <input v-model="paymentFilters.date_from" class="mobile-control" type="date" />
            </label>
            <label class="mobile-field">
              <span>До</span>
              <input v-model="paymentFilters.date_to" class="mobile-control" type="date" />
            </label>
            <label v-if="isAdmin && !showingTeachers" class="mobile-field">
              <span>Учень</span>
              <select v-model="paymentFilters.student" class="mobile-control">
                <option value="">Усі учні</option>
                <option v-for="student in students" :key="student.id" :value="String(student.id)">
                  {{ profileLabel(student, 'Учень') }}
                </option>
              </select>
            </label>
            <label v-if="isAdmin && showingTeachers" class="mobile-field">
              <span>Викладач</span>
              <select v-model="paymentFilters.teacher" class="mobile-control">
                <option value="">Усі викладачі</option>
                <option v-for="teacher in teachers" :key="teacher.id" :value="String(teacher.id)">
                  {{ profileLabel(teacher, 'Викладач') }}
                </option>
              </select>
            </label>
            <ion-button class="filter-submit" type="submit" :disabled="loading">Застосувати</ion-button>
          </form>
        </section>

        <p v-if="notice" class="action-notice">{{ notice }}</p>
        <PageState :loading="loading" :error="error" :empty="items.length === 0 && paymentHistory.length === 0" :retry="load" empty-text="Фінансових операцій немає">
          <div v-if="summaries.length" class="finance-summary">
            <span>{{ showingTeachers ? 'До виплати' : 'До сплати' }}</span>
            <strong>{{ formatMoney(summaryTotal) }}</strong>
            <small>{{ summaryName }}</small>
          </div>

          <section v-if="paymentHistory.length" class="finance-section">
            <h2>{{ showingTeachers ? 'Останні виплати' : 'Останні оплати' }}</h2>
            <div class="item-list">
              <article v-for="payment in paymentHistory" :key="`payment-${payment.id}`" class="data-item finance-item payment-item">
                <div class="data-item__main">
                  <div class="data-item__topline">
                    <h2>{{ paymentName(payment) }}</h2>
                    <strong class="money">{{ formatMoney(payment.amount) }}</strong>
                  </div>
                  <p>{{ formatDateTime(payment.paid_at) }}</p>
                  <p v-if="payment.comment" class="data-item__note">{{ payment.comment }}</p>
                </div>
                <ion-icon :icon="checkmarkCircleOutline" aria-label="Оплачено" />
              </article>
            </div>
          </section>

          <section v-if="items.length" class="finance-section">
            <h2>{{ showingTeachers ? 'Нарахування викладачам' : 'Нарахування учням' }}</h2>
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
          </section>
        </PageState>
      </div>
    </ion-content>

    <ion-modal :is-open="paymentOpen" @didDismiss="closePayment">
      <ion-header class="ion-no-border">
        <ion-toolbar>
          <ion-buttons slot="start"><ion-button @click="closePayment">Скасувати</ion-button></ion-buttons>
          <ion-title>Нова операція</ion-title>
          <ion-buttons slot="end"><ion-button strong :disabled="saving" @click="savePayment">Зберегти</ion-button></ion-buttons>
        </ion-toolbar>
      </ion-header>
      <ion-content>
        <form class="mobile-form" @submit.prevent="savePayment">
          <p v-if="formError" class="form-error form-error--panel">{{ formError }}</p>

          <ion-segment v-model="paymentForm.kind" value="student">
            <ion-segment-button value="student"><ion-label>Від учня</ion-label></ion-segment-button>
            <ion-segment-button value="teacher"><ion-label>Викладачу</ion-label></ion-segment-button>
          </ion-segment>

          <label v-if="paymentForm.kind === 'student'" class="mobile-field">
            <span>Учень</span>
            <select v-model.number="paymentForm.profile" class="mobile-control" required>
              <option :value="null" disabled>Оберіть учня</option>
              <option v-for="student in students" :key="student.id" :value="student.id">{{ profileLabel(student, 'Учень') }}</option>
            </select>
          </label>
          <label v-else class="mobile-field">
            <span>Викладач</span>
            <select v-model.number="paymentForm.profile" class="mobile-control" required>
              <option :value="null" disabled>Оберіть викладача</option>
              <option v-for="teacher in teachers" :key="teacher.id" :value="teacher.id">{{ profileLabel(teacher, 'Викладач') }}</option>
            </select>
          </label>

          <div class="mobile-form-grid">
            <label class="mobile-field">
              <span>Сума</span>
              <input v-model="paymentForm.amount" class="mobile-control" type="number" min="0.01" step="0.01" required />
            </label>
            <label class="mobile-field">
              <span>Дата</span>
              <input v-model="paymentForm.paid_at" class="mobile-control" type="date" required />
            </label>
          </div>

          <label class="mobile-field">
            <span>Коментар</span>
            <textarea v-model="paymentForm.comment" class="mobile-control" placeholder="Необов’язково" />
          </label>

          <ion-button class="mobile-submit" expand="block" type="submit" :disabled="saving">
            <ion-spinner v-if="saving" name="crescent" />
            <span v-else>Зберегти операцію</span>
          </ion-button>
        </form>
      </ion-content>
    </ion-modal>
  </ion-page>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  IonButton,
  IonButtons,
  IonContent,
  IonHeader,
  IonIcon,
  IonLabel,
  IonModal,
  IonPage,
  IonSegment,
  IonSegmentButton,
  IonSpinner,
  IonTitle,
  IonToolbar,
} from '@ionic/vue'
import { checkmarkCircleOutline } from 'ionicons/icons'
import MobileHeader from '@/components/MobileHeader.vue'
import PageState from '@/components/PageState.vue'
import { ApiError, apiRequest, errorMessage } from '@/services/api'
import { usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import type {
  Charge,
  PaymentsResponse,
  Payout,
  ProfileOption,
  StudentPayment,
  StudentSummary,
  TeacherPayment,
  TeacherSummary,
} from '@/types/api'
import { formatDateTime, formatMoney, statusLabel } from '@/utils/format'

const auth = useAuthStore()
const data = ref<PaymentsResponse>({})
const students = ref<ProfileOption[]>([])
const teachers = ref<ProfileOption[]>([])
const financeMode = ref<'students' | 'teachers'>('teachers')
const paymentOpen = ref(false)
const saving = ref(false)
const formError = ref('')
const notice = ref('')
const { loading, error, run } = usePageData()

const paymentFilters = reactive({
  date_from: '',
  date_to: '',
  student: '',
  teacher: '',
})

const isTeacher = computed(() => auth.me?.role === 'teacher')
const isAdmin = computed(() => Boolean(auth.me?.is_staff || auth.me?.role === 'admin'))
const showingTeachers = computed(() => isTeacher.value || (isAdmin.value && financeMode.value === 'teachers'))
const items = computed<Array<Charge | Payout>>(() => showingTeachers.value ? data.value.payouts ?? [] : data.value.charges ?? [])
const summaries = computed<Array<StudentSummary | TeacherSummary>>(() =>
  showingTeachers.value ? data.value.teacher_summaries ?? [] : data.value.student_summaries ?? [],
)
const paymentHistory = computed<Array<StudentPayment | TeacherPayment>>(() =>
  showingTeachers.value ? data.value.teacher_payments ?? [] : data.value.student_payments ?? [],
)
const summaryTotal = computed(() => summaries.value.reduce((total, row) => total + Number(row.debt_amount || 0), 0))
const summaryName = computed(() => summaries.value.length === 1
  ? ('teacher_name' in summaries.value[0] ? summaries.value[0].teacher_name : summaries.value[0].student_name)
  : showingTeachers.value ? `${summaries.value.length} викладачів` : `${summaries.value.length} учнів`)
const hasPaymentFilters = computed(() => Object.values(paymentFilters).some(Boolean))

const paymentForm = reactive({
  kind: 'student' as 'student' | 'teacher',
  profile: null as number | null,
  amount: '',
  paid_at: today(),
  comment: '',
})

const itemName = (item: Charge | Payout) =>
  'teacher_name' in item ? item.teacher_name || item.student_name || 'Виплата за урок' : item.student_name || 'Оплата за урок'

function paymentName(payment: StudentPayment | TeacherPayment) {
  return 'teacher' in payment
    ? payment.teacher_name || `Викладач #${payment.teacher}`
    : payment.student_name || `Учень #${payment.student}`
}

function profileLabel(profile: ProfileOption, fallback: string) {
  const user = profile.user_detail
  if (!user) return `${fallback} #${profile.id}`
  return [user.first_name, user.last_name].filter(Boolean).join(' ')
    || user.telegram_username
    || user.email
    || `${fallback} #${profile.id}`
}

function today() {
  const date = new Date()
  const pad = (part: number) => String(part).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function paymentsPath() {
  const params = new URLSearchParams()
  if (paymentFilters.date_from) params.set('date_from', paymentFilters.date_from)
  if (paymentFilters.date_to) params.set('date_to', paymentFilters.date_to)
  if (isAdmin.value && !showingTeachers.value && paymentFilters.student) {
    params.set('student', paymentFilters.student)
  }
  if (isAdmin.value && showingTeachers.value && paymentFilters.teacher) {
    params.set('teacher', paymentFilters.teacher)
  }
  const query = params.toString()
  return `/api/my/payments/${query ? `?${query}` : ''}`
}

const load = () => run(async () => {
  const [payments, studentRows, teacherRows] = await Promise.all([
    apiRequest<PaymentsResponse>(paymentsPath()),
    isAdmin.value ? apiRequest<ProfileOption[]>('/api/users/students/') : Promise.resolve([]),
    isAdmin.value ? apiRequest<ProfileOption[]>('/api/users/teachers/') : Promise.resolve([]),
  ])
  data.value = payments
  students.value = studentRows
  teachers.value = teacherRows
})

async function clearPaymentFilters() {
  Object.assign(paymentFilters, { date_from: '', date_to: '', student: '', teacher: '' })
  await load()
}

function openPayment() {
  paymentForm.kind = financeMode.value === 'teachers' ? 'teacher' : 'student'
  paymentForm.profile = paymentForm.kind === 'teacher' ? teachers.value[0]?.id ?? null : students.value[0]?.id ?? null
  paymentForm.amount = ''
  paymentForm.paid_at = today()
  paymentForm.comment = ''
  formError.value = ''
  paymentOpen.value = true
}

function closePayment() {
  if (saving.value) return
  paymentOpen.value = false
  formError.value = ''
}

watch(() => paymentForm.kind, (kind) => {
  paymentForm.profile = kind === 'teacher' ? teachers.value[0]?.id ?? null : students.value[0]?.id ?? null
})

async function savePayment() {
  if (!paymentForm.profile || Number(paymentForm.amount) <= 0) {
    formError.value = 'Оберіть отримувача та вкажіть суму більше нуля.'
    return
  }
  saving.value = true
  formError.value = ''
  try {
    const isTeacherPayment = paymentForm.kind === 'teacher'
    await apiRequest(isTeacherPayment ? '/api/finance/teacher-payments/' : '/api/finance/student-payments/', {
      method: 'POST',
      body: {
        [isTeacherPayment ? 'teacher' : 'student']: paymentForm.profile,
        amount: paymentForm.amount,
        paid_at: paymentForm.paid_at,
        comment: paymentForm.comment,
      },
    })
    financeMode.value = isTeacherPayment ? 'teachers' : 'students'
    paymentOpen.value = false
    notice.value = isTeacherPayment ? 'Виплату викладачу внесено.' : 'Оплату учня внесено.'
    await load()
  } catch (caught) {
    formError.value = caught instanceof ApiError
      ? errorMessage(caught.payload, 'Не вдалося зберегти оплату')
      : 'Не вдалося зберегти оплату'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
