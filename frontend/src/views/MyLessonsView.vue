<template>
  <AppShell title="Мої уроки">
    <div v-if="canManageLessons" class="panel form">
      <button class="btn create-toggle" type="button" @click="createLessonFormOpen = !createLessonFormOpen">
        {{ createLessonFormOpen ? 'Сховати' : 'Створити урок' }}
      </button>
      <div v-if="createLessonFormOpen" class="grid">
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
        <input class="input" type="datetime-local" step="900" v-model="lessonForm.starts_at_local" />
        <textarea class="input ta" v-model="lessonForm.notes" placeholder="Нотатки"></textarea>
        <button class="btn" type="button" :disabled="savingLesson" @click="createLesson">{{ savingLesson ? 'Збереження...' : 'Створити урок' }}</button>
      </div>
    </div>

    <div class="panel">
      <div class="panel__title">Останні</div>
      <div class="filters">
        <label class="field">
          <span class="field__label">З</span>
          <input class="input" type="date" v-model="dateFilterFrom" @change="reloadLessons" />
        </label>
        <label class="field">
          <span class="field__label">До</span>
          <input class="input" type="date" v-model="dateFilterTo" @change="reloadLessons" />
        </label>
        <label v-if="isAdmin" class="field">
          <span class="field__label">Викладач</span>
          <select class="input dropdown-list" v-model.number="teacherFilter">
            <option :value="null">Всі викладачі</option>
            <option v-for="teacher in teachers" :key="teacher.id" :value="teacher.id">{{ teacherLabel(teacher) }}</option>
          </select>
        </label>
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
      <DataTable v-else :columns="columns" :rows="filteredRows" :onRowClick="onLessonClick" />
    </div>

    <div v-if="selectedLesson" class="panel form">
      <div class="panel__title">Деталізація уроку #{{ selectedLesson.id }}</div>
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
            <select class="input dropdown-list" v-model="editLessonForm.status" :disabled="savingLesson || !isAdmin">
              <option value="scheduled">Заплановано</option>
              <option value="completed">Завершено</option>
              <option value="cancelled">Скасовано</option>
            </select>
          </label>
          <label class="field">
            <span class="field__label">Початок заняття</span>
            <input class="input" type="datetime-local" step="900" v-model="editLessonForm.starts_at_local" :disabled="savingLesson || !canManageLessons" />
          </label>
        </div>

        <div class="section-title">Учні</div>
        <table class="participants-table">
          <thead>
            <tr>
              <th>Учень</th>
              <th>Вартість заняття</th>
              <th>Винагорода викладача</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="participantForms.length === 0">
              <td class="muted" colspan="3">Немає учнів</td>
            </tr>
            <tr v-for="participant in participantForms" :key="participant.id">
              <td>{{ participant.studentLabel }}</td>
              <td>
                <input class="input amount-input" type="number" min="0" step="0.01" v-model="participant.billed_amount" :disabled="savingLesson || !isAdmin" />
              </td>
              <td>
                <input class="input amount-input" type="number" min="0" step="0.01" v-model="participant.payroll_amount" :disabled="savingLesson || !isAdmin" />
              </td>
            </tr>
          </tbody>
        </table>

        <label class="field">
          <span class="field__label">Нотатки</span>
          <textarea class="input ta" v-model="editLessonForm.notes" placeholder="Нотатки" :disabled="savingLesson || !canManageLessons"></textarea>
        </label>

        <button v-if="canManageLessons" class="btn save-detail" type="button" :disabled="savingLesson" @click="updateLesson">
          {{ savingLesson ? 'Збереження...' : 'Зберегти урок' }}
        </button>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import AppShell from '@/components/AppShell.vue'
import DataTable from '@/components/DataTable.vue'
import { apiRequest } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

