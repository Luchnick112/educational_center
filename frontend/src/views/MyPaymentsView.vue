<template>
  <AppShell :title="isAdmin ? 'Платежі' : 'Мої платежі'">
    <div class="panel filters-panel">
      <div class="panel__title">Період</div>
      <form class="filters" @submit.prevent="loadPayments">
        <label class="field">
          <span class="field__label">Від</span>
          <input class="input" type="date" v-model="filters.date_from" />
        </label>
        <label class="field">
          <span class="field__label">До</span>
          <input class="input" type="date" v-model="filters.date_to" />
        </label>
        <label v-if="isAdmin && activeTab === 'students'" class="field">
          <span class="field__label">Учень</span>
          <select class="input" v-model="filters.student">
            <option value="">Всі учні</option>
            <option v-for="student in students" :key="student.id" :value="String(student.id)">
              {{ profileLabel(student) }}
            </option>
          </select>
        </label>
        <label v-if="isAdmin && activeTab === 'teachers'" class="field">
          <span class="field__label">Викладач</span>
          <select class="input" v-model="filters.teacher">
            <option value="">Всі викладачі</option>
            <option v-for="teacher in teachers" :key="teacher.id" :value="String(teacher.id)">
              {{ profileLabel(teacher) }}
            </option>
          </select>
        </label>
        <button class="btn" type="submit" :disabled="loading">Оновити</button>
        <button class="btn btn--ghost" type="button" :disabled="loading" @click="clearFilters">Скинути</button>
      </form>
      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <template v-if="isAdmin">
      <div class="tabs" role="tablist" aria-label="Розрахунки">
        <button
          class="tab"
          :class="{ 'tab--active': activeTab === 'students' }"
          type="button"
          @click="setActiveTab('students')"
        >
          Учні
        </button>
        <button
          class="tab"
          :class="{ 'tab--active': activeTab === 'teachers' }"
          type="button"
          @click="setActiveTab('teachers')"
        >
          Викладачі
        </button>
      </div>

      <div v-if="activeTab === 'students'" class="admin-grid">
        <div class="panel">
          <div class="panel__title">Внести оплату учня</div>
          <form class="payment-form" @submit.prevent="submitStudentPayment">
            <label class="field">
              <span class="field__label">Учень</span>
              <select class="input" v-model="studentPaymentForm.student" required>
                <option value="">Оберіть учня</option>
                <option v-for="student in students" :key="student.id" :value="String(student.id)">
                  {{ profileLabel(student) }}
                </option>
              </select>
            </label>
            <label class="field">
              <span class="field__label">Дата</span>
              <input class="input" type="date" v-model="studentPaymentForm.paid_at" required />
            </label>
            <label class="field">
              <span class="field__label">Сума</span>
              <input class="input" type="number" step="0.01" min="0.01" v-model="studentPaymentForm.amount" required />
            </label>
            <label class="field">
              <span class="field__label">Коментар</span>
              <input class="input" v-model.trim="studentPaymentForm.comment" />
            </label>
            <button class="btn" type="submit" :disabled="savingPayment">
              {{ savingPayment ? 'Збереження...' : 'Внести оплату' }}
            </button>
          </form>
        </div>

        <div class="panel">
          <div class="panel__title">Стан розрахунків по учнях</div>
          <div class="summary-strip">
            <div>
              <span>Нараховано</span>
              <strong>{{ money(studentTotals.charged) }}</strong>
            </div>
            <div>
              <span>Оплачено</span>
              <strong>{{ money(studentTotals.paid) }}</strong>
            </div>
            <div>
              <span>Борг</span>
              <strong>{{ money(studentTotals.debt) }}</strong>
            </div>
          </div>
          <div v-if="loading" class="muted">Завантаження...</div>
          <DataTable v-else :columns="studentSummaryCols" :rows="studentSummaryRows" />
        </div>

        <div class="panel">
          <div class="panel__title">Нарахування та оплати</div>
          <div v-if="loading" class="muted">Завантаження...</div>
          <DataTable v-else :columns="chargeCols" :rows="allocatedStudentCharges" />
        </div>

        <div class="panel">
          <div class="panel__title">Внесені оплати учнів</div>
          <div v-if="loading" class="muted">Завантаження...</div>
          <DataTable v-else :columns="studentPaymentCols" :rows="data.student_payments" />
        </div>
      </div>

      <div v-else class="admin-grid">
        <div class="panel">
          <div class="panel__title">Внести оплату викладачу</div>
          <form class="payment-form" @submit.prevent="submitTeacherPayment">
            <label class="field">
              <span class="field__label">Викладач</span>
              <select class="input" v-model="teacherPaymentForm.teacher" required>
                <option value="">Оберіть викладача</option>
                <option v-for="teacher in teachers" :key="teacher.id" :value="String(teacher.id)">
                  {{ profileLabel(teacher) }}
                </option>
              </select>
            </label>
            <label class="field">
              <span class="field__label">Дата</span>
              <input class="input" type="date" v-model="teacherPaymentForm.paid_at" required />
            </label>
            <label class="field">
              <span class="field__label">Сума</span>
              <input class="input" type="number" step="0.01" min="0.01" v-model="teacherPaymentForm.amount" required />
            </label>
            <label class="field">
              <span class="field__label">Коментар</span>
              <input class="input" v-model.trim="teacherPaymentForm.comment" />
            </label>
            <button class="btn" type="submit" :disabled="savingPayment">
              {{ savingPayment ? 'Збереження...' : 'Внести оплату' }}
            </button>
          </form>
        </div>

        <div class="panel">
          <div class="panel__title">Стан розрахунків по викладачах</div>
          <div class="summary-strip">
            <div>
              <span>Нараховано</span>
              <strong>{{ money(teacherTotals.accrued) }}</strong>
            </div>
            <div>
              <span>Виплачено</span>
              <strong>{{ money(teacherTotals.paid) }}</strong>
            </div>
            <div>
              <span>До виплати</span>
              <strong>{{ money(teacherTotals.debt) }}</strong>
            </div>
          </div>
          <div v-if="loading" class="muted">Завантаження...</div>
          <DataTable v-else :columns="teacherSummaryCols" :rows="data.teacher_summaries" />
        </div>

        <div class="panel">
          <div class="panel__title">Виплати викладачам</div>
          <div v-if="loading" class="muted">Завантаження...</div>
          <DataTable
            v-else
            :columns="teacherLessonPayoutCols"
            :rows="teacherLessonPayouts"
            :row-key="(row) => row.key"
            :on-row-click="selectTeacherLessonPayout"
          />
        </div>

        <div v-if="selectedTeacherLessonPayout" class="panel">
          <div class="panel__title">Деталізація уроку #{{ selectedTeacherLessonPayout.lesson }}</div>
          <div class="detail-meta">
            <div>{{ selectedTeacherLessonPayout.teacher_name }}</div>
            <div>{{ dateLabel(selectedTeacherLessonPayout.lesson_starts_at) }}</div>
            <div>Сума: {{ money(selectedTeacherLessonPayout.amount_total) }}</div>
          </div>
          <DataTable :columns="payoutDetailCols" :rows="selectedTeacherLessonPayout.details" />
        </div>

        <div class="panel">
          <div class="panel__title">Внесені оплати викладачам</div>
          <div v-if="loading" class="muted">Завантаження...</div>
          <DataTable v-else :columns="teacherPaymentCols" :rows="data.teacher_payments" />
        </div>
      </div>
    </template>

    <template v-else>
      <div v-if="!isTeacher" class="panel">
        <div class="panel__title">Нарахування</div>
        <div v-if="loading" class="muted">Завантаження...</div>
        <DataTable v-else :columns="chargeCols" :rows="allocatedStudentCharges" />
      </div>

      <div v-if="!isTeacher" class="panel">
        <div class="panel__title">Внесені оплати</div>
        <div v-if="loading" class="muted">Завантаження...</div>
        <DataTable v-else :columns="studentPaymentCols" :rows="data.student_payments" />
      </div>

      <div v-if="isTeacher" class="panel">
        <div class="panel__title">Виплати</div>
        <div v-if="loading" class="muted">Завантаження...</div>
        <DataTable v-else :columns="payoutCols" :rows="data.payouts" />
      </div>

      <div v-if="isTeacher" class="panel">
        <div class="panel__title">Виплачено мені</div>
        <div class="summary-strip">
          <div>
            <span>Всього виплачено</span>
            <strong>{{ money(myTeacherPaymentTotal) }}</strong>
          </div>
        </div>
        <div v-if="loading" class="muted">Завантаження...</div>
        <DataTable v-else :columns="teacherPaymentCols" :rows="data.teacher_payments" />
      </div>
    </template>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import AppShell from '@/components/AppShell.vue'
