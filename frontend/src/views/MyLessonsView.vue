<template>
  <AppShell :title="isCreateRoute ? 'Створити урок' : 'Мої уроки'">
    <div v-if="canManageLessons && !isCreateRoute" class="panel form">
      <button class="btn create-toggle" type="button" @click="openCreateLessonPage">Створити урок</button>
    </div>

    <div v-if="canManageLessons && isCreateRoute" class="panel form create-page">
      <div class="form-title-row">
        <div class="panel__title">Створити урок</div>
        <button class="btn btn--ghost" type="button" :disabled="savingLesson" @click="cancelCreateLesson">Скасувати</button>
      </div>
      <div class="grid">
        <div class="dropdown">
          <button class="input dropdown__trigger" type="button" @click="lessonGroupOpen = !lessonGroupOpen">
            {{ selectedLessonGroupLabel }}
          </button>
          <div v-if="lessonGroupOpen" class="dropdown__menu dropdown-list">
            <button class="dropdown__option" type="button" @click="selectLessonGroup(null)">Група...</button>
            <button class="dropdown__option" v-for="g in groups" :key="g.id" type="button" @click="selectLessonGroup(g.id)">
              {{ g.name || `Група #${g.id}` }}
            </button>
          </div>
        </div>
        <input class="input" type="datetime-local" v-model="lessonForm.starts_at_local" />
        <textarea class="input ta" v-model="lessonForm.notes" placeholder="Нотатки"></textarea>
        <button class="btn" type="button" :disabled="savingLesson" @click="createLesson">{{ savingLesson ? 'Збереження...' : 'Створити урок' }}</button>
      </div>
    </div>

    <div v-if="!isCreateRoute" class="panel">
      <div class="panel__title">Останні</div>
      <div class="filters">
        <label class="field">
          <span class="field__label">З</span>
          <input class="input" type="date" v-model="dateFilterFrom" @change="reloadLessons()" />
        </label>
        <label class="field">
          <span class="field__label">До</span>
          <input class="input" type="date" v-model="dateFilterTo" @change="reloadLessons()" />
        </label>
        <SearchableSelect
          v-if="isAdmin"
          v-model="teacherFilter"
          label="Викладач"
          :options="teacherFilterOptions"
          @change="reloadLessons()"
        />
        <SearchableSelect
          v-if="canManageLessons"
          v-model="studentFilter"
          label="Учні"
          :options="studentFilterOptions"
          @change="reloadLessons()"
        />
        <SearchableSelect
          v-if="canManageLessons"
          v-model="groupFilter"
          label="Група"
          :options="groupFilterOptions"
          @change="reloadLessons()"
        />
        <button class="btn btn--ghost filter-clear" type="button" :disabled="!hasFilters" @click="clearFilters">
          Очистити
        </button>
      </div>
      <div v-if="canSeePayroll && hasDateInterval" class="period-totals">
        <div>Винагорода вчителя за період: {{ formatPayrollAmount(payrollAmountTotal) }}</div>
        <div v-if="isAdmin">Вартість занять за період: {{ formatPayrollAmount(billedAmountTotal) }}</div>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div v-else-if="loading" class="muted">Завантаження...</div>
      <template v-else>
        <DataTable class="lessons-table" :columns="columns" :rows="filteredRows" :onRowClick="onLessonClick" />
        <div v-if="lessonPageCount > 1" class="pagination">
          <button class="btn btn--ghost" type="button" :disabled="lessonPage <= 1" @click="goToLessonPage(lessonPage - 1)">
            Назад
          </button>
          <span class="pagination__label">
            Сторінка {{ lessonPage }} з {{ lessonPageCount }} · {{ lessonPageStart }}-{{ lessonPageEnd }} з {{ lessonCount }}
          </span>
          <button class="btn btn--ghost" type="button" :disabled="lessonPage >= lessonPageCount" @click="goToLessonPage(lessonPage + 1)">
            Вперед
          </button>
        </div>
      </template>
    </div>

    <div v-if="!isCreateRoute && selectedLesson" class="lesson-modal" @click.self="closeLessonDetailAndRoute">
      <div ref="lessonDetailPanel" class="panel form lesson-modal__window" role="dialog" aria-modal="true">
        <div class="lesson-modal__header">
          <div class="panel__title">Деталізація уроку #{{ selectedLesson.id }}</div>
          <button class="btn btn--ghost lesson-modal__close" type="button" :disabled="savingLesson || savingReschedule" @click="closeLessonDetailAndRoute">
            Назад
          </button>
        </div>
      <div v-if="detailError" class="error">{{ detailError }}</div>
      <div v-else-if="detailLoading" class="muted">Завантаження...</div>
      <div v-else class="lesson-detail">
        <div class="detail-grid">
          <label class="field">
            <span class="field__label">Викладач</span>
            <input class="input" type="text" :value="teacherLabelByGroup(editLessonForm.group)" disabled />
          </label>
          <label class="field">
            <span class="field__label">Група</span>
            <input class="input" type="text" :value="groupLabel(editLessonForm.group)" disabled />
          </label>
          <label class="field">
            <span class="field__label">Статус</span>
            <select class="input dropdown-list" v-model="editLessonForm.status" :disabled="savingLesson || !canManageLessons">
              <option value="scheduled">Заплановано</option>
              <option value="completed">Завершено</option>
              <option value="cancelled">Скасовано</option>
            </select>
          </label>
          <label class="field">
            <span class="field__label">Початок заняття</span>
            <input class="input" type="datetime-local" step="900" v-model="editLessonForm.starts_at_local" :disabled="savingLesson || !canEditLessonTime" />
          </label>
          <label v-if="canSeeLessonPayrollAmount" class="field">
            <span class="field__label">Винагорода викладача за урок</span>
            <input class="input" type="text" :value="formatPayrollAmount(selectedLesson.payroll_amount)" disabled />
          </label>
        </div>

        <div class="section-title">Учні</div>
        <table class="participants-table">
          <thead>
            <tr>
              <th>Учень</th>
              <th>Присутній</th>
              <th v-if="canSeeLessonBilledAmount">Вартість заняття</th>
              <th v-if="showParticipantPayrollAmount">Винагорода викладача</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="participantForms.length === 0">
              <td class="muted" :colspan="participantColumnCount">Немає учнів</td>
            </tr>
            <tr v-for="participant in participantForms" :key="participant.id">
              <td>{{ participant.studentLabel }}</td>
              <td>
                <input
                  class="presence-checkbox"
                  type="checkbox"
                  :checked="isParticipantPresent(participant)"
                  :disabled="savingLesson || !canMarkAttendance"
                  @change="toggleParticipantPresence(participant, $event)"
                />
              </td>
              <td v-if="canSeeLessonBilledAmount">
                <input class="input amount-input" type="number" min="0" step="0.01" v-model="participant.billed_amount" :disabled="savingLesson || !isAdmin" />
              </td>
              <td v-if="showParticipantPayrollAmount">
                <input class="input amount-input" type="number" min="0" step="0.01" :value="participantPayrollAmount(participant)" disabled />
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="participantForms.length" class="participants-list">
          <div v-for="participant in participantForms" :key="participant.id" class="participant-card">
            <div class="participant-card__name">{{ participant.studentLabel }}</div>
            <label class="participant-card__row">
              <span>Присутній</span>
              <input
                class="presence-checkbox"
                type="checkbox"
                :checked="isParticipantPresent(participant)"
                :disabled="savingLesson || !canMarkAttendance"
                @change="toggleParticipantPresence(participant, $event)"
              />
            </label>
            <label v-if="canSeeLessonBilledAmount" class="participant-card__row">
              <span>Вартість заняття</span>
              <input class="input amount-input" type="number" min="0" step="0.01" v-model="participant.billed_amount" :disabled="savingLesson || !isAdmin" />
            </label>
            <div v-if="showParticipantPayrollAmount" class="participant-card__row">
              <span>Винагорода викладача</span>
              <span>{{ participantPayrollAmount(participant) }}</span>
            </div>
          </div>
        </div>

        <div class="section-title">Перенесення</div>
        <div class="reschedule-panel">
          <div v-if="rescheduleError" class="error">{{ rescheduleError }}</div>
          <div v-if="activeRescheduleRequest" class="reschedule-status">
            <div>Статус: {{ rescheduleStatusLabel(activeRescheduleRequest.status) }}</div>
            <div v-if="activeRescheduleRequest.requested_starts_at">Бажаний час: {{ formatLessonDateTime(activeRescheduleRequest.requested_starts_at) }}</div>
            <div v-if="activeRescheduleRequest.reason">Причина: {{ activeRescheduleRequest.reason }}</div>
          </div>

          <div v-if="canCreateRescheduleRequest" class="reschedule-form">
            <label class="field">
              <span class="field__label">Бажаний час</span>
              <input class="input" type="datetime-local" step="900" v-model="rescheduleForm.requested_starts_at_local" :disabled="savingReschedule" />
            </label>
            <label class="field">
              <span class="field__label">Причина</span>
              <textarea class="input ta" v-model="rescheduleForm.reason" :disabled="savingReschedule"></textarea>
            </label>
            <button class="btn save-detail" type="button" :disabled="savingReschedule" @click="createRescheduleRequest">
              {{ savingReschedule ? 'Збереження...' : 'Запросити перенесення' }}
            </button>
          </div>

          <button v-else-if="canConfirmRescheduleRequest" class="btn save-detail" type="button" :disabled="savingReschedule" @click="confirmRescheduleRequest">
            {{ savingReschedule ? 'Збереження...' : 'Підтвердити перенесення' }}
          </button>

          <div v-else-if="canApplyRescheduleRequest" class="reschedule-form">
            <label class="field">
              <span class="field__label">Новий час уроку</span>
              <input class="input" type="datetime-local" step="900" v-model="applyRescheduleForm.starts_at_local" :disabled="savingReschedule" />
            </label>
            <label class="field">
              <span class="field__label">Коментар вчителя</span>
              <textarea class="input ta" v-model="applyRescheduleForm.teacher_comment" :disabled="savingReschedule"></textarea>
            </label>
            <button class="btn save-detail" type="button" :disabled="savingReschedule || !applyRescheduleForm.starts_at_local" @click="applyRescheduleRequest">
              {{ savingReschedule ? 'Збереження...' : 'Перенести урок' }}
            </button>
          </div>

          <div v-else-if="rescheduleRequests.length === 0" class="muted">Запитів на перенесення немає</div>
        </div>

        <label class="field">
          <span class="field__label">Нотатки</span>
          <textarea class="input ta" v-model="editLessonForm.notes" placeholder="Нотатки" :disabled="savingLesson || !canManageLessons"></textarea>
        </label>

        <button v-if="canManageLessons" class="btn save-detail" type="button" :disabled="savingLesson" @click="updateLesson">
          {{ savingLesson ? 'Збереження...' : 'Зберегти урок' }}
        </button>
        <button v-if="isAdmin" class="btn btn--ghost save-detail" type="button" :disabled="savingLesson" @click="deleteLesson">
          Видалити урок
        </button>
      </div>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import AppShell from '@/components/AppShell.vue'
