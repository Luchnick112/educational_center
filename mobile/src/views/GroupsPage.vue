<template>
  <ion-page>
    <MobileHeader
      title="Групи"
      :refresh="load"
      :loading="loading"
      :action="canManage ? openCreate : undefined"
      action-label="Створити групу"
    />
    <ion-content :fullscreen="true">
      <div class="page-intro page-intro--compact">
        <p class="eyebrow">Навчання</p>
        <h1>Мої групи</h1>
        <p>Склад і прогрес навчальних груп.</p>
      </div>
      <div class="page-body">
        <p v-if="notice" class="action-notice">{{ notice }}</p>

        <section v-if="canManage" class="filter-panel" aria-label="Фільтри груп">
          <div class="filter-panel__header">
            <h2>Фільтри</h2>
            <ion-button fill="clear" size="small" :disabled="!hasGroupFilters" @click="clearGroupFilters">
              Очистити
            </ion-button>
          </div>
          <div class="filter-grid">
            <label v-if="isAdmin" class="mobile-field">
              <span>Викладач</span>
              <select v-model="groupFilters.teacher" class="mobile-control">
                <option value="">Усі викладачі</option>
                <option v-for="teacher in teachers" :key="teacher.id" :value="String(teacher.id)">
                  {{ profileLabel(teacher, 'Викладач') }}
                </option>
              </select>
            </label>
            <label class="mobile-field">
              <span>Учень</span>
              <select v-model="groupFilters.student" class="mobile-control">
                <option value="">Усі учні</option>
                <option v-for="student in students" :key="student.id" :value="String(student.id)">
                  {{ profileLabel(student, 'Учень') }}
                </option>
              </select>
            </label>
          </div>
        </section>

        <PageState
          :loading="loading"
          :error="error"
          :empty="filteredGroups.length === 0"
          :retry="load"
          :empty-text="hasGroupFilters ? 'За вибраними фільтрами груп немає' : 'Активних груп немає'"
        >
          <div class="item-list">
            <article v-for="group in filteredGroups" :key="group.id" class="data-item data-item--stacked">
              <div class="data-item__topline">
                <div>
                  <h2>{{ group.name || `Група #${group.id}` }}</h2>
                  <span class="format-badge">{{ group.format === 'individual' ? 'Індивідуальна' : 'Групова' }}</span>
                </div>
                <ion-button
                  v-if="canManage"
                  class="icon-action"
                  fill="clear"
                  size="small"
                  :aria-label="`Редагувати ${group.name || `групу ${group.id}`}`"
                  @click="openEdit(group)"
                >
                  <ion-icon slot="icon-only" :icon="createOutline" />
                </ion-button>
              </div>
              <div class="metric-row">
                <div><strong>{{ group.completed_lessons_count ?? 0 }}</strong><span>проведено</span></div>
                <div><strong>{{ group.lessons_until_next_billing ?? '—' }}</strong><span>до оплати</span></div>
                <div><strong>{{ group.capacity ?? '—' }}</strong><span>місць</span></div>
              </div>
            </article>
          </div>
        </PageState>
      </div>
    </ion-content>

    <ion-modal :is-open="editorOpen" @didDismiss="closeEditor">
      <ion-header class="ion-no-border">
        <ion-toolbar>
          <ion-buttons slot="start">
            <ion-button :disabled="saving || savingAttendanceRates" @click="closeEditor">Скасувати</ion-button>
          </ion-buttons>
          <ion-title>{{ editingId ? 'Редагувати групу' : 'Нова група' }}</ion-title>
          <ion-buttons slot="end">
            <ion-button strong :disabled="saving || savingAttendanceRates" @click="saveGroup">Зберегти</ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      <ion-content>
        <form class="mobile-form" @submit.prevent="saveGroup">
          <p v-if="formError" class="form-error form-error--panel">{{ formError }}</p>

          <label class="mobile-field">
            <span>Предмет</span>
            <select v-model.number="form.subject" class="mobile-control" required>
              <option :value="null" disabled>Оберіть предмет</option>
              <option v-for="subject in subjects" :key="subject.id" :value="subject.id">{{ subject.name }}</option>
            </select>
          </label>

          <label v-if="isAdmin" class="mobile-field">
            <span>Викладач</span>
            <select v-model.number="form.teacher" class="mobile-control" required>
              <option :value="null" disabled>Оберіть викладача</option>
              <option v-for="teacher in teachers" :key="teacher.id" :value="teacher.id">{{ profileLabel(teacher, 'Викладач') }}</option>
            </select>
          </label>

          <label class="mobile-field">
            <span>Формат</span>
            <select v-model="form.format" class="mobile-control">
              <option value="group">Групова</option>
              <option value="individual">Індивідуальна</option>
            </select>
          </label>

          <label class="mobile-field">
            <span>Кількість місць</span>
            <input v-model.number="form.capacity" class="mobile-control" type="number" min="1" required />
          </label>

          <div v-if="isAdmin" class="mobile-form-grid">
            <label class="mobile-field">
              <span>Ціна для учня</span>
              <input v-model="form.student_price" class="mobile-control" type="number" min="0" step="0.01" required />
            </label>
            <label class="mobile-field">
              <span>Ставка викладача</span>
              <input v-model="form.teacher_rate" class="mobile-control" type="number" min="0" step="0.01" required />
            </label>
          </div>

          <fieldset v-if="isAdmin && editingId && form.format === 'group'" class="choice-list attendance-rate-section">
            <legend>Виплата викладачу за присутніми</legend>

            <div v-if="loadingAttendanceRates" class="attendance-rate-loading">
              <ion-spinner name="crescent" />
              <span>Завантаження ставок...</span>
            </div>

            <template v-else>
              <label class="mobile-field">
                <span>Дата початку дії</span>
                <input
                  v-model="attendanceRateForm.effective_from_date"
                  class="mobile-control"
                  type="date"
                  @change="hydrateAttendanceRateFormFromRules"
                />
              </label>

              <div class="attendance-rate-grid">
                <label v-for="tier in attendanceRateTiers" :key="tier.present_count" class="mobile-field">
                  <span>{{ tier.label }}</span>
                  <input
                    v-model="attendanceRateForm.rates[tier.present_count]"
                    class="mobile-control"
                    type="number"
                    min="0"
                    step="0.01"
                    inputmode="decimal"
                    placeholder="0.00"
                  />
                </label>
              </div>

              <ion-button
                class="attendance-rate-submit"
                expand="block"
                fill="outline"
                type="button"
                :disabled="savingAttendanceRates || !attendanceRateForm.effective_from_date"
                @click="saveAttendanceRateGrid"
              >
                <ion-spinner v-if="savingAttendanceRates" name="crescent" />
                <span v-else>Зберегти ставки</span>
              </ion-button>
            </template>
          </fieldset>

          <fieldset class="choice-list">
            <legend>Учні</legend>
            <p v-if="students.length === 0" class="field-hint">Доступних учнів немає</p>
            <label v-for="student in students" :key="student.id" class="choice-row">
              <span>{{ profileLabel(student, 'Учень') }}</span>
              <ion-checkbox
                :checked="form.students.includes(student.id)"
                :aria-label="profileLabel(student, 'Учень')"
                @ion-change="toggleStudent(student.id, $event.detail.checked)"
              />
            </label>
          </fieldset>

          <label class="choice-row choice-row--standalone">
            <span>Активна група</span>
            <ion-toggle v-model="form.is_active" aria-label="Активна група" />
          </label>

          <ion-button class="mobile-submit" expand="block" type="submit" :disabled="saving || savingAttendanceRates">
            <ion-spinner v-if="saving" name="crescent" />
            <span v-else>Зберегти групу</span>
          </ion-button>
        </form>
      </ion-content>
    </ion-modal>
  </ion-page>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  IonButton,
  IonButtons,
  IonCheckbox,
  IonContent,
  IonHeader,
  IonIcon,
  IonModal,
  IonPage,
  IonSpinner,
  IonTitle,
  IonToggle,
  IonToolbar,
} from '@ionic/vue'
import { createOutline } from 'ionicons/icons'
import MobileHeader from '@/components/MobileHeader.vue'
import PageState from '@/components/PageState.vue'
import { ApiError, apiRequest, errorMessage } from '@/services/api'
import { usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import type { Enrollment, GroupAttendanceRate, ProfileOption, StudyGroup, Subject } from '@/types/api'

const auth = useAuthStore()
const groups = ref<StudyGroup[]>([])
const subjects = ref<Subject[]>([])
const students = ref<ProfileOption[]>([])
const teachers = ref<ProfileOption[]>([])
const enrollments = ref<Enrollment[]>([])
const editorOpen = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const loadingAttendanceRates = ref(false)
const savingAttendanceRates = ref(false)
const formError = ref('')
const notice = ref('')
const { loading, error, run } = usePageData()

const isAdmin = computed(() => Boolean(auth.me?.is_staff || auth.me?.role === 'admin'))
const canManage = computed(() => isAdmin.value || auth.me?.role === 'teacher')

const groupFilters = reactive({ teacher: '', student: '' })
const hasGroupFilters = computed(() => Boolean(groupFilters.teacher || groupFilters.student))
const filteredGroups = computed(() => groups.value.filter((group) => {
  if (groupFilters.teacher && String(group.teacher ?? '') !== groupFilters.teacher) return false
  if (groupFilters.student) {
    const hasStudent = enrollments.value.some((item) => (
      item.group === group.id
      && item.status === 'active'
      && String(item.student) === groupFilters.student
    ))
    if (!hasStudent) return false
  }
  return true
}))

const form = reactive({
  subject: null as number | null,
  teacher: null as number | null,
  format: 'group',
  capacity: 1,
  student_price: '0.00',
  teacher_rate: '0.00',
  students: [] as number[],
  is_active: true,
})

const attendanceRateTiers = [
  { present_count: 1, label: '1 учень' },
  { present_count: 2, label: '2 учні' },
  { present_count: 3, label: '3 учні' },
  { present_count: 4, label: '4+ учні' },
]
const attendanceRateRules = ref<GroupAttendanceRate[]>([])
const attendanceRateForm = reactive({
  effective_from_date: '',
  rates: emptyAttendanceRateRates(),
})
const selectedGroupAttendanceRateRules = computed(() => {
  if (!editingId.value) return []
  return attendanceRateRules.value
    .filter((rule) => Number(rule.group) === Number(editingId.value))
    .sort((a, b) => (
      a.present_count - b.present_count
      || new Date(b.effective_from).getTime() - new Date(a.effective_from).getTime()
      || b.id - a.id
    ))
})

function clearGroupFilters() {
  Object.assign(groupFilters, { teacher: '', student: '' })
}

function profileLabel(profile: ProfileOption, fallback: string) {
  const user = profile.user_detail
  if (!user) return `${fallback} #${profile.id}`
  return [user.first_name, user.last_name].filter(Boolean).join(' ')
    || user.telegram_username
    || user.email
    || `${fallback} #${profile.id}`
}

function todayDate() {
  const date = new Date()
  const pad = (value: number) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function dateInputValue(value?: string | null) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const pad = (part: number) => String(part).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function emptyAttendanceRateRates() {
  return Object.fromEntries(attendanceRateTiers.map((tier) => [tier.present_count, ''])) as Record<number, string>
}

function resetAttendanceRateForm() {
  attendanceRateForm.effective_from_date = todayDate()
  attendanceRateForm.rates = emptyAttendanceRateRates()
  attendanceRateRules.value = []
}

function currentAttendanceRateRule(presentCount: number, date: string) {
  return selectedGroupAttendanceRateRules.value
    .filter((rule) => Number(rule.present_count) <= presentCount && dateInputValue(rule.effective_from) <= date)
    .sort((a, b) => {
      const byPresentCount = Number(b.present_count) - Number(a.present_count)
      if (byPresentCount !== 0) return byPresentCount
      const byDate = dateInputValue(b.effective_from).localeCompare(dateInputValue(a.effective_from))
      if (byDate !== 0) return byDate
      return b.id - a.id
    })[0]
}

function hydrateAttendanceRateFormFromRules() {
  const date = attendanceRateForm.effective_from_date
  const rates = emptyAttendanceRateRates()
  if (!editingId.value || !date) {
    attendanceRateForm.rates = rates
    return
  }

  for (const tier of attendanceRateTiers) {
    const rule = currentAttendanceRateRule(tier.present_count, date)
    rates[tier.present_count] = rule ? String(rule.teacher_rate) : ''
  }
  attendanceRateForm.rates = rates
}

async function loadAttendanceRateRules(groupId: number) {
  const rules = await apiRequest<GroupAttendanceRate[]>(`/api/academics/group-attendance-rates/?group=${groupId}`)
  attendanceRateRules.value = rules
  hydrateAttendanceRateFormFromRules()
}

async function loadLookups() {
  if (!canManage.value) return
  const [subjectRows, studentRows, enrollmentRows, teacherRows] = await Promise.all([
    apiRequest<Subject[]>('/api/academics/subjects/'),
    apiRequest<ProfileOption[]>('/api/users/students/'),
    apiRequest<Enrollment[]>('/api/academics/enrollments/'),
    isAdmin.value ? apiRequest<ProfileOption[]>('/api/users/teachers/') : Promise.resolve([]),
  ])
  subjects.value = subjectRows
  students.value = studentRows
  enrollments.value = enrollmentRows
  teachers.value = teacherRows
}

const load = () => run(async () => {
  groups.value = await apiRequest<StudyGroup[]>('/api/academics/groups/')
  if (canManage.value) await loadLookups()
})

function resetForm() {
  Object.assign(form, {
    subject: subjects.value[0]?.id ?? null,
    teacher: teachers.value[0]?.id ?? null,
    format: 'group',
    capacity: 1,
    student_price: '0.00',
    teacher_rate: '0.00',
    students: [],
    is_active: true,
  })
  formError.value = ''
}

async function openCreate() {
  try {
    if (!subjects.value.length) await loadLookups()
    editingId.value = null
    resetForm()
    resetAttendanceRateForm()
    editorOpen.value = true
  } catch (caught) {
    error.value = caught instanceof ApiError ? errorMessage(caught.payload) : 'Не вдалося завантажити дані форми'
  }
}

async function openEdit(group: StudyGroup) {
  try {
    if (!subjects.value.length) await loadLookups()
    editingId.value = group.id
    Object.assign(form, {
      subject: group.subject ?? null,
      teacher: group.teacher ?? null,
      format: group.format || 'group',
      capacity: group.capacity ?? 1,
      student_price: group.student_price ?? '0.00',
      teacher_rate: group.teacher_rate ?? '0.00',
      students: enrollments.value
        .filter((item) => item.group === group.id && item.status === 'active')
        .map((item) => item.student),
      is_active: group.is_active ?? true,
    })
    resetAttendanceRateForm()
    formError.value = ''
    editorOpen.value = true
    if (isAdmin.value && form.format === 'group') {
      loadingAttendanceRates.value = true
      try {
        await loadAttendanceRateRules(group.id)
      } catch (caught) {
        formError.value = caught instanceof ApiError
          ? errorMessage(caught.payload, 'Не вдалося завантажити ставки за присутніми')
          : 'Не вдалося завантажити ставки за присутніми'
      } finally {
        loadingAttendanceRates.value = false
      }
    }
  } catch (caught) {
    error.value = caught instanceof ApiError ? errorMessage(caught.payload) : 'Не вдалося завантажити групу'
  }
}

function closeEditor() {
  if (saving.value || savingAttendanceRates.value) return
  editorOpen.value = false
  editingId.value = null
  resetAttendanceRateForm()
  formError.value = ''
}

function toggleStudent(studentId: number, checked: boolean) {
  form.students = checked
    ? Array.from(new Set([...form.students, studentId]))
    : form.students.filter((id) => id !== studentId)
}

async function saveGroup() {
  if (!form.subject || (isAdmin.value && !form.teacher)) {
    formError.value = 'Заповніть предмет і викладача.'
    return
  }

  saving.value = true
  formError.value = ''
  try {
    const body: Record<string, unknown> = {
      subject: form.subject,
      format: form.format,
      capacity: form.format === 'individual' ? 1 : form.capacity,
      is_active: form.is_active,
    }
    if (isAdmin.value) {
      body.teacher = form.teacher
      body.student_price = form.student_price
      body.teacher_rate = form.teacher_rate
    }

    const group = editingId.value
      ? await apiRequest<StudyGroup>(`/api/academics/groups/${editingId.value}/`, { method: 'PATCH', body })
      : await apiRequest<StudyGroup>('/api/academics/groups/', { method: 'POST', body })

    await apiRequest(`/api/academics/groups/${group.id}/students/`, {
      method: 'POST',
      body: { student_ids: form.students },
    })
    notice.value = editingId.value ? 'Групу оновлено.' : 'Групу створено.'
    editorOpen.value = false
    editingId.value = null
    await load()
  } catch (caught) {
    formError.value = caught instanceof ApiError
      ? errorMessage(caught.payload, 'Не вдалося зберегти групу')
      : 'Не вдалося зберегти групу'
  } finally {
    saving.value = false
  }
}

async function saveAttendanceRateGrid() {
  if (!editingId.value || !attendanceRateForm.effective_from_date) return

  const parsedRates = attendanceRateTiers.map((tier) => {
    const raw = attendanceRateForm.rates[tier.present_count] ?? ''
    const rate = Number(String(raw).replace(',', '.'))
    return { ...tier, raw, rate }
  })
  if (parsedRates.some((item) => item.raw === '' || !Number.isFinite(item.rate) || item.rate < 0)) {
    formError.value = 'Заповніть ставки для 1, 2, 3 та 4+ учнів.'
    return
  }

  savingAttendanceRates.value = true
  formError.value = ''
  try {
    const groupId = editingId.value
    const formDate = attendanceRateForm.effective_from_date
    const effectiveFrom = new Date(`${formDate}T00:00:00`).toISOString()

    for (const item of parsedRates) {
      const matchingRules = selectedGroupAttendanceRateRules.value
        .filter((rule) => Number(rule.present_count) === item.present_count && dateInputValue(rule.effective_from) === formDate)
        .sort((a, b) => b.id - a.id)
      const keep = matchingRules[0]

      if (keep) {
        await apiRequest<GroupAttendanceRate>(`/api/academics/group-attendance-rates/${keep.id}/`, {
          method: 'PATCH',
          body: {
            teacher_rate: item.rate.toFixed(2),
            effective_from: effectiveFrom,
          },
        })
      } else {
        await apiRequest<GroupAttendanceRate>('/api/academics/group-attendance-rates/', {
          method: 'POST',
          body: {
            group: groupId,
            present_count: item.present_count,
            teacher_rate: item.rate.toFixed(2),
            effective_from: effectiveFrom,
          },
        })
      }

      for (const duplicate of matchingRules.slice(1)) {
        await apiRequest(`/api/academics/group-attendance-rates/${duplicate.id}/`, { method: 'DELETE' })
      }
    }

    await loadAttendanceRateRules(groupId)
    notice.value = 'Ставки за присутніми збережено.'
  } catch (caught) {
    formError.value = caught instanceof ApiError
      ? errorMessage(caught.payload, 'Не вдалося зберегти ставки за присутніми')
      : 'Не вдалося зберегти ставки за присутніми'
  } finally {
    savingAttendanceRates.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.attendance-rate-section {
  gap: 14px;
  padding: 14px 12px 12px;
}

.attendance-rate-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.attendance-rate-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 72px;
  color: var(--app-muted);
  font-size: 12px;
}

.attendance-rate-loading ion-spinner {
  width: 20px;
  height: 20px;
}

.attendance-rate-submit {
  --border-radius: 6px;
  margin: 0;
}

@media (max-width: 380px) {
  .attendance-rate-grid {
    grid-template-columns: 1fr;
  }
}
</style>