import DataTable from '@/components/DataTable.vue'
import { apiRequest } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

type Charge = {
  id: number
  student?: number
  status: string
  amount: string
  student_name?: string
  parent_name?: string
  lesson_starts_at?: string
  issued_at?: string
  paid_at?: string | null
}

type Payout = {
  id: number
  lesson?: number
  participant?: number
  teacher?: number
  status: string
  amount: string
  student_name?: string
  teacher_name?: string
  lesson_starts_at?: string
  approved_at?: string | null
  paid_at?: string | null
}

type TeacherLessonPayout = {
  key: string
  lesson: number | string
  teacher_name: string
  lesson_starts_at?: string
  status: string
  amount_total: number
  paid_amount: number
  debt_amount: number
  payout_count: number
  details: Payout[]
}

type StudentSummary = {
  student: number
  student_name: string
  charged_amount: string
  paid_amount: string
  debt_amount: string
  charge_count: number
  paid_count: number
  debt_count: number
}

type TeacherSummary = {
  teacher: number
  teacher_name: string
  accrued_amount: string
  paid_amount: string
  debt_amount: string
  payout_count: number
  paid_count: number
  debt_count: number
}

type StudentPayment = {
  id: number
  student: number
  student_name?: string
  amount: string
  paid_at: string
  comment?: string
}