import DataTable from '@/components/DataTable.vue'
import SearchableSelect from '@/components/SearchableSelect.vue'
import { apiRequest } from '@/lib/api'
import { pushDetailRoute, replaceWithoutDetailRoute, routeQueryId } from '@/lib/detailRoute'
import { useAuthStore } from '@/stores/auth'
import { useRoute, useRouter } from 'vue-router'

type Lesson = { id: number; status: string; starts_at: string; payroll_amount?: string; billed_amount?: string; notes?: string; group: number; can_request_reschedule?: boolean }
type LessonParticipant = {
  id: number
  student: number
  student_first_name?: string
  student_last_name?: string
  attendance_status?: string
  billed_amount?: string | number
  payroll_amount?: string | number
}
type LessonDetail = Lesson & { participants?: LessonParticipant[] }
type ParticipantForm = { id: number; studentLabel: string; attendance_status: string; billed_amount: string; payroll_amount: string }
type Group = { id: number; name?: string; teacher?: number | null; format?: string }
type Teacher = { id: number; user_detail?: { first_name?: string; last_name?: string; telegram_username?: string; email?: string } }
type Student = { id: number; user_detail?: { first_name?: string; last_name?: string; telegram_username?: string; email?: string } }
type LessonColumn = { key: string; label: string; render?: (row: Lesson) => string; className?: string; cellClass?: (row: Lesson) => string }
type LessonPageResponse = { count: number; page: number; page_size: number; results: Lesson[] }
type LessonRescheduleRequest = {
  id: number
  lesson: number
  requested_starts_at?: string | null
  reason?: string
  status: string
  parent_confirmed_by?: number | null
  parent_confirmed_at?: string | null
  applied_by?: number | null
  applied_at?: string | null
  new_starts_at?: string | null
  teacher_comment?: string
}

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const canManageLessons = ref(false)
const isAdmin = ref(false)
const loading = ref(true)
const savingLesson = ref(false)
const error = ref<string | null>(null)
const detailLoading = ref(false)
const detailError = ref<string | null>(null)
const rescheduleError = ref<string | null>(null)
const savingReschedule = ref(false)
const lessonGroupOpen = ref(false)
const dateFilterFrom = ref('')
const dateFilterTo = ref('')
const teacherFilter = ref<number | null>(null)
const studentFilter = ref<number | null>(null)
const groupFilter = ref('')
const lessonPage = ref(1)
const lessonPageSize = ref(20)
const lessonCount = ref(0)
const rows = ref<Lesson[]>([])
const selectedLesson = ref<Lesson | null>(null)
const lessonDetailPanel = ref<HTMLElement | null>(null)
const groups = ref<Group[]>([])
const teachers = ref<Teacher[]>([])
const students = ref<Student[]>([])
const participantForms = ref<ParticipantForm[]>([])
const rescheduleRequests = ref<LessonRescheduleRequest[]>([])
let detailRequestSeq = 0