type Lesson = { id: number; status: string; starts_at: string; payroll_amount?: string; billed_amount?: string; notes?: string; group: number }
type LessonParticipant = {
  id: number
  student: number
  student_first_name?: string
  student_last_name?: string
  billed_amount?: string | number
  payroll_amount?: string | number
}
type LessonDetail = Lesson & { participants?: LessonParticipant[] }
type ParticipantForm = { id: number; studentLabel: string; billed_amount: string; payroll_amount: string }
type Group = { id: number; name?: string; teacher?: number | null }
type Teacher = { id: number; user_detail?: { first_name?: string; last_name?: string; telegram_username?: string; email?: string } }

const auth = useAuthStore()
const canManageLessons = ref(false)
const isAdmin = ref(false)
const loading = ref(true)
const savingLesson = ref(false)
const error = ref<string | null>(null)
const detailLoading = ref(false)
const detailError = ref<string | null>(null)
const lessonGroupOpen = ref(false)
const createLessonFormOpen = ref(false)
const dateFilterFrom = ref('')
const dateFilterTo = ref('')
const teacherFilter = ref<number | null>(null)
const rows = ref<Lesson[]>([])
const selectedLesson = ref<Lesson | null>(null)
const groups = ref<Group[]>([])
const teachers = ref<Teacher[]>([])
const participantForms = ref<ParticipantForm[]>([])
let detailRequestSeq = 0

const lessonForm = ref({ group: null as number | null, starts_at_local: '', notes: '' })
const editLessonForm = ref({ group: null as number | null, status: 'scheduled', starts_at_local: '', notes: '' })

const columns = computed(() => {
  const items = [
    { key: 'id', label: 'ID' },
    { key: 'group', label: 'Група', render: (r: Lesson) => groupLabel(r.group) },
    { key: 'status', label: 'Статус', render: (r: Lesson) => lessonStatusLabel(r.status) },
    { key: 'starts_at', label: 'Початок', render: (r: Lesson) => formatLessonDateTime(r.starts_at) },
  ]
  if (isAdmin.value) {
    items.splice(1, 0, { key: 'teacher', label: 'Викладач', render: (r: Lesson) => teacherLabelByGroup(r.group) })
  }
  if (canSeePayroll.value) {
    items.push({ key: 'payroll_amount', label: 'Винагорода вчителя', render: (r: Lesson) => formatPayrollAmount(r.payroll_amount) })
  }
  if (isAdmin.value) {
    items.push({ key: 'billed_amount', label: 'Вартість заняття', render: (r: Lesson) => formatPayrollAmount(r.billed_amount) })
  }
  items.push({ key: 'notes', label: 'Нотатки', render: (r: Lesson) => r.notes || '-' })
  return items
})

const hasDateInterval = computed(() => Boolean(dateFilterFrom.value || dateFilterTo.value))
const hasFilters = computed(() => hasDateInterval.value || teacherFilter.value !== null)
const canSeePayroll = computed(() => canManageLessons.value)
const filteredRows = computed(() => {
  if (!isAdmin.value || teacherFilter.value === null) return rows.value
  return rows.value.filter((lesson) => groupTeacherId(lesson.group) === teacherFilter.value)
})
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

function studentLabel(participant: LessonParticipant) {
  return [participant.student_first_name, participant.student_last_name].filter(Boolean).join(' ') || `Учень #${participant.student}`
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
    billed_amount: String(participant.billed_amount ?? '0.00'),
    payroll_amount: String(participant.payroll_amount ?? '0.00'),
  }))
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
  const requestSeq = ++detailRequestSeq
  selectedLesson.value = lesson
  fillLessonDetailForm({ ...lesson, participants: [] })
  detailLoading.value = true
  detailError.value = null
  try {
    const detail = await apiRequest<LessonDetail>(`/api/academics/lessons/${lesson.id}/`)
    if (requestSeq !== detailRequestSeq) return
    selectedLesson.value = detail
    fillLessonDetailForm(detail)
  } catch (e: any) {
    if (requestSeq !== detailRequestSeq) return
    detailError.value = e?.payload?.detail || e?.message || 'Не вдалося завантажити деталізацію уроку'
  } finally {
    if (requestSeq === detailRequestSeq) detailLoading.value = false
  }
}