type TeacherPayment = {
  id: number
  teacher: number
  teacher_name?: string
  amount: string
  paid_at: string
  comment?: string
}

type ProfileOption = {
  id: number
  user_detail?: {
    id?: number
    first_name?: string
    last_name?: string
    telegram_username?: string
    email?: string
  }
}

type PaymentsData = {
  charges: Charge[]
  payouts: Payout[]
  student_payments: StudentPayment[]
  teacher_payments: TeacherPayment[]
  student_summaries: StudentSummary[]
  teacher_summaries: TeacherSummary[]
}

const auth = useAuthStore()
const loading = ref(true)
const savingPayment = ref(false)
const error = ref<string | null>(null)
const activeTab = ref<'students' | 'teachers'>('students')
const selectedTeacherLessonPayout = ref<TeacherLessonPayout | null>(null)
const filters = reactive({ date_from: '', date_to: '', student: '', teacher: '' })
const data = ref<PaymentsData>({
  charges: [],
  payouts: [],
  student_payments: [],
  teacher_payments: [],
  student_summaries: [],
  teacher_summaries: [],
})
const students = ref<ProfileOption[]>([])
const teachers = ref<ProfileOption[]>([])
const studentPaymentForm = reactive({ student: '', paid_at: today(), amount: '', comment: '' })
const teacherPaymentForm = reactive({ teacher: '', paid_at: today(), amount: '', comment: '' })

const isAdmin = computed(() => !!auth.me && (auth.me.is_staff || auth.me.role === 'admin'))
const isTeacher = computed(() => auth.me?.role === 'teacher')