const lessonForm = ref({ group: null as number | null, starts_at_local: '', notes: '' })
const editLessonForm = ref({ group: null as number | null, status: 'scheduled', starts_at_local: '', notes: '' })
const rescheduleForm = ref({ requested_starts_at_local: '', reason: '' })
const applyRescheduleForm = ref({ starts_at_local: '', teacher_comment: '' })
const isCreateRoute = computed(() => route.name === 'my-lessons-create')
const DETAIL_QUERY_KEY = 'lesson'
const LIST_ROUTE_NAME = 'my-lessons'

const columns = computed(() => {
  const items: LessonColumn[] = [
    { key: 'id', label: 'ID', className: isAdmin.value ? 'admin-mobile-hidden' : undefined },
    { key: 'group', label: 'Група', render: (r: Lesson) => groupLabel(r.group) },
    {
      key: 'status',
      label: 'Статус',
      className: isAdmin.value ? 'admin-mobile-hidden' : undefined,
      render: (r: Lesson) => lessonStatusLabel(r.status),
      cellClass: (r: Lesson) => lessonStatusClass(r.status),
    },
    { key: 'starts_at', label: 'Початок', render: (r: Lesson) => formatLessonDateTime(r.starts_at) },
  ]
  if (isAdmin.value) {
    items.splice(1, 0, { key: 'teacher', label: 'Викладач', render: (r: Lesson) => teacherLabelByGroup(r.group) })
  }
  if (canSeePayroll.value) {
    items.push({ key: 'payroll_amount', label: 'Винагорода вчителя', render: (r: Lesson) => formatPayrollAmount(r.payroll_amount) })
  }
  if (isAdmin.value) {
    items.push({
      key: 'billed_amount',
      label: 'Вартість заняття',
      className: 'admin-mobile-hidden',
      render: (r: Lesson) => formatPayrollAmount(r.billed_amount),
    })
  }
  items.push({ key: 'notes', label: 'Нотатки', className: 'col-notes', render: (r: Lesson) => r.notes || '-' })
  return items
})