async function loadTeacherGroups() {
  if (isAdmin.value) {
    const [groupItems, teacherItems] = await Promise.all([
      apiRequest<Group[]>('/api/academics/groups/'),
      apiRequest<Teacher[]>('/api/users/teachers/'),
    ])
    groups.value = groupItems
    teachers.value = teacherItems
    return
  }
  groups.value = await apiRequest<Group[]>('/api/academics/groups/')
}

async function loadLessons() {
  const params = new URLSearchParams()
  if (dateFilterFrom.value) params.set('date_from', dateFilterFrom.value)
  if (dateFilterTo.value) params.set('date_to', dateFilterTo.value)
  const query = params.toString()
  rows.value = await apiRequest<Lesson[]>(`/api/my/lessons/${query ? `?${query}` : ''}`)
}

async function reloadLessons() {
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

function clearFilters() {
  if (!hasFilters.value) return
  const hadDateFilter = hasDateInterval.value
  dateFilterFrom.value = ''
  dateFilterTo.value = ''
  teacherFilter.value = null
  if (hadDateFilter) void reloadLessons()
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
    await reloadLessons()
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
    const body: Record<string, unknown> = {
      starts_at: new Date(editLessonForm.value.starts_at_local).toISOString(),
      notes: editLessonForm.value.notes,
    }
    if (isAdmin.value) {
      body.status = editLessonForm.value.status
      body.participant_updates = participantForms.value.map((participant) => ({
        id: participant.id,
        billed_amount: participant.billed_amount,
        payroll_amount: participant.payroll_amount,
      }))
    }
    const updated = await apiRequest<LessonDetail>(`/api/academics/lessons/${selectedLesson.value.id}/`, {
      method: 'PATCH',
      body,
    })
    selectedLesson.value = updated
    fillLessonDetailForm(updated as LessonDetail)
    await reloadLessons()
  } catch (e: any) {
    detailError.value = e?.payload?.detail || e?.message || 'Не вдалося оновити урок'
  } finally {
    savingLesson.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await auth.bootstrap()
    canManageLessons.value = auth.me?.role === 'teacher' || auth.me?.role === 'admin' || !!auth.me?.is_staff
    isAdmin.value = auth.me?.role === 'admin' || !!auth.me?.is_staff
    await loadTeacherGroups()
    await loadLessons()
  } catch (e: any) {
    error.value = e?.payload?.detail || e?.message || 'Не вдалося завантажити дані'
  } finally {
    loading.value = false
  }
})

watch(
  () => lessonForm.value.starts_at_local,
  (value) => {
    const normalized = normalizeToQuarterHour(value)
    if (normalized !== value) lessonForm.value.starts_at_local = normalized
  },
)

watch(
  () => editLessonForm.value.starts_at_local,
  (value) => {
    const normalized = normalizeToQuarterHour(value)
    if (normalized !== value) editLessonForm.value.starts_at_local = normalized
  },
)
</script>

<style scoped>
.form {
  margin-bottom: 12px;
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
  grid-template-columns: minmax(160px, 1fr) minmax(160px, 1fr) minmax(180px, 1fr) auto;
  gap: 10px;
  align-items: end;
  margin-bottom: 10px;
}
.filter-clear {
  min-height: 39px;
}
.period-totals {
  display: grid;
  gap: 4px;
  margin-bottom: 10px;
  color: rgba(232, 238, 252, 0.85);
  font-size: 13px;
  font-weight: 650;
}
.lesson-detail {
  display: grid;
  gap: 12px;
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
.participants-table th,
.participants-table td {
  text-align: left;
  padding: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.amount-input {
  min-width: 120px;
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
  border: 1px solid #d0d7de;
  border-radius: 6px;
  padding: 6px;
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
  background: rgba(255, 255, 255, 0.08);
}
@media (max-width: 640px) {
  .filters {
    grid-template-columns: 1fr;
  }
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