const studentSummaryRows = computed<StudentSummary[]>(() => {
  if (!data.value.charges.length && !data.value.student_payments.length) {
    return data.value.student_summaries
  }

  type StudentAccumulator = {
    student: number
    student_name: string
    charged: number
    paid: number
    charges: Array<{ id: number; amount: number; lesson_starts_at?: string }>
  }

  const rows = new Map<number, StudentAccumulator>()
  const ensureRow = (student: number, studentName?: string) => {
    const existing = rows.get(student)
    if (existing) {
      if (!existing.student_name && studentName) existing.student_name = studentName
      return existing
    }
    const row = {
      student,
      student_name: studentName || `#${student}`,
      charged: 0,
      paid: 0,
      charges: [],
    }
    rows.set(student, row)
    return row
  }

  for (const charge of data.value.charges) {
    if (!charge.student || charge.status === 'cancelled') continue
    const row = ensureRow(charge.student, charge.student_name)
    const amount = Number(charge.amount || 0)
    row.charged += amount
    row.charges.push({ id: charge.id, amount, lesson_starts_at: charge.lesson_starts_at })
  }

  for (const payment of data.value.student_payments) {
    if (!payment.student) continue
    const row = ensureRow(payment.student, payment.student_name)
    row.paid += Number(payment.amount || 0)
  }

  return Array.from(rows.values())
    .map((row) => {
      let remainingPaid = row.paid
      let paidCount = 0
      let debtCount = 0
      for (const charge of [...row.charges].sort((a, b) => {
        const aTime = a.lesson_starts_at ? new Date(a.lesson_starts_at).getTime() : 0
        const bTime = b.lesson_starts_at ? new Date(b.lesson_starts_at).getTime() : 0
        return aTime - bTime || a.id - b.id
      })) {
        if (remainingPaid >= charge.amount) {
          paidCount += 1
          remainingPaid -= charge.amount
        } else {
          debtCount += 1
          remainingPaid = 0
        }
      }

      return {
        student: row.student,
        student_name: row.student_name,
        charged_amount: row.charged.toFixed(2),
        paid_amount: row.paid.toFixed(2),
        debt_amount: Math.max(row.charged - row.paid, 0).toFixed(2),
        charge_count: row.charges.length,
        paid_count: paidCount,
        debt_count: debtCount,
      }
    })
    .sort((a, b) => Number(b.debt_amount) - Number(a.debt_amount) || a.student_name.localeCompare(b.student_name))
})

const studentTotals = computed(() =>
  studentSummaryRows.value.reduce(
    (acc, row) => ({
      charged: acc.charged + Number(row.charged_amount || 0),
      paid: acc.paid + Number(row.paid_amount || 0),
      debt: acc.debt + Number(row.debt_amount || 0),
    }),
    { charged: 0, paid: 0, debt: 0 },
  ),
)

const allocatedStudentCharges = computed<Charge[]>(() => {
  const paymentsByStudent = new Map<number, Array<{ remaining: number; paid_at: string }>>()
  for (const payment of data.value.student_payments) {
    const list = paymentsByStudent.get(payment.student) || []
    list.push({ remaining: Number(payment.amount || 0), paid_at: payment.paid_at })
    paymentsByStudent.set(payment.student, list)
  }
  for (const payments of paymentsByStudent.values()) {
    payments.sort((a, b) => a.paid_at.localeCompare(b.paid_at))
  }

  return [...data.value.charges]
    .sort((a, b) => {
      const aTime = a.lesson_starts_at ? new Date(a.lesson_starts_at).getTime() : 0
      const bTime = b.lesson_starts_at ? new Date(b.lesson_starts_at).getTime() : 0
      return aTime - bTime || a.id - b.id
    })
    .map((charge) => {
      const student = charge.student
      if (!student || charge.status === 'cancelled') return charge
      const payments = paymentsByStudent.get(student) || []
      let remainingCharge = Number(charge.amount || 0)
      let paid = 0
      let paidAt: string | null = null

      for (const payment of payments) {
        if (remainingCharge <= 0) break
        if (payment.remaining <= 0) continue
        const applied = Math.min(payment.remaining, remainingCharge)
        payment.remaining -= applied
        remainingCharge -= applied
        paid += applied
        paidAt = payment.paid_at
      }

      return {
        ...charge,
        status: paid >= Number(charge.amount || 0) ? 'paid' : paid > 0 ? 'partial' : charge.status,
        paid_at: paidAt || charge.paid_at || null,
      }
    })
    .sort((a, b) => b.id - a.id)
})