const hasDateInterval = computed(() => Boolean(dateFilterFrom.value || dateFilterTo.value))
const hasFilters = computed(() => (
  hasDateInterval.value
  || teacherFilter.value !== null
  || studentFilter.value !== null
  || groupFilter.value !== ''
))
const canSeePayroll = computed(() => canManageLessons.value)
const canSeeLessonBilledAmount = computed(() => isAdmin.value || !canManageLessons.value)
const canSeeLessonPayrollAmount = computed(() => canManageLessons.value)
const selectedLessonGroup = computed(() => {
  const groupId = selectedLesson.value?.group
  if (!groupId) return null
  return groups.value.find((g) => g.id === groupId) || null
})
const selectedLessonIsGroup = computed(() => selectedLessonGroup.value?.format === 'group')
const showParticipantPayrollAmount = computed(() => canSeeLessonPayrollAmount.value && !selectedLessonIsGroup.value)
const canMarkAttendance = computed(() => canManageLessons.value && selectedLesson.value?.status === 'scheduled')
const canEditLessonTime = computed(() => {
  if (isAdmin.value) return true
  return currentRole.value === 'teacher' && ['scheduled', 'cancelled'].includes(selectedLesson.value?.status || '')
})
const participantColumnCount = computed(() => 2 + Number(canSeeLessonBilledAmount.value) + Number(showParticipantPayrollAmount.value))
const activeRescheduleRequest = computed(() =>
  rescheduleRequests.value.find((item) => item.status === 'pending_parent' || item.status === 'parent_confirmed') || null,
)
const currentRole = computed(() => auth.me?.role || '')
const canCreateRescheduleRequest = computed(() =>
  currentRole.value === 'student' && Boolean(selectedLesson.value?.can_request_reschedule) && !activeRescheduleRequest.value,
)
const canConfirmRescheduleRequest = computed(() =>
  currentRole.value === 'parent' && activeRescheduleRequest.value?.status === 'pending_parent',
)
const canApplyRescheduleRequest = computed(() =>
  canManageLessons.value && activeRescheduleRequest.value?.status === 'parent_confirmed',
)
const filteredRows = computed(() => {
  if (!isAdmin.value || teacherFilter.value === null) return rows.value
  return rows.value.filter((lesson) => groupTeacherId(lesson.group) === teacherFilter.value)
})
const teacherFilterOptions = computed(() => [
  { value: null, label: 'Всі викладачі' },
  ...teachers.value.map((teacher) => ({ value: teacher.id, label: teacherLabel(teacher) })),
])
const studentFilterOptions = computed(() => [
  { value: null, label: 'Всі учні' },
  ...students.value.map((student) => ({ value: student.id, label: studentProfileLabel(student) })),
])
const groupFilterOptions = computed(() => [
  { value: '', label: 'Всі групи' },
  { value: 'individual', label: 'Індивідуальні' },
  { value: 'group', label: 'Групові' },
  ...groups.value.map((group) => ({ value: String(group.id), label: group.name || `Група #${group.id}` })),
])
const lessonPageCount = computed(() => Math.max(1, Math.ceil(lessonCount.value / lessonPageSize.value)))
const lessonPageStart = computed(() => (lessonCount.value === 0 ? 0 : (lessonPage.value - 1) * lessonPageSize.value + 1))
const lessonPageEnd = computed(() => Math.min(lessonCount.value, lessonPage.value * lessonPageSize.value))
const payrollAmountTotal = computed(() => filteredRows.value.reduce((sum, lesson) => sum + payrollAmountValue(lesson.payroll_amount), 0))
const billedAmountTotal = computed(() => filteredRows.value.reduce((sum, lesson) => sum + payrollAmountValue(lesson.billed_amount), 0))

const selectedLessonGroupLabel = computed(() => {
  if (!lessonForm.value.group) return 'Група...'
  return groups.value.find((g) => g.id === lessonForm.value.group)?.name || `Група #${lessonForm.value.group}`
})

function selectLessonGroup(groupId: number | null) {
  lessonForm.value.group = groupId
  lessonGroupOpen.value = false
}

