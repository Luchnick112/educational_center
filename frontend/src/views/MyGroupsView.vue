<template>
  <AppShell :title="isCreateRoute ? 'Створити групу' : 'Мої групи'">
    <div v-if="!isCreateRoute" class="panel groups-panel">
      <div class="panel__title">Список груп</div>
      <div v-if="notice" class="notice">{{ notice }}</div>
      <div class="groups-list">
      <div class="toolbar">
        <button v-if="canManageGroups" class="btn" type="button" @click="openCreateForm">Створити групу</button>
        <button v-if="canManageGroups" class="btn btn--ghost" type="button" :disabled="!selectedGroupId" @click="openEditForm">Редагувати</button>
        <button v-if="isAdmin" class="btn btn--ghost" type="button" :disabled="!selectedGroupId || saving" @click="deleteSelectedGroup">Видалити</button>
      </div>
      <div class="filters">
        <div v-if="isAdmin" class="dropdown">
          <button class="input dropdown__trigger" type="button" @click="teacherFilterOpen = !teacherFilterOpen">{{ selectedTeacherFilterLabel }}</button>
          <div v-if="teacherFilterOpen" class="dropdown__menu dropdown-list">
            <button class="dropdown__option" type="button" @click="setTeacherFilter(null)">Всі вчителі</button>
            <button class="dropdown__option" v-for="t in teachers" :key="t.id" type="button" @click="setTeacherFilter(t.id)">{{ teacherLabel(t.id) }}</button>
          </div>
        </div>
        <div class="dropdown">
          <button class="input dropdown__trigger" type="button" @click="studentFilterOpen = !studentFilterOpen">{{ selectedStudentFilterLabel }}</button>
          <div v-if="studentFilterOpen" class="dropdown__menu dropdown-list">
            <button class="dropdown__option" type="button" @click="setStudentFilter(null)">Всі студенти</button>
            <button class="dropdown__option" v-for="s in students" :key="s.id" type="button" @click="setStudentFilter(s.id)">{{ studentLabel(s) }}</button>
          </div>
        </div>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div v-else-if="loading" class="muted">Завантаження...</div>
      <table v-else class="groups-table">
        <thead>
          <tr>
            <th class="col-teacher">Вчитель</th>
            <th>Назва групи</th>
            <th>Тип</th>
            <th v-if="isAdmin" class="col-student-price">Ціна за навчання</th>
            <th>Ставка вчителя</th>
            <th>Кількість учнів</th>
            <th>Завершено уроків</th>
            <th>До рахунку</th>
            <th class="col-student-list">Список студентів</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in filteredGroupRows"
            :key="row.group.id"
            :class="{ selected: selectedGroupId === row.group.id }"
            @click="openGroupDetail(row.group.id)"
          >
            <td class="col-teacher" data-label="Вчитель">{{ teacherLabel(row.group.teacher) }}</td>
            <td class="col-group-name" data-label="Назва групи">{{ row.group.name || `Група #${row.group.id}` }}</td>
            <td data-label="Тип">{{ groupFormatLabel(row.group.format) }}</td>
            <td v-if="isAdmin" class="col-student-price" data-label="Ціна за навчання">{{ priceLabel(row.group.student_price) }}</td>
            <td data-label="Ставка вчителя">{{ priceLabel(row.group.teacher_rate) }}</td>
            <td data-label="Кількість учнів">{{ row.studentIds.length }}</td>
            <td data-label="Завершено уроків">{{ groupCompletedLessonsLabel(row.group) }}</td>
            <td data-label="До рахунку">{{ groupLessonsUntilBillingLabel(row.group) }}</td>
            <td class="col-student-list" data-label="Список студентів">{{ row.studentNames.join(', ') || '-' }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="!loading && !error" class="mobile-groups-list" aria-label="Список груп">
        <button
          v-for="row in filteredGroupRows"
          :key="row.group.id"
          class="mobile-group-card"
          :class="{ 'mobile-group-card--selected': selectedGroupId === row.group.id }"
          type="button"
          @click="openGroupDetail(row.group.id)"
        >
          <span class="mobile-group-card__header">
            <span class="mobile-group-card__title">{{ row.group.name || `Група #${row.group.id}` }}</span>
            <span class="mobile-group-card__format">{{ groupFormatLabel(row.group.format) }}</span>
          </span>
          <span class="mobile-group-card__teacher">
            <span class="mobile-group-card__label">Вчитель</span>
            <span>{{ teacherLabel(row.group.teacher) }}</span>
          </span>
          <span class="mobile-group-card__stats">
            <span class="mobile-group-card__stat">
              <span class="mobile-group-card__value">{{ row.studentIds.length }}</span>
              <span class="mobile-group-card__label">Учнів</span>
            </span>
            <span class="mobile-group-card__stat">
              <span class="mobile-group-card__value">{{ groupCompletedLessonsLabel(row.group) }}</span>
              <span class="mobile-group-card__label">Завершено</span>
            </span>
            <span class="mobile-group-card__stat">
              <span class="mobile-group-card__value">{{ groupLessonsUntilBillingLabel(row.group) }}</span>
              <span class="mobile-group-card__label">До рахунку</span>
            </span>
          </span>
          <span class="mobile-group-card__prices">
            <span v-if="isAdmin">
              <span class="mobile-group-card__label">Навчання</span>
              <span>{{ priceLabel(row.group.student_price) }}</span>
            </span>
            <span>
              <span class="mobile-group-card__label">Ставка вчителя</span>
              <span>{{ priceLabel(row.group.teacher_rate) }}</span>
            </span>
          </span>
          <span class="mobile-group-card__students">
            <span class="mobile-group-card__label">Студенти</span>
            <span>{{ row.studentNames.join(', ') || 'Немає студентів' }}</span>
          </span>
        </button>
        <div v-if="filteredGroupRows.length === 0" class="mobile-groups-list__empty">Груп не знайдено</div>
      </div>
      </div>
    </div>

    <div
      v-if="!isCreateRoute && selectedGroupDetail && !showEditForm"
      class="group-modal"
      @click.self="closeGroupDetailFromBackdrop"
    >
      <div
        class="panel group-detail group-modal__window group-detail-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="group-detail-title"
      >
        <div class="group-detail__header group-modal__header">
          <div id="group-detail-title" class="group-detail__title">{{ selectedGroupDetail.group.name || `Група #${selectedGroupDetail.group.id}` }}</div>
          <div class="group-detail__actions">
            <button v-if="canManageGroups" class="btn" type="button" @click="openEditForm">Редагувати</button>
            <button class="btn btn--ghost" type="button" @click="closeGroupDetail">Закрити</button>
          </div>
        </div>
        <div class="group-detail__grid">
          <div class="detail-item col-teacher">
            <span class="detail-item__label">Вчитель</span>
            <span>{{ teacherLabel(selectedGroupDetail.group.teacher) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-item__label">Тип</span>
            <span>{{ groupFormatLabel(selectedGroupDetail.group.format) }}</span>
          </div>
          <div v-if="isAdmin" class="detail-item col-student-price">
            <span class="detail-item__label">Ціна за навчання</span>
            <span>{{ priceLabel(selectedGroupDetail.group.student_price) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-item__label">Ставка вчителя</span>
            <span>{{ priceLabel(selectedGroupDetail.group.teacher_rate) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-item__label">Учнів</span>
            <span>{{ selectedGroupDetail.studentIds.length }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-item__label">Завершено уроків</span>
            <span>{{ groupCompletedLessonsLabel(selectedGroupDetail.group) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-item__label">До наступного рахунку</span>
            <span>{{ groupLessonsUntilBillingLabel(selectedGroupDetail.group) }}</span>
          </div>
          <div class="detail-item detail-item--wide col-student-list">
            <span class="detail-item__label">Студенти</span>
            <span>{{ selectedGroupDetail.studentNames.join(', ') || '-' }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="(showCreateForm || isCreateRoute) && canManageGroups" class="panel form create-page">
      <div class="form-title-row">
        <div class="panel__title">Створити групу</div>
        <button class="btn btn--ghost" type="button" :disabled="saving" @click="closeCreatePage">Скасувати</button>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div class="grid">
        <div class="dropdown">
          <button class="input dropdown__trigger" type="button" @click="subjectOpen = !subjectOpen">{{ selectedCreateSubjectLabel }}</button>
          <div v-if="subjectOpen" class="dropdown__menu dropdown-list">
            <button class="dropdown__option" type="button" @click="setCreateSubject(null)">Предмет...</button>
            <button class="dropdown__option" v-for="s in subjects" :key="s.id" type="button" @click="setCreateSubject(s.id)">{{ s.name }}</button>
          </div>
        </div>
        <div v-if="isAdmin" class="dropdown">
          <button class="input dropdown__trigger" type="button" @click="createTeacherOpen = !createTeacherOpen">{{ selectedCreateTeacherLabel }}</button>
          <div v-if="createTeacherOpen" class="dropdown__menu dropdown-list">
            <button class="dropdown__option" type="button" @click="setCreateTeacher(null)">Вчитель...</button>
            <button class="dropdown__option" v-for="t in teachers" :key="t.id" type="button" @click="setCreateTeacher(t.id)">{{ teacherLabel(t.id) }}</button>
          </div>
        </div>
        <label class="field">
          <span class="field__label">Тип</span>
          <select class="input" v-model="createForm.format">
            <option v-for="option in groupFormatOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </label>
        <div v-if="isAdmin" class="field">
          <div class="field__label">Ціна за навчання</div>
          <input class="input" type="number" min="0" step="0.01" v-model.number="createForm.student_price" />
        </div>
        <div v-if="isAdmin" class="field">
          <div class="field__label">Ставка вчителя</div>
          <input class="input" type="number" min="0" step="0.01" v-model.number="createForm.teacher_rate" />
        </div>
        <div class="dropdown">
          <button class="input dropdown__trigger" type="button" @click="createStudentsOpen = !createStudentsOpen">{{ selectedStudentsLabel(createForm.students) }}</button>
          <div v-if="createStudentsOpen" class="dropdown__menu dropdown-list dropdown__menu--static">
            <label v-for="s in students" :key="s.id" class="dropdown__item">
              <input type="checkbox" :checked="createForm.students.includes(s.id)" @change="toggleStudentSelection(createForm.students, s.id)" />
              <span>{{ studentLabel(s) }}</span>
            </label>
          </div>
        </div>
        <button class="btn" type="button" :disabled="saving" @click="createGroup">{{ saving ? 'Збереження...' : 'Створити групу' }}</button>
      </div>
    </div>

    <div
      v-if="showEditForm && editableGroup && canManageGroups"
      class="group-modal"
      @click.self="closeEditFormFromBackdrop"
    >
      <div
        class="panel form group-modal__window group-edit-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="group-edit-title"
      >
      <div class="form-title-row group-modal__header">
        <div id="group-edit-title" class="panel__title">Редагувати групу {{ editableGroup.name || `#${editableGroup.id}` }}</div>
        <button class="btn btn--ghost" type="button" :disabled="saving || savingPricing || savingAttendanceRate" @click="closeEditForm">Скасувати</button>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="notice" class="notice">{{ notice }}</div>
      <div v-if="saving" class="muted">Зберігаю...</div>
      <div class="grid">
        <div class="field">
          <div class="field__label">Предмет</div>
          <div class="dropdown">
            <button class="input dropdown__trigger" type="button" @click="editSubjectOpen = !editSubjectOpen">{{ selectedEditSubjectLabel }}</button>
            <div v-if="editSubjectOpen" class="dropdown__menu dropdown-list">
              <button class="dropdown__option" type="button" @click="setEditSubject(null)">Предмет...</button>
              <button class="dropdown__option" v-for="s in subjects" :key="s.id" type="button" @click="setEditSubject(s.id)">{{ s.name }}</button>
            </div>
          </div>
        </div>
        <div v-if="isAdmin" class="field">
          <div class="field__label">Ціна за навчання</div>
          <input class="input" type="number" min="0" step="0.01" v-model.number="editForm.student_price" placeholder="Ціна за навчання" />
        </div>
        <div v-if="isAdmin" class="field">
          <div class="field__label">Ставка вчителя</div>
          <input class="input" type="number" min="0" step="0.01" v-model.number="editForm.teacher_rate" placeholder="Ставка вчителя" />
        </div>
        <label class="field">
          <span class="field__label">Тип</span>
          <select class="input" v-model="editForm.format">
            <option v-for="option in groupFormatOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </label>
        <div class="field">
          <div class="field__label">Учні групи</div>
          <div class="dropdown">
            <button class="input dropdown__trigger" type="button" @click="editStudentsOpen = !editStudentsOpen">{{ selectedStudentsLabel(editForm.students) }}</button>
            <div v-if="editStudentsOpen" class="dropdown__menu dropdown-list dropdown__menu--static">
              <label v-for="s in students" :key="s.id" class="dropdown__item">
                <input type="checkbox" :checked="editForm.students.includes(s.id)" @change="toggleStudentSelection(editForm.students, s.id)" />
                <span>{{ studentLabel(s) }}</span>
              </label>
            </div>
          </div>
        </div>
        <button class="btn" type="button" :disabled="saving" @click="saveEditedGroup">{{ saving ? 'Збереження...' : 'Зберегти' }}</button>
      </div>

      <div v-if="isAdmin" class="pricing-block">
        <div class="section-title">Ціни з дати</div>
        <div class="pricing-form">
          <label class="field">
            <span class="field__label">Дата з</span>
            <input class="input" type="date" v-model="pricingForm.effective_from_date" />
          </label>
          <label class="field">
            <span class="field__label">Ціна за навчання</span>
            <input class="input" type="number" min="0" step="0.01" v-model.number="pricingForm.student_price" />
          </label>
          <label class="field">
            <span class="field__label">Ставка вчителя</span>
            <input class="input" type="number" min="0" step="0.01" v-model.number="pricingForm.teacher_rate" />
          </label>
          <button class="btn pricing-submit" type="button" :disabled="savingPricing || !pricingForm.effective_from_date" @click="createPricingRule">
            {{ savingPricing ? 'Збереження...' : 'Додати ціну з дати' }}
          </button>
        </div>
        <table v-if="selectedGroupPricingRules.length" class="pricing-table">
          <thead>
            <tr>
              <th>Дата з</th>
              <th>Ціна за навчання</th>
              <th>Ставка вчителя</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rule in selectedGroupPricingRules" :key="rule.id">
              <td>{{ dateLabel(rule.effective_from) }}</td>
              <td>{{ priceLabel(rule.student_price) }}</td>
              <td>{{ priceLabel(rule.teacher_rate) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="muted">Правил цін ще немає</div>
      </div>

      <div v-if="isAdmin && editForm.format === 'group'" class="pricing-block">
        <div class="section-title">Виплата вчителю за присутніми</div>
        <div class="attendance-rate-form">
          <label class="field">
            <span class="field__label">Дата з</span>
            <input class="input" type="date" v-model="attendanceRateForm.effective_from_date" @change="hydrateAttendanceRateFormFromRules" />
          </label>
          <div class="attendance-rate-grid">
            <label v-for="tier in attendanceRateTiers" :key="tier.present_count" class="field">
              <span class="field__label">{{ tier.label }}</span>
              <input
                class="input"
                type="number"
                min="0"
                step="0.01"
                v-model="attendanceRateForm.rates[tier.present_count]"
                placeholder="0.00"
              />
            </label>
          </div>
          <button class="btn pricing-submit" type="button" :disabled="savingAttendanceRate || !attendanceRateForm.effective_from_date" @click="saveAttendanceRateGrid">
            {{ savingAttendanceRate ? 'Збереження...' : 'Зберегти ставки' }}
          </button>
        </div>
        <table v-if="selectedGroupAttendanceRateRules.length" class="pricing-table">
          <thead>
            <tr>
              <th>Дата з</th>
              <th>Присутніх від</th>
              <th>Ставка вчителя</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rule in selectedGroupAttendanceRateRules" :key="rule.id">
              <td>{{ dateLabel(rule.effective_from) }}</td>
              <td>{{ rule.present_count }}+</td>
              <td>{{ priceLabel(rule.teacher_rate) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="muted">Ставок за присутніми ще немає</div>
      </div>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { apiRequest } from '@/lib/api'
import { pushDetailRoute, replaceWithoutDetailRoute, routeQueryId } from '@/lib/detailRoute'
import { useAuthStore } from '@/stores/auth'

type Subject = { id: number; name: string }
type Student = { id: number; user_detail?: { first_name?: string; last_name?: string; email?: string; telegram_username?: string } }
type Teacher = { id: number; user_detail?: { first_name?: string; last_name?: string; telegram_username?: string; email?: string } }
type GroupFormat = 'group' | 'individual'
type Group = {
  id: number
  name?: string
  teacher?: number | null
  subject?: number | null
  format?: GroupFormat | string | null
  capacity?: number | null
  student_price?: string | number | null
  teacher_rate?: string | number | null
  completed_lessons_count?: number | null
  lessons_until_next_billing?: number | null
}
type GroupPricing = { id: number; group: number; group_name?: string; student_price: string | number; teacher_rate: string | number; effective_from: string; created_at?: string }
type GroupAttendanceRate = { id: number; group: number; group_name?: string; present_count: number; teacher_rate: string | number; effective_from: string; created_at?: string }
type Enrollment = {
  id: number
  group: number
  student: number
  status: string
  end_date?: string | null
  student_first_name?: string
  student_last_name?: string
  student_email?: string
  student_telegram_username?: string
}

const groupFormatOptions: Array<{ value: GroupFormat; label: string }> = [
  { value: 'group', label: 'Груповий' },
  { value: 'individual', label: 'Індивідуальний' },
]

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const canManageGroups = ref(false)
const isAdmin = ref(false)
const loading = ref(true)
const saving = ref(false)
const savingPricing = ref(false)
const savingAttendanceRate = ref(false)
const error = ref<string | null>(null)
const notice = ref<string | null>(null)
const selectedGroupId = ref<number | null>(null)
let bodyOverflowBeforeGroupModal: string | null = null

const subjectOpen = ref(false)
const editSubjectOpen = ref(false)
const createTeacherOpen = ref(false)
const createStudentsOpen = ref(false)
const editStudentsOpen = ref(false)
const teacherFilterOpen = ref(false)
const studentFilterOpen = ref(false)

const showCreateForm = ref(false)
const showEditForm = ref(false)

const teacherFilter = ref<number | null>(null)
const studentFilter = ref<number | null>(null)

const subjects = ref<Subject[]>([])
const students = ref<Student[]>([])
const teachers = ref<Teacher[]>([])
const groups = ref<Group[]>([])
const enrollments = ref<Enrollment[]>([])
const pricingRules = ref<GroupPricing[]>([])
const attendanceRateRules = ref<GroupAttendanceRate[]>([])
const attendanceRateTiers = [
  { present_count: 1, label: '1 учень' },
  { present_count: 2, label: '2 учні' },
  { present_count: 3, label: '3 учні' },
  { present_count: 4, label: '4+ учні' },
]

const createForm = ref({
  subject: null as number | null,
  teacher: null as number | null,
  format: 'group' as GroupFormat,
  capacity: 1,
  student_price: 0,
  teacher_rate: 0,
  students: [] as number[],
})
const editForm = ref({ subject: null as number | null, format: 'group' as GroupFormat, student_price: 0, teacher_rate: 0, students: [] as number[] })
const pricingForm = ref({ effective_from_date: '', student_price: 0, teacher_rate: 0 })
const attendanceRateForm = ref({
  effective_from_date: '',
  rates: Object.fromEntries(attendanceRateTiers.map((tier) => [tier.present_count, ''])) as Record<number, string>,
})
const isCreateRoute = computed(() => route.name === 'my-groups-create')
const DETAIL_QUERY_KEY = 'group'
const LIST_ROUTE_NAME = 'my-groups'

const editableGroup = computed(() => groups.value.find((g) => g.id === selectedGroupId.value) || null)
const selectedGroupPricingRules = computed(() => {
  if (!selectedGroupId.value) return []
  return pricingRules.value
    .filter((rule) => Number(rule.group) === Number(selectedGroupId.value))
    .sort((a, b) => new Date(b.effective_from).getTime() - new Date(a.effective_from).getTime() || b.id - a.id)
})

const selectedGroupAttendanceRateRules = computed(() => {
  if (!selectedGroupId.value) return []
  return attendanceRateRules.value
    .filter((rule) => Number(rule.group) === Number(selectedGroupId.value))
    .sort((a, b) => a.present_count - b.present_count || new Date(b.effective_from).getTime() - new Date(a.effective_from).getTime() || b.id - a.id)
})

const selectedCreateSubjectLabel = computed(() => {
  if (!createForm.value.subject) return 'Предмет...'
  return subjects.value.find((s) => s.id === createForm.value.subject)?.name || 'Предмет...'
})

const selectedCreateTeacherLabel = computed(() => {
  if (!createForm.value.teacher) return 'Вчитель...'
  return teacherLabel(createForm.value.teacher)
})

const selectedEditSubjectLabel = computed(() => {
  if (!editForm.value.subject) return 'Предмет...'
  return subjects.value.find((s) => s.id === editForm.value.subject)?.name || 'Предмет...'
})

const sortedGroups = computed(() => {
  return [...groups.value].sort((a, b) => {
    const ta = teacherLabel(a.teacher)
    const tb = teacherLabel(b.teacher)
    const byTeacher = ta.localeCompare(tb, 'uk')
    if (byTeacher !== 0) return byTeacher
    return (a.name || `Група #${a.id}`).localeCompare(b.name || `Група #${b.id}`, 'uk')
  })
})

const groupRows = computed(() => {
  return sortedGroups.value.map((group) => ({
    group,
    studentIds: activeStudentIdsByGroup(group.id),
    studentNames: activeStudentLabelsByGroup(group.id),
  }))
})

const filteredGroupRows = computed(() => {
  return groupRows.value.filter((row) => {
    if (teacherFilter.value && Number(row.group.teacher) !== Number(teacherFilter.value)) return false
    if (studentFilter.value && !row.studentIds.includes(Number(studentFilter.value))) return false
    return true
  })
})

const selectedGroupDetail = computed(() => groupRows.value.find((row) => row.group.id === selectedGroupId.value) || null)
const isGroupModalOpen = computed(() => !isCreateRoute.value && (!!selectedGroupDetail.value || showEditForm.value))

const selectedTeacherFilterLabel = computed(() => (teacherFilter.value ? teacherLabel(teacherFilter.value) : 'Всі вчителі'))
const selectedStudentFilterLabel = computed(() => {
  if (!studentFilter.value) return 'Всі студенти'
  const s = students.value.find((x) => x.id === studentFilter.value)
  return s ? studentLabel(s) : `Учень #${studentFilter.value}`
})

function studentLabel(s: Student) {
  const u = s.user_detail || {}
  return [u.first_name, u.last_name].filter(Boolean).join(' ') || u.telegram_username || u.email || `Учень #${s.id}`
}

function studentLabelById(studentId: number) {
  const student = students.value.find((s) => Number(s.id) === Number(studentId))
  return student ? studentLabel(student) : `Учень #${studentId}`
}

function enrollmentStudentLabel(enrollment: Enrollment) {
  return (
    [enrollment.student_first_name, enrollment.student_last_name].filter(Boolean).join(' ') ||
    enrollment.student_telegram_username ||
    enrollment.student_email ||
    studentLabelById(enrollment.student)
  )
}

function teacherLabel(teacherId?: number | null) {
  if (!teacherId) return '-'
  const t = teachers.value.find((x) => x.id === teacherId)
  if (!t) return `Вчитель #${teacherId}`
  const u = t.user_detail || {}
  return [u.first_name, u.last_name].filter(Boolean).join(' ') || u.telegram_username || u.email || `Вчитель #${teacherId}`
}

function groupFormatLabel(format?: string | null) {
  return groupFormatOptions.find((option) => option.value === format)?.label || 'Груповий'
}

function priceLabel(value?: string | number | null) {
  if (value === null || value === undefined || value === '') return '-'
  const n = Number(value)
  return Number.isFinite(n) ? n.toFixed(2) : String(value)
}

function isGroupFormat(group: Group) {
  return (group.format || 'group') === 'group'
}

function groupCompletedLessonsLabel(group: Group) {
  if (!isGroupFormat(group)) return '-'
  return String(group.completed_lessons_count ?? 0)
}

function groupLessonsUntilBillingLabel(group: Group) {
  if (!isGroupFormat(group)) return '-'
  return String(group.lessons_until_next_billing ?? '-')
}

function dateLabel(value?: string | null) {
  if (!value) return '-'
  const d = new Date(value)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()}`
}

function dateInputValue(value?: string | null) {
  if (!value) return ''
  const d = new Date(value)
  if (isNaN(d.getTime())) return ''
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function attendanceRateIsoDate() {
  return new Date(`${attendanceRateForm.value.effective_from_date}T00:00:00`).toISOString()
}

function emptyAttendanceRateRates() {
  return Object.fromEntries(attendanceRateTiers.map((tier) => [tier.present_count, ''])) as Record<number, string>
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
  const groupId = selectedGroupId.value
  const date = attendanceRateForm.value.effective_from_date
  const rates = emptyAttendanceRateRates()
  if (!groupId || !date) {
    attendanceRateForm.value.rates = rates
    return
  }

  for (const tier of attendanceRateTiers) {
    const rule = currentAttendanceRateRule(tier.present_count, date)
    rates[tier.present_count] = rule ? String(rule.teacher_rate) : ''
  }
  attendanceRateForm.value.rates = rates
}

function parseMoneyInput(value: string) {
  return Number(String(value).replace(',', '.'))
}

function apiErrorMessage(e: any, fallback: string) {
  const payload = e?.payload
  if (payload?.detail) return String(payload.detail)
  if (payload && typeof payload === 'object') {
    const labels: Record<string, string> = {
      teacher: 'Вчитель',
      subject: 'Предмет',
      student_price: 'Ціна за навчання',
      teacher_rate: 'Ставка вчителя',
      student_ids: 'Учні',
      non_field_errors: 'Помилка',
    }
    return Object.entries(payload)
      .map(([field, messages]) => {
        const text = Array.isArray(messages) ? messages.join(', ') : String(messages)
        const translated = text
          .replace('This field is required.', "обов'язкове поле")
          .replace('This field may not be null.', "обов'язкове поле")
        return `${labels[field] || field}: ${translated}`
      })
      .join('; ')
  }
  return e?.message || fallback
}

function selectedStudentsLabel(ids: number[]) {
  if (!ids.length) return 'Оберіть учнів...'
  if (ids.length === 1) {
    const student = students.value.find((s) => s.id === ids[0])
    return student ? studentLabel(student) : `Учень #${ids[0]}`
  }
  return `Обрано учнів: ${ids.length}`
}

function toggleStudentSelection(target: number[], studentId: number) {
  notice.value = null
  error.value = null
  const idx = target.indexOf(studentId)
  if (idx >= 0) target.splice(idx, 1)
  else target.push(studentId)
}

function setCreateSubject(subjectId: number | null) {
  notice.value = null
  error.value = null
  createForm.value.subject = subjectId
  subjectOpen.value = false
}

function setEditSubject(subjectId: number | null) {
  notice.value = null
  error.value = null
  editForm.value.subject = subjectId
  editSubjectOpen.value = false
}

function setCreateTeacher(teacherId: number | null) {
  notice.value = null
  error.value = null
  createForm.value.teacher = teacherId
  createTeacherOpen.value = false
}

function setTeacherFilter(teacherId: number | null) {
  teacherFilter.value = teacherId
  teacherFilterOpen.value = false
}

function setStudentFilter(studentId: number | null) {
  studentFilter.value = studentId
  studentFilterOpen.value = false
}

function activeEnrollmentsByGroup(groupId: number) {
  return enrollments.value.filter((e) => Number(e.group) === Number(groupId) && isActiveEnrollment(e))
}

function activeStudentIdsByGroup(groupId: number) {
  return [...new Set(activeEnrollmentsByGroup(groupId).map((e) => Number(e.student)))]
}

function activeStudentLabelsByGroup(groupId: number) {
  return activeEnrollmentsByGroup(groupId).map((e) => enrollmentStudentLabel(e))
}

function isActiveEnrollment(enrollment: Enrollment) {
  return String(enrollment.status).toLowerCase() === 'active' && !enrollment.end_date
}

function activeEnrollmentCount(items: Enrollment[]) {
  return items.filter((e) => isActiveEnrollment(e)).length
}

function activeStudentIdsFromEnrollments(items: Enrollment[]) {
  return [...new Set(items.filter((e) => isActiveEnrollment(e)).map((e) => Number(e.student)))]
}

function replaceGroupEnrollments(groupId: number, updatedGroupEnrollments: Enrollment[]) {
  enrollments.value = [
    ...enrollments.value.filter((e) => Number(e.group) !== Number(groupId)),
    ...updatedGroupEnrollments,
  ]
}

function removeGroupFromState(groupId: number) {
  groups.value = groups.value.filter((g) => Number(g.id) !== Number(groupId))
  enrollments.value = enrollments.value.filter((e) => Number(e.group) !== Number(groupId))
  pricingRules.value = pricingRules.value.filter((rule) => Number(rule.group) !== Number(groupId))
  attendanceRateRules.value = attendanceRateRules.value.filter((rule) => Number(rule.group) !== Number(groupId))
}

function todayDate() {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

async function syncGroupStudents(groupId: number, studentIds: number[]) {
  const updatedGroupEnrollments = await apiRequest<Enrollment[]>(`/api/academics/groups/${groupId}/students/`, {
    method: 'POST',
    body: { student_ids: studentIds.map(Number) },
  })
  replaceGroupEnrollments(groupId, updatedGroupEnrollments)
  return updatedGroupEnrollments
}

async function loadData() {
  const [t, sub, st, gr, en] = await Promise.all([
    apiRequest<Teacher[]>('/api/users/teachers/'),
    apiRequest<Subject[]>('/api/academics/subjects/'),
    apiRequest<Student[]>('/api/users/students/'),
    apiRequest<Group[]>('/api/academics/groups/'),
    apiRequest<Enrollment[]>('/api/academics/enrollments/'),
  ])
  teachers.value = t
  subjects.value = sub
  students.value = st
  groups.value = gr
  enrollments.value = en
}

async function loadPricingRules(groupId?: number | null) {
  if (!isAdmin.value) return
  const query = groupId ? `?group=${groupId}` : ''
  const rules = await apiRequest<GroupPricing[]>(`/api/academics/group-pricings/${query}`)
  if (groupId) {
    pricingRules.value = [
      ...pricingRules.value.filter((rule) => Number(rule.group) !== Number(groupId)),
      ...rules,
    ]
    return
  }
  pricingRules.value = rules
}

async function loadAttendanceRateRules(groupId?: number | null) {
  if (!isAdmin.value) return
  const query = groupId ? `?group=${groupId}` : ''
  const rules = await apiRequest<GroupAttendanceRate[]>(`/api/academics/group-attendance-rates/${query}`)
  if (groupId) {
    attendanceRateRules.value = [
      ...attendanceRateRules.value.filter((rule) => Number(rule.group) !== Number(groupId)),
      ...rules,
    ]
    hydrateAttendanceRateFormFromRules()
    return
  }
  attendanceRateRules.value = rules
}

function openCreateForm() {
  router.push({ name: 'my-groups-create' })
}

function resetCreateForm() {
  notice.value = null
  error.value = null
  createForm.value = {
    subject: null,
    teacher: null,
    format: 'group',
    capacity: 1,
    student_price: 0,
    teacher_rate: 0,
    students: [],
  }
  subjectOpen.value = false
  createTeacherOpen.value = false
  createStudentsOpen.value = false
  showEditForm.value = false
  showCreateForm.value = true
}

function closeCreatePage() {
  router.push({ name: LIST_ROUTE_NAME })
}

async function openGroupDetail(id: number) {
  if (await pushDetailRoute(router, route, DETAIL_QUERY_KEY, id)) return
  selectedGroupId.value = id
}

async function closeGroupDetail() {
  selectedGroupId.value = null
  showEditForm.value = false
  await replaceWithoutDetailRoute(router, route, LIST_ROUTE_NAME, DETAIL_QUERY_KEY)
}

function closeGroupDetailFromBackdrop() {
  if (!saving.value) void closeGroupDetail()
}

function closeEditForm() {
  if (saving.value || savingPricing.value || savingAttendanceRate.value) return
  showEditForm.value = false
  editSubjectOpen.value = false
  editStudentsOpen.value = false
  error.value = null
}

function closeEditFormFromBackdrop() {
  closeEditForm()
}

function onWindowKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape') return
  if (showEditForm.value) {
    closeEditForm()
    return
  }
  if (selectedGroupDetail.value && !saving.value) {
    void closeGroupDetail()
  }
}

function syncGroupDetailFromRoute() {
  if (isCreateRoute.value) return
  selectedGroupId.value = routeQueryId(route, DETAIL_QUERY_KEY)
}

function openEditForm() {
  if (!editableGroup.value) return
  notice.value = null
  error.value = null
  const g = editableGroup.value
  showCreateForm.value = false
  showEditForm.value = true
  editForm.value.subject = g.subject || null
  editForm.value.format = g.format === 'individual' ? 'individual' : 'group'
  editForm.value.student_price = Number(g.student_price || 0)
  editForm.value.teacher_rate = Number(g.teacher_rate || 0)
  editForm.value.students = activeStudentIdsByGroup(g.id)
  pricingForm.value = {
    effective_from_date: todayDate(),
    student_price: Number(g.student_price || 0),
    teacher_rate: Number(g.teacher_rate || 0),
  }
  attendanceRateForm.value = {
    effective_from_date: todayDate(),
    rates: emptyAttendanceRateRates(),
  }
  void loadPricingRules(g.id)
  void loadAttendanceRateRules(g.id)
}

async function createGroup() {
  if (!createForm.value.subject) return
  if (isAdmin.value && !createForm.value.teacher) {
    error.value = 'Оберіть вчителя'
    return
  }
  saving.value = true
  error.value = null
  notice.value = null
  try {
    const body: Record<string, unknown> = {
      subject: createForm.value.subject,
      format: createForm.value.format,
      capacity: createForm.value.capacity,
      is_active: true,
    }
    if (isAdmin.value) {
      body.teacher = createForm.value.teacher
      body.student_price = createForm.value.student_price
      body.teacher_rate = createForm.value.teacher_rate
    }
    const created = await apiRequest<Group>('/api/academics/groups/', {
      method: 'POST',
      body,
    })
    const updatedGroupEnrollments = await syncGroupStudents(created.id, createForm.value.students)
    await loadData()
    replaceGroupEnrollments(created.id, updatedGroupEnrollments)
    selectedGroupId.value = created.id
    showCreateForm.value = false
    notice.value = `Групу створено. Активних учнів: ${activeEnrollmentCount(updatedGroupEnrollments)}`
    if (isCreateRoute.value) {
      await router.push({ name: LIST_ROUTE_NAME, query: { [DETAIL_QUERY_KEY]: String(created.id) } })
    } else {
      await pushDetailRoute(router, route, DETAIL_QUERY_KEY, created.id)
    }
  } catch (e: any) {
    error.value = apiErrorMessage(e, 'Не вдалося створити групу')
  } finally {
    saving.value = false
  }
}

async function saveEditedGroup() {
  if (!editableGroup.value) return
  saving.value = true
  error.value = null
  notice.value = null
  try {
    const groupId = editableGroup.value.id
    const body: Record<string, unknown> = {
      subject: editForm.value.subject,
      format: editForm.value.format,
    }
    if (isAdmin.value) {
      body.student_price = editForm.value.student_price
      body.teacher_rate = editForm.value.teacher_rate
    }
    await apiRequest(`/api/academics/groups/${groupId}/`, { method: 'PATCH', body })
    const updatedGroupEnrollments = await syncGroupStudents(groupId, editForm.value.students)
    await loadData()
    replaceGroupEnrollments(groupId, updatedGroupEnrollments)
    selectedGroupId.value = groupId
    editForm.value.students = activeStudentIdsFromEnrollments(updatedGroupEnrollments)
    showEditForm.value = false
    editSubjectOpen.value = false
    editStudentsOpen.value = false
    notice.value = `Групу збережено. Активних учнів: ${activeEnrollmentCount(updatedGroupEnrollments)}`
    await pushDetailRoute(router, route, DETAIL_QUERY_KEY, groupId)
  } catch (e: any) {
    error.value = apiErrorMessage(e, 'Не вдалося зберегти групу')
  } finally {
    saving.value = false
  }
}

async function deleteSelectedGroup() {
  const group = editableGroup.value
  if (!group) return
  const label = group.name || `#${group.id}`
  if (!window.confirm(`Видалити групу ${label}?`)) return

  saving.value = true
  error.value = null
  notice.value = null
  try {
    await apiRequest(`/api/academics/groups/${group.id}/`, { method: 'DELETE' })
    removeGroupFromState(group.id)
    selectedGroupId.value = null
    showCreateForm.value = false
    showEditForm.value = false
    await replaceWithoutDetailRoute(router, route, LIST_ROUTE_NAME, DETAIL_QUERY_KEY)
    notice.value = 'Групу видалено'
  } catch (e: any) {
    if (e?.status === 404) {
      removeGroupFromState(group.id)
      selectedGroupId.value = null
      showCreateForm.value = false
      showEditForm.value = false
      await replaceWithoutDetailRoute(router, route, LIST_ROUTE_NAME, DETAIL_QUERY_KEY)
      notice.value = 'Групу вже видалено'
      return
    }
    error.value = apiErrorMessage(e, 'Не вдалося видалити групу')
  } finally {
    saving.value = false
  }
}

async function createPricingRule() {
  if (!editableGroup.value || !pricingForm.value.effective_from_date) return
  savingPricing.value = true
  error.value = null
  notice.value = null
  try {
    const groupId = editableGroup.value.id
    await apiRequest<GroupPricing>('/api/academics/group-pricings/', {
      method: 'POST',
      body: {
        group: groupId,
        student_price: pricingForm.value.student_price,
        teacher_rate: pricingForm.value.teacher_rate,
        effective_from: new Date(`${pricingForm.value.effective_from_date}T00:00:00`).toISOString(),
      },
    })
    await loadPricingRules(groupId)
    notice.value = 'Ціну з дати додано'
  } catch (e: any) {
    error.value = apiErrorMessage(e, 'Не вдалося додати ціну з дати')
  } finally {
    savingPricing.value = false
  }
}

async function saveAttendanceRateGrid() {
  if (!editableGroup.value || !attendanceRateForm.value.effective_from_date) return

  const parsedRates = attendanceRateTiers.map((tier) => {
    const raw = attendanceRateForm.value.rates[tier.present_count] ?? ''
    const rate = parseMoneyInput(raw)
    return { ...tier, raw, rate }
  })
  if (parsedRates.some((item) => item.raw === '' || !Number.isFinite(item.rate) || item.rate < 0)) {
    error.value = 'Заповніть ставки для 1, 2, 3 та 4+ учнів'
    return
  }

  savingAttendanceRate.value = true
  error.value = null
  notice.value = null
  try {
    const groupId = editableGroup.value.id
    const effectiveFrom = attendanceRateIsoDate()
    const formDate = attendanceRateForm.value.effective_from_date

    for (const item of parsedRates) {
      const matchingRules = selectedGroupAttendanceRateRules.value
        .filter((rule) => Number(rule.present_count) === item.present_count && dateInputValue(rule.effective_from) === formDate)
        .sort((a, b) => b.id - a.id)

      const keep = matchingRules[0]
      const duplicateRules = matchingRules.slice(1)

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

      for (const duplicate of duplicateRules) {
        await apiRequest(`/api/academics/group-attendance-rates/${duplicate.id}/`, { method: 'DELETE' })
      }
    }

    await loadAttendanceRateRules(groupId)
    notice.value = 'Ставки за присутніми збережено'
  } catch (e: any) {
    error.value = apiErrorMessage(e, 'Не вдалося зберегти ставки за присутніми')
  } finally {
    savingAttendanceRate.value = false
  }
}

onMounted(async () => {
  window.addEventListener('keydown', onWindowKeydown)
  loading.value = true
  try {
    await auth.bootstrap()
    canManageGroups.value = auth.me?.role === 'teacher' || auth.me?.role === 'admin' || !!auth.me?.is_staff
    isAdmin.value = auth.me?.role === 'admin' || !!auth.me?.is_staff
    if (canManageGroups.value) await loadData()
    if (isAdmin.value) {
      await loadPricingRules()
      await loadAttendanceRateRules()
    }
    if (isCreateRoute.value) resetCreateForm()
    else syncGroupDetailFromRoute()
  } catch (e: any) {
    error.value = apiErrorMessage(e, 'Не вдалося завантажити дані')
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onWindowKeydown)
  if (bodyOverflowBeforeGroupModal !== null) {
    document.body.style.overflow = bodyOverflowBeforeGroupModal
  }
})

watch(isGroupModalOpen, (open) => {
  if (open) {
    bodyOverflowBeforeGroupModal = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return
  }

  if (bodyOverflowBeforeGroupModal !== null) {
    document.body.style.overflow = bodyOverflowBeforeGroupModal
    bodyOverflowBeforeGroupModal = null
  }
})

watch(
  () => route.name,
  (name) => {
    if (name === 'my-groups-create') {
      resetCreateForm()
    } else {
      showCreateForm.value = false
      syncGroupDetailFromRoute()
    }
  },
)

watch(
  () => route.query[DETAIL_QUERY_KEY],
  () => syncGroupDetailFromRoute(),
)
</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.form { margin-bottom: 12px; }
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
.grid { display: grid; gap: 10px; }
.dropdown { position: relative; }
.dropdown__trigger { width: 100%; text-align: left; }
.dropdown__menu {
  position: absolute;
  z-index: 10;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  max-height: 240px;
  overflow: auto;
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  padding: 6px;
  background: var(--surface);
  box-shadow: var(--shadow-lg);
}
.dropdown__menu--static {
  position: static;
  margin-top: 4px;
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
.dropdown__option:hover { background: var(--surface-hover); }
.dropdown__item { display: flex; align-items: center; gap: 8px; padding: 6px; }
.notice { color: var(--success); font-size: 13px; margin-bottom: 10px; }
.groups-table { width: 100%; border-collapse: collapse; }
.mobile-groups-list { display: none; }
.filters { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
.groups-table th, .groups-table td, .pricing-table th, .pricing-table td { text-align: left; padding: 8px; border-bottom: 1px solid var(--border); }
.groups-table tbody tr { cursor: pointer; }
.groups-table tbody tr:hover { background: var(--surface-hover); }
.groups-table tbody tr.selected {
  background: var(--accent-soft);
  box-shadow: inset 3px 0 0 var(--accent);
}
.group-modal {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgba(15, 23, 42, 0.48);
}
.group-modal__window {
  width: min(1040px, 100%);
  max-height: calc(100vh - 36px);
  margin: 0;
  overflow: auto;
}
.group-detail-modal {
  width: min(720px, 100%);
}
.group-detail__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.group-detail {
  margin: 0;
}
.group-detail__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}
.group-detail__title {
  font-weight: 650;
}
.group-detail__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 14px;
}
.detail-item {
  display: grid;
  gap: 2px;
  min-width: 0;
  font-size: 14px;
}
.detail-item--wide {
  grid-column: 1 / -1;
}
.detail-item__label {
  color: var(--text-soft);
  font-size: 12px;
}
.pricing-block {
  margin-top: 16px;
  display: grid;
  gap: 10px;
}
.section-title {
  font-weight: 650;
}
.pricing-form {
  display: grid;
  grid-template-columns: minmax(150px, 1fr) minmax(150px, 1fr) minmax(150px, 1fr) auto;
  gap: 10px;
  align-items: end;
}
.attendance-rate-form {
  display: grid;
  grid-template-columns: minmax(150px, 0.8fr) minmax(320px, 2fr) auto;
  gap: 10px;
  align-items: end;
}
.attendance-rate-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(80px, 1fr));
  gap: 10px;
}
.pricing-submit {
  min-height: 39px;
}
.pricing-table {
  width: 100%;
  border-collapse: collapse;
}
@media (max-width: 760px) {
  .group-modal {
    place-items: stretch;
    padding: 0;
  }
  .group-modal__window {
    width: 100%;
    height: 100dvh;
    max-height: 100dvh;
    border-radius: 0;
    padding-bottom: 20px;
  }
  .group-detail {
    margin-top: 0;
    border-top: 0;
    padding-top: 0;
  }
  .group-modal__header {
    position: sticky;
    top: 0;
    z-index: 2;
    margin: -14px -14px 14px;
    padding: 12px 14px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
  }
  .group-detail__actions {
    flex: 0 0 auto;
  }
  .group-detail__title {
    font-size: 18px;
    line-height: 1.25;
  }
  .toolbar {
    display: grid;
    grid-template-columns: 1fr;
  }
  .toolbar .btn {
    width: 100%;
  }
  .pricing-table {
    display: block;
    max-width: 100%;
    overflow-x: auto;
    white-space: nowrap;
  }

  .groups-table {
    display: none;
  }
  .mobile-groups-list {
    display: grid;
    gap: 8px;
  }
  .mobile-group-card {
    display: grid;
    gap: 12px;
    width: 100%;
    min-width: 0;
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--surface-soft);
    color: var(--text);
    text-align: left;
    cursor: pointer;
  }
  .mobile-group-card:active {
    border-color: var(--accent-border);
    background: var(--accent-hover);
  }
  .mobile-group-card--selected {
    border-color: var(--accent-border);
    background: var(--accent-soft);
    box-shadow: inset 3px 0 0 var(--accent);
  }
  .mobile-group-card__header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
  }
  .mobile-group-card__title {
    min-width: 0;
    font-size: 15px;
    font-weight: 700;
    line-height: 1.3;
    overflow-wrap: anywhere;
  }
  .mobile-group-card__format {
    flex: 0 0 auto;
    padding: 3px 7px;
    border: 1px solid var(--border-strong);
    border-radius: 999px;
    color: var(--text-soft);
    font-size: 12px;
  }
  .mobile-group-card__teacher,
  .mobile-group-card__students {
    display: grid;
    gap: 3px;
    min-width: 0;
    line-height: 1.35;
    overflow-wrap: anywhere;
  }
  .mobile-group-card__stats {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    border-block: 1px solid var(--border);
  }
  .mobile-group-card__stat {
    display: grid;
    gap: 2px;
    padding: 10px 8px;
    text-align: center;
  }
  .mobile-group-card__stat + .mobile-group-card__stat {
    border-left: 1px solid var(--border);
  }
  .mobile-group-card__value {
    font-size: 16px;
    font-weight: 700;
  }
  .mobile-group-card__label {
    display: block;
    color: var(--muted);
    font-size: 11px;
    line-height: 1.3;
  }
  .mobile-group-card__prices {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    font-size: 13px;
  }
  .mobile-group-card__prices > span {
    display: grid;
    gap: 3px;
  }
  .mobile-group-card__prices > span:only-child {
    grid-column: 1 / -1;
  }
  .mobile-groups-list__empty {
    padding: 20px 12px;
    border: 1px dashed var(--border-strong);
    border-radius: 8px;
    color: var(--muted);
    text-align: center;
  }
  .filters {
    grid-template-columns: 1fr;
  }
  .group-detail__grid {
    grid-template-columns: 1fr;
  }
  .pricing-form {
    grid-template-columns: 1fr;
  }
  .attendance-rate-form,
  .attendance-rate-grid {
    grid-template-columns: 1fr;
  }
}
</style>