const teacherTotals = computed(() =>
  data.value.teacher_summaries.reduce(
    (acc, row) => ({
      accrued: acc.accrued + Number(row.accrued_amount || 0),
      paid: acc.paid + Number(row.paid_amount || 0),
      debt: acc.debt + Number(row.debt_amount || 0),
    }),
    { accrued: 0, paid: 0, debt: 0 },
  ),
)

const myTeacherPaymentTotal = computed(() =>
  data.value.teacher_payments.reduce((total, payment) => total + Number(payment.amount || 0), 0),
)

const allocatedTeacherPayouts = computed<Payout[]>(() => {
  const paymentsByTeacher = new Map<number, Array<{ remaining: number; paid_at: string }>>()
  for (const payment of data.value.teacher_payments) {
    const list = paymentsByTeacher.get(payment.teacher) || []
    list.push({ remaining: Number(payment.amount || 0), paid_at: payment.paid_at })
    paymentsByTeacher.set(payment.teacher, list)
  }
  for (const payments of paymentsByTeacher.values()) {
    payments.sort((a, b) => a.paid_at.localeCompare(b.paid_at))
  }

  return [...data.value.payouts]
    .sort((a, b) => {
      const aTime = a.lesson_starts_at ? new Date(a.lesson_starts_at).getTime() : 0
      const bTime = b.lesson_starts_at ? new Date(b.lesson_starts_at).getTime() : 0
      return aTime - bTime || a.id - b.id
    })
    .map((payout) => {
      const teacher = payout.teacher
      if (!teacher) return payout
      const payments = paymentsByTeacher.get(teacher) || []
      let remainingPayout = Number(payout.amount || 0)
      let paid = 0
      let paidAt: string | null = null

      for (const payment of payments) {
        if (remainingPayout <= 0) break
        if (payment.remaining <= 0) continue
        const applied = Math.min(payment.remaining, remainingPayout)
        payment.remaining -= applied
        remainingPayout -= applied
        paid += applied
        paidAt = payment.paid_at
      }

      return {
        ...payout,
        status: paid >= Number(payout.amount || 0) ? 'paid' : paid > 0 ? 'partial' : 'draft',
        paid_at: paidAt || null,
      }
    })
})

const teacherLessonPayouts = computed<TeacherLessonPayout[]>(() => {
  const groups = new Map<string, TeacherLessonPayout>()

  for (const payout of allocatedTeacherPayouts.value) {
    const lesson = payout.lesson ?? `participant:${payout.participant ?? payout.id}`
    const key = String(lesson)
    const group = groups.get(key) || {
      key,
      lesson,
      teacher_name: payout.teacher_name || '-',
      lesson_starts_at: payout.lesson_starts_at,
      status: '',
      amount_total: 0,
      paid_amount: 0,
      debt_amount: 0,
      payout_count: 0,
      details: [],
    }
    const amount = Number(payout.amount || 0)
    if (payout.status !== 'cancelled') {
      group.amount_total += amount
      if (payout.status === 'paid') group.paid_amount += amount
      else group.debt_amount += amount
      group.payout_count += 1
    }
    group.details.push(payout)
    group.status = lessonPayoutStatus(group.details)
    groups.set(key, group)
  }

  return Array.from(groups.values()).sort((a, b) => {
    const aTime = a.lesson_starts_at ? new Date(a.lesson_starts_at).getTime() : 0
    const bTime = b.lesson_starts_at ? new Date(b.lesson_starts_at).getTime() : 0
    return bTime - aTime
  })
})