function localFromIso(iso: string) {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function formatLessonDateTime(iso: string) {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function isoFromLocal(localDateTime: string) {
  if (!localDateTime) return null
  const d = new Date(localDateTime)
  if (isNaN(d.getTime())) return null
  return d.toISOString()
}

function payrollAmountValue(value: string | number | null | undefined) {
  const amount = Number(value ?? 0)
  return Number.isFinite(amount) ? amount : 0
}

function formatPayrollAmount(value: string | number | null | undefined) {
  const amount = payrollAmountValue(value)
  return amount.toFixed(2)
}

function lessonStatusLabel(status: string) {
  const map: Record<string, string> = {
    scheduled: 'Заплановано',
    completed: 'Завершено',
    cancelled: 'Скасовано',
  }
  return map[status] || status
}

function lessonStatusClass(status: string) {
  if (status === 'scheduled') return 'status-scheduled'
  if (status === 'completed') return 'status-completed'
  return ''
}

function rescheduleStatusLabel(status: string) {
  const map: Record<string, string> = {
    pending_parent: 'Очікує підтвердження батьків',
    parent_confirmed: 'Підтверджено батьками',
    applied: 'Перенесено',
    rejected: 'Відхилено',
  }
  return map[status] || status
}

function apiErrorMessage(e: any, fallback: string) {
  const detail = e?.payload?.detail
  if (typeof detail === 'string') return detail
  if (e?.payload && typeof e.payload === 'object') {
    const first = Object.values(e.payload)[0]
    if (Array.isArray(first) && first.length > 0) return String(first[0])
    if (typeof first === 'string') return first
  }
  return e?.message || fallback
}

function groupLabel(groupId: number | null) {
  if (!groupId) return '-'
  return groups.value.find((g) => g.id === groupId)?.name || `Група #${groupId}`
}

function teacherLabelByGroup(groupId: number | null) {
  if (!groupId) return '-'
  const teacherId = groupTeacherId(groupId)
  if (!teacherId) return '-'
  const teacher = teachers.value.find((t) => t.id === teacherId)
  if (teacher) return teacherLabel(teacher)
  return `Викладач #${teacherId}`
}

function groupTeacherId(groupId: number | null) {
  if (!groupId) return null
  return groups.value.find((g) => g.id === groupId)?.teacher ?? null
}

function teacherLabel(teacher: Teacher) {
  const u = teacher.user_detail || {}
  return [u.first_name, u.last_name].filter(Boolean).join(' ') || u.telegram_username || u.email || `Викладач #${teacher.id}`
}

function studentProfileLabel(student: Student) {
  const user = student.user_detail || {}
  return [user.first_name, user.last_name].filter(Boolean).join(' ')
    || user.telegram_username
    || user.email
    || `Учень #${student.id}`
}

function studentLabel(participant: LessonParticipant) {
  return [participant.student_last_name, participant.student_first_name].filter(Boolean).join(' ') || `Учень #${participant.student}`
}

function isParticipantPresent(participant: ParticipantForm) {
  return participant.attendance_status === 'present'
}

function participantPayrollAmount(participant: ParticipantForm) {
  return isParticipantPresent(participant) ? participant.payroll_amount : '0.00'
}

function fillLessonDetailForm(lesson: LessonDetail) {
  editLessonForm.value = {
    group: lesson.group,
    status: lesson.status,
    starts_at_local: localFromIso(lesson.starts_at),
    notes: lesson.notes || '',
  }
  participantForms.value = (lesson.participants || []).map((participant) => ({
    id: participant.id,
    studentLabel: studentLabel(participant),
    attendance_status: participant.attendance_status || 'pending',
    billed_amount: String(participant.billed_amount ?? '0.00'),
    payroll_amount: String(participant.payroll_amount ?? '0.00'),
  }))
}

function closeLessonDetail() {
  selectedLesson.value = null
  participantForms.value = []
  rescheduleRequests.value = []
  rescheduleForm.value = { requested_starts_at_local: '', reason: '' }
  applyRescheduleForm.value = { starts_at_local: '', teacher_comment: '' }
  detailError.value = null
  rescheduleError.value = null
}

async function closeLessonDetailAndRoute() {
  closeLessonDetail()
  await replaceWithoutDetailRoute(router, route, LIST_ROUTE_NAME, DETAIL_QUERY_KEY)
}

async function toggleParticipantPresence(participant: ParticipantForm, event: Event) {
  if (!selectedLesson.value) return
  const checkbox = event.target as HTMLInputElement
  const nextStatus = checkbox.checked ? 'present' : 'absent'
  const previousStatus = participant.attendance_status
  const previousPayrollAmount = participant.payroll_amount

  participant.attendance_status = nextStatus
  if (nextStatus !== 'present') participant.payroll_amount = '0.00'
  savingLesson.value = true
  detailError.value = null

  try {
    const result = await apiRequest<{ attendance_status: string; payroll_amount?: string | number }>(
      `/api/academics/lessons/${selectedLesson.value.id}/mark-attendance/`,
      {
        method: 'POST',
        body: {
          participant_id: participant.id,
          attendance_status: nextStatus,
        },
      },
    )
    participant.attendance_status = result.attendance_status
    participant.payroll_amount = String(result.payroll_amount ?? participant.payroll_amount)
    await reloadSelectedLessonDetail()
    await reloadLessons()
  } catch (e: any) {
    participant.attendance_status = previousStatus
    participant.payroll_amount = previousPayrollAmount
    checkbox.checked = previousStatus === 'present'
    detailError.value = apiErrorMessage(e, 'Не вдалося оновити присутність')
  } finally {
    savingLesson.value = false
  }
}

function syncApplyRescheduleForm() {
  const request = activeRescheduleRequest.value
  applyRescheduleForm.value = {
    starts_at_local: request?.requested_starts_at ? localFromIso(request.requested_starts_at) : editLessonForm.value.starts_at_local,
    teacher_comment: request?.teacher_comment || '',
  }
}

async function loadRescheduleRequests(lessonId: number) {
  try {
    rescheduleRequests.value = await apiRequest<LessonRescheduleRequest[]>(`/api/academics/reschedule-requests/?lesson=${lessonId}`)
    syncApplyRescheduleForm()
  } catch (e: any) {
    rescheduleError.value = apiErrorMessage(e, 'Не вдалося завантажити запити на перенесення')
  }
}

async function reloadSelectedLessonDetail() {
  if (!selectedLesson.value) return
  const detail = await apiRequest<LessonDetail>(`/api/academics/lessons/${selectedLesson.value.id}/`)
  selectedLesson.value = detail
  fillLessonDetailForm(detail)
  await loadRescheduleRequests(detail.id)
}

async function openLessonById(lessonId: number) {
  if (!lessonId) return
  const row = rows.value.find((lesson) => lesson.id === lessonId)
  if (row) {
    await onLessonClick(row)
    return
  }

  const requestSeq = ++detailRequestSeq
  detailLoading.value = true
  detailError.value = null
  rescheduleError.value = null
  try {
    const detail = await apiRequest<LessonDetail>(`/api/academics/lessons/${lessonId}/`)
    if (requestSeq !== detailRequestSeq) return
    selectedLesson.value = detail
    fillLessonDetailForm(detail)
    rescheduleRequests.value = []
    rescheduleForm.value = { requested_starts_at_local: '', reason: '' }
    applyRescheduleForm.value = { starts_at_local: localFromIso(detail.starts_at), teacher_comment: '' }
    await nextTick()
    lessonDetailPanel.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    await loadRescheduleRequests(detail.id)
  } finally {
    if (requestSeq === detailRequestSeq) detailLoading.value = false
  }
}

async function openLessonFromRoute() {
  const lessonId = routeQueryId(route, DETAIL_QUERY_KEY)
  if (!lessonId) {
    if (selectedLesson.value) closeLessonDetail()
    return
  }
  try {
    await openLessonById(lessonId)
  } catch (e: any) {
    detailError.value = apiErrorMessage(e, 'Не вдалося завантажити деталізацію уроку')
  }
}

function normalizeToQuarterHour(localDateTime: string) {
  if (!localDateTime) return localDateTime
  const d = new Date(localDateTime)
  if (isNaN(d.getTime())) return localDateTime
  d.setSeconds(0, 0)
  const minute = d.getMinutes()
  const roundedMinute = Math.round(minute / 15) * 15
  d.setMinutes(roundedMinute)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function onLessonClick(lesson: Lesson) {
  if (await pushDetailRoute(router, route, DETAIL_QUERY_KEY, lesson.id)) return

  const requestSeq = ++detailRequestSeq
  selectedLesson.value = lesson
  fillLessonDetailForm({ ...lesson, participants: [] })
  rescheduleRequests.value = []
  rescheduleForm.value = { requested_starts_at_local: '', reason: '' }
  applyRescheduleForm.value = { starts_at_local: localFromIso(lesson.starts_at), teacher_comment: '' }
  detailLoading.value = true
  detailError.value = null
  rescheduleError.value = null
  await nextTick()
  lessonDetailPanel.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  try {
    const detail = await apiRequest<LessonDetail>(`/api/academics/lessons/${lesson.id}/`)
    if (requestSeq !== detailRequestSeq) return
    selectedLesson.value = detail
    fillLessonDetailForm(detail)
    await loadRescheduleRequests(lesson.id)
  } catch (e: any) {
    if (requestSeq !== detailRequestSeq) return
    detailError.value = e?.payload?.detail || e?.message || 'Не вдалося завантажити деталізацію уроку'
  } finally {
    if (requestSeq === detailRequestSeq) detailLoading.value = false
  }
}

async function loadTeacherGroups() {
  if (isAdmin.value) {
    const [groupItems, teacherItems, studentItems] = await Promise.all([
      apiRequest<Group[]>('/api/academics/groups/'),
      apiRequest<Teacher[]>('/api/users/teachers/'),
      apiRequest<Student[]>('/api/users/students/'),
    ])
    groups.value = groupItems
    teachers.value = teacherItems
    students.value = studentItems
    return
  }
  const [groupItems, studentItems] = await Promise.all([
    apiRequest<Group[]>('/api/academics/groups/'),
    canManageLessons.value ? apiRequest<Student[]>('/api/users/students/') : Promise.resolve([]),
  ])
  groups.value = groupItems
  students.value = studentItems
}

async function loadLessons() {
  const params = new URLSearchParams()
  if (dateFilterFrom.value) params.set('date_from', dateFilterFrom.value)
  if (dateFilterTo.value) params.set('date_to', dateFilterTo.value)
  if (teacherFilter.value !== null) params.set('teacher', String(teacherFilter.value))
  if (studentFilter.value !== null) params.set('student', String(studentFilter.value))
  if (groupFilter.value === 'individual' || groupFilter.value === 'group') {
    params.set('group_format', groupFilter.value)
  } else if (groupFilter.value) {
    params.set('group', groupFilter.value)
  }
  params.set('page', String(lessonPage.value))
  params.set('page_size', String(lessonPageSize.value))
  const query = params.toString()
  const data = await apiRequest<Lesson[] | LessonPageResponse>(`/api/my/lessons/${query ? `?${query}` : ''}`)
  if (Array.isArray(data)) {
    rows.value = data
    lessonCount.value = data.length
    return
  }
  rows.value = data.results
  lessonCount.value = data.count
  lessonPage.value = data.page
  lessonPageSize.value = data.page_size
}

async function reloadLessons(resetPage = true) {
  if (resetPage) lessonPage.value = 1
  loading.value = true
  error.value = null
  try {
    await loadLessons()
  } catch (e: any) {
    error.value = e?.payload?.detail || e?.message || 'Не вдалося завантажити уроки'
  } finally {
    loading.value = false
  }
}

async function goToLessonPage(page: number) {
  const nextPage = Math.min(Math.max(page, 1), lessonPageCount.value)
  if (nextPage === lessonPage.value || loading.value) return
  lessonPage.value = nextPage
  await reloadLessons(false)
}

function clearFilters() {
  if (!hasFilters.value) return
  dateFilterFrom.value = ''
  dateFilterTo.value = ''
  teacherFilter.value = null
  studentFilter.value = null
  groupFilter.value = ''
  void reloadLessons()
}

function resetCreateLessonForm() {
  lessonForm.value = { group: null, starts_at_local: '', notes: '' }
  lessonGroupOpen.value = false
  selectedLesson.value = null
  error.value = null
}

function openCreateLessonPage() {
  router.push({ name: 'my-lessons-create' })
}

function cancelCreateLesson() {
  router.push({ name: 'my-lessons' })
}

async function createLesson() {
  if (!lessonForm.value.group || !lessonForm.value.starts_at_local) return
  savingLesson.value = true
  error.value = null
  try {
    await apiRequest('/api/academics/lessons/', {
      method: 'POST',
      body: {
        group: lessonForm.value.group,
        starts_at: new Date(lessonForm.value.starts_at_local).toISOString(),
        status: 'scheduled',
        notes: lessonForm.value.notes,
      },
    })
    lessonForm.value = { group: null, starts_at_local: '', notes: '' }
    lessonGroupOpen.value = false
    if (isCreateRoute.value) {
      router.push({ name: 'my-lessons' })
    } else {
      await reloadLessons()
    }
  } catch (e: any) {
    error.value = e?.payload?.detail || e?.message || 'Не вдалося створити урок'
  } finally {
    savingLesson.value = false
  }
}

async function updateLesson() {
  if (!selectedLesson.value || !editLessonForm.value.starts_at_local) return
  savingLesson.value = true
  error.value = null
  detailError.value = null
  try {
    const body: Record<string, unknown> = { notes: editLessonForm.value.notes }
    if (canEditLessonTime.value) {
      body.starts_at = new Date(editLessonForm.value.starts_at_local).toISOString()
    }
    if (canManageLessons.value) {
      body.status = editLessonForm.value.status
    }
    if (isAdmin.value) {
      body.participant_updates = participantForms.value.map((participant) => ({
        id: participant.id,
        billed_amount: participant.billed_amount,
      }))
    }
    await apiRequest<LessonDetail>(`/api/academics/lessons/${selectedLesson.value.id}/`, {
      method: 'PATCH',
      body,
    })
    await reloadLessons()
    await closeLessonDetailAndRoute()
  } catch (e: any) {
    detailError.value = e?.payload?.detail || e?.message || 'Не вдалося оновити урок'
  } finally {
    savingLesson.value = false
  }
}

async function deleteLesson() {
  if (!selectedLesson.value) return
  const ok = window.confirm(`Видалити урок #${selectedLesson.value.id}?`)
  if (!ok) return

  savingLesson.value = true
  error.value = null
  detailError.value = null
  try {
    await apiRequest(`/api/academics/lessons/${selectedLesson.value.id}/`, { method: 'DELETE' })
    await closeLessonDetailAndRoute()
    await reloadLessons()
  } catch (e: any) {
    detailError.value = apiErrorMessage(e, 'Не вдалося видалити урок')
  } finally {
    savingLesson.value = false
  }
}

async function createRescheduleRequest() {
  if (!selectedLesson.value) return
  savingReschedule.value = true
  rescheduleError.value = null
  try {
    await apiRequest('/api/academics/reschedule-requests/', {
      method: 'POST',
      body: {
        lesson: selectedLesson.value.id,
        requested_starts_at: isoFromLocal(rescheduleForm.value.requested_starts_at_local),
        reason: rescheduleForm.value.reason,
      },
    })
    rescheduleForm.value = { requested_starts_at_local: '', reason: '' }
    await loadRescheduleRequests(selectedLesson.value.id)
  } catch (e: any) {
    rescheduleError.value = apiErrorMessage(e, 'Не вдалося створити запит на перенесення')
  } finally {
    savingReschedule.value = false
  }
}

async function confirmRescheduleRequest() {
  const request = activeRescheduleRequest.value
  if (!request || !selectedLesson.value) return
  savingReschedule.value = true
  rescheduleError.value = null
  try {
    await apiRequest(`/api/academics/reschedule-requests/${request.id}/confirm-parent/`, {
      method: 'POST',
      body: {},
    })
    await loadRescheduleRequests(selectedLesson.value.id)
  } catch (e: any) {
    rescheduleError.value = apiErrorMessage(e, 'Не вдалося підтвердити перенесення')
  } finally {
    savingReschedule.value = false
  }
}

async function applyRescheduleRequest() {
  const request = activeRescheduleRequest.value
  const startsAt = isoFromLocal(applyRescheduleForm.value.starts_at_local)
  if (!request || !selectedLesson.value || !startsAt) return
  savingReschedule.value = true
  rescheduleError.value = null
  try {
    await apiRequest(`/api/academics/reschedule-requests/${request.id}/apply/`, {
      method: 'POST',
      body: {
        starts_at: startsAt,
        teacher_comment: applyRescheduleForm.value.teacher_comment,
      },
    })
    await reloadSelectedLessonDetail()
    await reloadLessons()
  } catch (e: any) {
    rescheduleError.value = apiErrorMessage(e, 'Не вдалося перенести урок')
  } finally {
    savingReschedule.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await auth.bootstrap()
    canManageLessons.value = auth.me?.role === 'teacher' || auth.me?.role === 'admin' || !!auth.me?.is_staff
    isAdmin.value = auth.me?.role === 'admin' || !!auth.me?.is_staff
    await loadTeacherGroups()
    if (isCreateRoute.value) {
      resetCreateLessonForm()
    } else {
      await loadLessons()
      await openLessonFromRoute()
    }
  } catch (e: any) {
    error.value = e?.payload?.detail || e?.message || 'Не вдалося завантажити дані'
  } finally {
    loading.value = false
  }
})

watch(
  () => route.query[DETAIL_QUERY_KEY],
  () => {
    if (!loading.value && !isCreateRoute.value) void openLessonFromRoute()
  },
)

watch(
  () => route.name,
  (name) => {
    if (name === 'my-lessons-create') {
      resetCreateLessonForm()
    } else if (name === 'my-lessons') {
      void reloadLessons()
    }
  },
)

watch(
  () => editLessonForm.value.starts_at_local,
  (value) => {
    const normalized = normalizeToQuarterHour(value)
    if (normalized !== value) editLessonForm.value.starts_at_local = normalized
  },
)

watch(
  () => rescheduleForm.value.requested_starts_at_local,
  (value) => {
    const normalized = normalizeToQuarterHour(value)
    if (normalized !== value) rescheduleForm.value.requested_starts_at_local = normalized
  },
)

watch(
  () => applyRescheduleForm.value.starts_at_local,
  (value) => {
    const normalized = normalizeToQuarterHour(value)
    if (normalized !== value) applyRescheduleForm.value.starts_at_local = normalized
  },
)
</script>

<style scoped>
.form {
  margin-bottom: 12px;
}
.create-page {
  max-width: 720px;
}
.form-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}
.grid {
  display: grid;
  gap: 10px;
}
.create-toggle {
  justify-self: start;
  padding: 1px 9px;
  font-size: 12px;
  line-height: 1.1;
}
.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
  align-items: end;
  margin-bottom: 10px;
}
.filter-clear {
  min-height: 39px;
}
.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 12px;
  flex-wrap: wrap;
}
.pagination__label {
  color: var(--text-soft);
  font-size: 13px;
}
.period-totals {
  display: grid;
  gap: 4px;
  margin-bottom: 10px;
  color: var(--text-soft);
  font-size: 13px;
  font-weight: 650;
}
.lesson-detail {
  display: grid;
  gap: 12px;
}
.lesson-modal {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgba(15, 23, 42, 0.48);
}
.lesson-modal__window {
  width: min(960px, 100%);
  max-height: calc(100vh - 36px);
  margin: 0;
  overflow: auto;
}
.lesson-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.lesson-modal__close {
  flex: 0 0 auto;
}
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(180px, 1fr));
  gap: 10px;
}
.section-title {
  font-weight: 650;
}
.participants-table {
  width: 100%;
  border-collapse: collapse;
}
.participants-list {
  display: none;
}
.participant-card {
  display: grid;
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
}
.participant-card__name {
  font-weight: 650;
}
.participant-card__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  color: var(--text-soft);
  font-size: 13px;
}
.participants-table th,
.participants-table td {
  text-align: left;
  padding: 8px;
  border-bottom: 1px solid var(--border);
}
.amount-input {
  min-width: 120px;
}
.presence-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
}
.presence-checkbox:disabled {
  cursor: default;
}
.reschedule-panel {
  display: grid;
  gap: 10px;
}
.reschedule-panel .btn {
  border-color: var(--warning-border);
}
.reschedule-form {
  display: grid;
  gap: 10px;
}
.reschedule-status {
  display: grid;
  gap: 4px;
  color: var(--text-soft);
  font-size: 13px;
}
.save-detail {
  justify-self: start;
}
.ta {
  min-height: 80px;
  resize: vertical;
}
.dropdown {
  position: relative;
}
.dropdown__trigger {
  width: 100%;
  text-align: left;
}
.dropdown__menu {
  position: absolute;
  z-index: 10;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  max-height: 220px;
  overflow: auto;
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  padding: 6px;
  background: var(--surface);
  box-shadow: var(--shadow-lg);
}
.dropdown__option {
  width: 100%;
  text-align: left;
  border: 0;
  border-radius: 4px;
  padding: 8px;
  color: inherit;
  background: transparent;
  cursor: pointer;
}
.dropdown__option:hover {
  background: var(--surface-hover);
}
@media (max-width: 640px) {
  .filters {
    grid-template-columns: 1fr;
    width: 100%;
  }
  .filter-clear {
    width: 100%;
  }
  :deep(.lessons-table .admin-mobile-hidden) {
    display: none;
  }
  .lesson-modal {
    align-items: stretch;
    padding: 0;
    place-items: stretch;
  }
  .lesson-modal__window {
    width: 100%;
    height: 100dvh;
    max-height: 100dvh;
    border-radius: 0;
    overflow: auto;
    padding-bottom: 20px;
  }
  .lesson-modal__header {
    position: sticky;
    top: 0;
    z-index: 2;
    margin: -14px -14px 14px;
    padding: 12px 14px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    align-items: flex-start;
  }
  .lesson-modal__header .panel__title {
    font-size: 17px;
    line-height: 1.25;
  }
  .lesson-modal__close {
    min-width: 92px;
  }
  .detail-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .reschedule-form {
    grid-template-columns: 1fr;
  }
  .pagination {
    justify-content: stretch;
  }
  .pagination .btn {
    flex: 1 1 120px;
  }
  .pagination__label {
    order: -1;
    width: 100%;
    text-align: center;
  }
  .participants-table {
    display: none;
  }
  .participants-list {
    display: grid;
    gap: 10px;
  }
  .participant-card__row .amount-input {
    width: min(150px, 42vw);
  }
  .amount-input {
    min-width: 108px;
  }
  .save-detail {
    width: 100%;
  }
}
</style>