const studentSummaryCols = [
  { key: 'student_name', label: 'Учень' },
  { key: 'charged_amount', label: 'Нараховано', render: (r: StudentSummary) => money(r.charged_amount) },
  { key: 'paid_amount', label: 'Оплачено', render: (r: StudentSummary) => money(r.paid_amount) },
  { key: 'debt_amount', label: 'Борг', render: (r: StudentSummary) => money(r.debt_amount) },
  { key: 'debt_count', label: 'Неоплачені' },
]

const teacherSummaryCols = [
  { key: 'teacher_name', label: 'Викладач' },
  { key: 'accrued_amount', label: 'Нараховано', render: (r: TeacherSummary) => money(r.accrued_amount) },
  { key: 'paid_amount', label: 'Виплачено', render: (r: TeacherSummary) => money(r.paid_amount) },
  { key: 'debt_amount', label: 'До виплати', render: (r: TeacherSummary) => money(r.debt_amount) },
  { key: 'debt_count', label: 'Невиплачені' },
]

const chargeCols = [
  { key: 'id', label: 'ID' },
  { key: 'student_name', label: 'Учень', render: (r: Charge) => r.student_name || '-' },
  { key: 'parent_name', label: 'Платник', render: (r: Charge) => r.parent_name || '-' },
  { key: 'status', label: 'Статус', render: (r: Charge) => chargeStatusLabel(r.status) },
  { key: 'amount', label: 'Сума', render: (r: Charge) => money(r.amount) },
  { key: 'lesson_starts_at', label: 'Урок', render: (r: Charge) => dateLabel(r.lesson_starts_at) },
  { key: 'paid_at', label: 'Оплачено', render: (r: Charge) => dateLabel(r.paid_at) },
]

const payoutCols = [
  { key: 'id', label: 'ID' },
  { key: 'teacher_name', label: 'Викладач', render: (r: Payout) => r.teacher_name || '-' },
  { key: 'status', label: 'Статус', render: (r: Payout) => payoutStatusLabel(r.status) },
  { key: 'amount', label: 'Сума', render: (r: Payout) => money(r.amount) },
  { key: 'lesson_starts_at', label: 'Урок', render: (r: Payout) => dateLabel(r.lesson_starts_at) },
  { key: 'paid_at', label: 'Виплачено', render: (r: Payout) => dateLabel(r.paid_at) },
]

const teacherLessonPayoutCols = [
  { key: 'lesson', label: 'Урок' },
  { key: 'lesson_starts_at', label: 'Дата', render: (r: TeacherLessonPayout) => dateLabel(r.lesson_starts_at) },
  { key: 'teacher_name', label: 'Викладач' },
  { key: 'status', label: 'Статус', render: (r: TeacherLessonPayout) => r.status },
  { key: 'amount_total', label: 'Сума', render: (r: TeacherLessonPayout) => money(r.amount_total) },
  { key: 'paid_amount', label: 'Виплачено', render: (r: TeacherLessonPayout) => money(r.paid_amount) },
  { key: 'debt_amount', label: 'До виплати', render: (r: TeacherLessonPayout) => money(r.debt_amount) },
  { key: 'payout_count', label: 'Учасників' },
]

const payoutDetailCols = [
  { key: 'student_name', label: 'Учень', render: (r: Payout) => r.student_name || '-' },
  { key: 'status', label: 'Статус', render: (r: Payout) => payoutStatusLabel(r.status) },
  { key: 'amount', label: 'Сума', render: (r: Payout) => money(r.amount) },
  { key: 'paid_at', label: 'Виплачено', render: (r: Payout) => dateLabel(r.paid_at) },
]

const studentPaymentCols = [
  { key: 'paid_at', label: 'Дата', render: (r: StudentPayment) => dateOnlyLabel(r.paid_at) },
  { key: 'student_name', label: 'Учень', render: (r: StudentPayment) => r.student_name || '-' },
  { key: 'amount', label: 'Сума', render: (r: StudentPayment) => money(r.amount) },
  { key: 'comment', label: 'Коментар', render: (r: StudentPayment) => r.comment || '-' },
]

const teacherPaymentCols = [
  { key: 'paid_at', label: 'Дата', render: (r: TeacherPayment) => dateOnlyLabel(r.paid_at) },
  { key: 'teacher_name', label: 'Викладач', render: (r: TeacherPayment) => r.teacher_name || '-' },
  { key: 'amount', label: 'Сума', render: (r: TeacherPayment) => money(r.amount) },
  { key: 'comment', label: 'Коментар', render: (r: TeacherPayment) => r.comment || '-' },
]

function paymentsPath() {
  const params = new URLSearchParams()
  if (filters.date_from) params.set('date_from', filters.date_from)
  if (filters.date_to) params.set('date_to', filters.date_to)
  if (activeTab.value === 'students' && filters.student) params.set('student', filters.student)
  if (activeTab.value === 'teachers' && filters.teacher) params.set('teacher', filters.teacher)
  const query = params.toString()
  return `/api/my/payments/${query ? `?${query}` : ''}`
}

async function loadLookups() {
  if (!isAdmin.value) return
  try {
    const [studentRows, teacherRows] = await Promise.all([
      apiRequest<ProfileOption[]>('/api/users/students/'),
      apiRequest<ProfileOption[]>('/api/users/teachers/'),
    ])
    students.value = studentRows
    teachers.value = teacherRows
  } catch (e: any) {
    error.value = permissionAwareError(e)
  }
}

async function loadPayments() {
  loading.value = true
  error.value = null
  try {
    const payload = await apiRequest<Partial<PaymentsData>>(paymentsPath())
    data.value = {
      charges: payload.charges || [],
      payouts: payload.payouts || [],
      student_payments: payload.student_payments || [],
      teacher_payments: payload.teacher_payments || [],
      student_summaries: payload.student_summaries || [],
      teacher_summaries: payload.teacher_summaries || [],
    }
    selectedTeacherLessonPayout.value = null
  } catch (e: any) {
    error.value = permissionAwareError(e)
  } finally {
    loading.value = false
  }
}

async function submitStudentPayment() {
  savingPayment.value = true
  error.value = null
  try {
    await apiRequest('/api/finance/student-payments/', {
      method: 'POST',
      body: {
        student: Number(studentPaymentForm.student),
        amount: studentPaymentForm.amount,
        paid_at: studentPaymentForm.paid_at,
        comment: studentPaymentForm.comment,
      },
    })
    filters.student = studentPaymentForm.student
    studentPaymentForm.amount = ''
    studentPaymentForm.comment = ''
    await loadPayments()
  } catch (e: any) {
    error.value = paymentError(e)
  } finally {
    savingPayment.value = false
  }
}

async function submitTeacherPayment() {
  savingPayment.value = true
  error.value = null
  try {
    await apiRequest('/api/finance/teacher-payments/', {
      method: 'POST',
      body: {
        teacher: Number(teacherPaymentForm.teacher),
        amount: teacherPaymentForm.amount,
        paid_at: teacherPaymentForm.paid_at,
        comment: teacherPaymentForm.comment,
      },
    })
    filters.teacher = teacherPaymentForm.teacher
    teacherPaymentForm.amount = ''
    teacherPaymentForm.comment = ''
    await loadPayments()
  } catch (e: any) {
    error.value = paymentError(e)
  } finally {
    savingPayment.value = false
  }
}

function selectTeacherLessonPayout(row: TeacherLessonPayout) {
  selectedTeacherLessonPayout.value = row
}

function setActiveTab(tab: 'students' | 'teachers') {
  if (activeTab.value === tab) return
  activeTab.value = tab
  selectedTeacherLessonPayout.value = null
  loadPayments()
}

function clearFilters() {
  filters.date_from = ''
  filters.date_to = ''
  filters.student = ''
  filters.teacher = ''
  loadPayments()
}

function money(value: string | number | null | undefined) {
  const amount = Number(value || 0)
  return Number.isFinite(amount) ? amount.toFixed(2) : String(value || '-')
}

function dateLabel(value: string | null | undefined) {
  if (!value) return '-'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function dateOnlyLabel(value: string | null | undefined) {
  if (!value) return '-'
  const date = new Date(`${value}T00:00:00`)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString()
}

function today() {
  const date = new Date()
  const pad = (value: number) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function profileLabel(profile: ProfileOption) {
  const user = profile.user_detail
  if (!user) return `#${profile.id}`
  return `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.telegram_username || user.email || `#${profile.id}`
}

function chargeStatusLabel(status: string) {
  const map: Record<string, string> = {
    draft: 'Чернетка',
    issued: 'Очікує оплати',
    partial: 'Частково оплачено',
    paid: 'Оплачено',
    cancelled: 'Скасовано',
  }
  return map[status] || status
}

function payoutStatusLabel(status: string) {
  const map: Record<string, string> = {
    draft: 'Нараховано',
    approved: 'Нараховано',
    partial: 'Частково виплачено',
    paid: 'Виплачено',
    cancelled: 'Скасовано',
  }
  return map[status] || status
}

function lessonPayoutStatus(payouts: Payout[]) {
  const active = payouts.filter((payout) => payout.status !== 'cancelled')
  const accrued = active.reduce((total, payout) => total + Number(payout.amount || 0), 0)
  const paid = active
    .filter((payout) => payout.status === 'paid')
    .reduce((total, payout) => total + Number(payout.amount || 0), 0)
  if (accrued > 0 && paid >= accrued) return 'Виплачено'
  if (paid > 0) return 'Частково виплачено'
  return 'Нараховано'
}

function paymentError(e: any) {
  const payload = e?.payload
  if (payload?.detail) return String(payload.detail)
  if (payload && typeof payload === 'object') {
    return Object.entries(payload)
      .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(', ') : String(messages)}`)
      .join('; ')
  }
  return e?.message || 'Не вдалося зберегти оплату'
}

function permissionAwareError(e: any) {
  if (e?.status === 403) {
    return 'Немає прав для цієї дії. Вийдіть із системи та увійдіть під admin@example.com.'
  }
  return e?.payload?.detail || e?.message || 'Не вдалося завантажити платежі'
}

onMounted(async () => {
  await auth.bootstrap()
  await auth.refreshMe()
  await loadLookups()
  await loadPayments()
})
</script>

<style scoped>
.filters-panel {
  margin-bottom: 12px;
}

.filters {
  display: grid;
  grid-template-columns: repeat(3, minmax(150px, 220px)) auto auto;
  gap: 10px;
  align-items: end;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.tab {
  border: 1px solid var(--border-strong);
  background: var(--button-ghost-bg);
  color: var(--text-soft);
  border-radius: 6px;
  padding: 8px 12px;
  cursor: pointer;
}

.tab--active {
  border-color: var(--accent-border);
  background: var(--accent-soft);
}

.admin-grid {
  display: grid;
  gap: 12px;
}

.detail-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
  color: var(--text-soft);
  font-size: 13px;
}

.payment-form {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) minmax(140px, 180px) minmax(120px, 180px) minmax(180px, 1fr) auto;
  gap: 10px;
  align-items: end;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(120px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.summary-strip div {
  display: grid;
  gap: 4px;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px;
  background: var(--surface-soft);
}

.summary-strip span {
  color: var(--muted);
  font-size: 12px;
}

.summary-strip strong {
  color: var(--text);
  font-size: 18px;
}

@media (max-width: 720px) {
  .filters {
    grid-template-columns: 1fr;
  }

  .payment-form {
    grid-template-columns: 1fr;
  }

  .summary-strip {
    grid-template-columns: 1fr;
  }
}
</style>
