<template>
  <AppShell title="Мої групи">
    <div class="panel">
      <div class="panel__title">Список груп</div>
      <div v-if="notice" class="notice">{{ notice }}</div>
      <div class="toolbar">
        <button v-if="canManageGroups" class="btn" type="button" @click="openCreateForm">Створити групу</button>
        <button v-if="canManageGroups" class="btn btn--ghost" type="button" :disabled="!selectedGroupId" @click="openEditForm">Редагувати</button>
      </div>
      <div class="filters">
        <div class="dropdown">
          <button class="input dropdown__trigger" type="button" @click="teacherFilterOpen = !teacherFilterOpen">{{ selectedTeacherFilterLabel }}</button>
          <div v-if="teacherFilterOpen" class="dropdown__menu">
            <button class="dropdown__option" type="button" @click="setTeacherFilter(null)">Всі вчителі</button>
            <button class="dropdown__option" v-for="t in teachers" :key="t.id" type="button" @click="setTeacherFilter(t.id)">{{ teacherLabel(t.id) }}</button>
          </div>
        </div>
        <div class="dropdown">
          <button class="input dropdown__trigger" type="button" @click="studentFilterOpen = !studentFilterOpen">{{ selectedStudentFilterLabel }}</button>
          <div v-if="studentFilterOpen" class="dropdown__menu">
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
            <th>Вчитель</th>
            <th>Назва групи</th>
            <th>Ціна учня</th>
            <th>Ставка вчителя</th>
            <th>Кількість учнів</th>
            <th>Список студентів</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in filteredGroupRows"
            :key="row.group.id"
            :class="{ selected: selectedGroupId === row.group.id }"
            @click="selectedGroupId = row.group.id"
          >
            <td>{{ teacherLabel(row.group.teacher) }}</td>
            <td>{{ row.group.name || `Група #${row.group.id}` }}</td>
            <td>{{ priceLabel(row.group.student_price) }}</td>
            <td>{{ priceLabel(row.group.teacher_rate) }}</td>
            <td>{{ row.studentIds.length }}</td>
            <td>{{ row.studentNames.join(', ') || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showCreateForm && canManageGroups" class="panel form">
      <div class="panel__title">Створити групу</div>
      <div v-if="error" class="error">{{ error }}</div>
      <div class="grid">
        <div class="dropdown">
          <button class="input dropdown__trigger" type="button" @click="subjectOpen = !subjectOpen">{{ selectedCreateSubjectLabel }}</button>
          <div v-if="subjectOpen" class="dropdown__menu">
            <button class="dropdown__option" type="button" @click="setCreateSubject(null)">Предмет...</button>
            <button class="dropdown__option" v-for="s in subjects" :key="s.id" type="button" @click="setCreateSubject(s.id)">{{ s.name }}</button>
          </div>
        </div>
        <input class="input" type="number" min="1" v-model.number="createForm.capacity" placeholder="Місткість" />
        <div class="dropdown">
          <button class="input dropdown__trigger" type="button" @click="createStudentsOpen = !createStudentsOpen">{{ selectedStudentsLabel(createForm.students) }}</button>
          <div v-if="createStudentsOpen" class="dropdown__menu dropdown__menu--static">
            <label v-for="s in students" :key="s.id" class="dropdown__item">
              <input type="checkbox" :checked="createForm.students.includes(s.id)" @change="toggleStudentSelection(createForm.students, s.id)" />
              <span>{{ studentLabel(s) }}</span>
            </label>
          </div>
        </div>
        <button class="btn" type="button" :disabled="saving" @click="createGroup">{{ saving ? 'Збереження...' : 'Створити групу' }}</button>
      </div>
    </div>

    <div v-if="showEditForm && editableGroup && canManageGroups" class="panel form">
      <div class="panel__title">Редагувати групу {{ editableGroup.name || `#${editableGroup.id}` }}</div>
      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="notice" class="notice">{{ notice }}</div>
      <div v-if="saving" class="muted">Зберігаю...</div>
      <div class="grid">
        <div class="field">
          <div class="field__label">Предмет</div>
          <div class="dropdown">
            <button class="input dropdown__trigger" type="button" @click="editSubjectOpen = !editSubjectOpen">{{ selectedEditSubjectLabel }}</button>
            <div v-if="editSubjectOpen" class="dropdown__menu">
              <button class="dropdown__option" type="button" @click="setEditSubject(null)">Предмет...</button>
              <button class="dropdown__option" v-for="s in subjects" :key="s.id" type="button" @click="setEditSubject(s.id)">{{ s.name }}</button>
            </div>
          </div>
        </div>
        <div class="field">
          <div class="field__label">Місткість</div>
          <input class="input" type="number" min="1" v-model.number="editForm.capacity" placeholder="Місткість" />
        </div>
        <div v-if="isAdmin" class="field">
          <div class="field__label">Ціна учня</div>
          <input class="input" type="number" min="0" step="0.01" v-model.number="editForm.student_price" placeholder="Ціна учня" />
        </div>
        <div v-if="isAdmin" class="field">
          <div class="field__label">Ставка вчителя</div>
          <input class="input" type="number" min="0" step="0.01" v-model.number="editForm.teacher_rate" placeholder="Ставка вчителя" />
        </div>
        <div class="field">
          <div class="field__label">Учні групи</div>
          <div class="dropdown">
            <button class="input dropdown__trigger" type="button" @click="editStudentsOpen = !editStudentsOpen">{{ selectedStudentsLabel(editForm.students) }}</button>
            <div v-if="editStudentsOpen" class="dropdown__menu dropdown__menu--static">
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
            <span class="field__label">Ціна учня</span>
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
              <th>Ціна учня</th>
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
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppShell from '@/components/AppShell.vue'
import { apiRequest } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

type Subject = { id: number; name: string }
type Student = { id: number; user_detail?: { first_name?: string; last_name?: string; email?: string; telegram_username?: string } }
type Teacher = { id: number; user_detail?: { first_name?: string; last_name?: string; telegram_username?: string; email?: string } }
type Group = { id: number; name?: string; teacher?: number | null; subject?: number | null; capacity?: number | null; student_price?: string | number | null; teacher_rate?: string | number | null }
type GroupPricing = { id: number; group: number; group_name?: string; student_price: string | number; teacher_rate: string | number; effective_from: string; created_at?: string }
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

const auth = useAuthStore()
const canManageGroups = ref(false)
const isAdmin = ref(false)
const loading = ref(true)
const saving = ref(false)
const savingPricing = ref(false)
const error = ref<string | null>(null)
const notice = ref<string | null>(null)
const selectedGroupId = ref<number | null>(null)

const subjectOpen = ref(false)
const editSubjectOpen = ref(false)
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

const createForm = ref({ subject: null as number | null, capacity: 1, students: [] as number[] })
const editForm = ref({ subject: null as number | null, capacity: 1, student_price: 0, teacher_rate: 0, students: [] as number[] })
const pricingForm = ref({ effective_from_date: '', student_price: 0, teacher_rate: 0 })

const editableGroup = computed(() => groups.value.find((g) => g.id === selectedGroupId.value) || null)
const selectedGroupPricingRules = computed(() => {
  if (!selectedGroupId.value) return []
  return pricingRules.value
    .filter((rule) => Number(rule.group) === Number(selectedGroupId.value))
    .sort((a, b) => new Date(b.effective_from).getTime() - new Date(a.effective_from).getTime() || b.id - a.id)
})

const selectedCreateSubjectLabel = computed(() => {
  if (!createForm.value.subject) return 'Предмет...'
  return subjects.value.find((s) => s.id === createForm.value.subject)?.name || 'Предмет...'
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

function priceLabel(value?: string | number | null) {
  if (value === null || value === undefined || value === '') return '-'
  const n = Number(value)
  return Number.isFinite(n) ? n.toFixed(2) : String(value)
}

function dateLabel(value?: string | null) {
  if (!value) return '-'
  const d = new Date(value)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()}`
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

function openCreateForm() {
  notice.value = null
  error.value = null
  showEditForm.value = false
  showCreateForm.value = true
}

function openEditForm() {
  if (!editableGroup.value) return
  notice.value = null
  error.value = null
  const g = editableGroup.value
  showCreateForm.value = false
  showEditForm.value = true
  editForm.value.subject = g.subject || null
  editForm.value.capacity = g.capacity || 1
  editForm.value.student_price = Number(g.student_price || 0)
  editForm.value.teacher_rate = Number(g.teacher_rate || 0)
  editForm.value.students = activeStudentIdsByGroup(g.id)
  pricingForm.value = {
    effective_from_date: todayDate(),
    student_price: Number(g.student_price || 0),
    teacher_rate: Number(g.teacher_rate || 0),
  }
  void loadPricingRules(g.id)
}

async function createGroup() {
  if (!createForm.value.subject) return
  saving.value = true
  error.value = null
  notice.value = null
  try {
    const created = await apiRequest<Group>('/api/academics/groups/', {
      method: 'POST',
      body: { subject: createForm.value.subject, capacity: createForm.value.capacity, is_active: true },
    })
    const updatedGroupEnrollments = await syncGroupStudents(created.id, createForm.value.students)
    await loadData()
    replaceGroupEnrollments(created.id, updatedGroupEnrollments)
    selectedGroupId.value = created.id
    showCreateForm.value = false
    notice.value = `Групу створено. Активних учнів: ${activeEnrollmentCount(updatedGroupEnrollments)}`
  } catch (e: any) {
    error.value = e?.payload?.detail || e?.message || 'Не вдалося створити групу'
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
      capacity: editForm.value.capacity,
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
    notice.value = `Групу збережено. Активних учнів: ${activeEnrollmentCount(updatedGroupEnrollments)}`
  } catch (e: any) {
    error.value = e?.payload?.detail || e?.message || 'Не вдалося зберегти групу'
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
    error.value = e?.payload?.detail || e?.message || 'Не вдалося додати ціну з дати'
  } finally {
    savingPricing.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await auth.bootstrap()
    canManageGroups.value = auth.me?.role === 'teacher' || auth.me?.role === 'admin' || !!auth.me?.is_staff
    isAdmin.value = auth.me?.role === 'admin' || !!auth.me?.is_staff
    if (canManageGroups.value) await loadData()
    if (isAdmin.value) await loadPricingRules()
  } catch (e: any) {
    error.value = e?.payload?.detail || e?.message || 'Не вдалося завантажити дані'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 10px; }
.form { margin-bottom: 12px; }
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
  border: 1px solid #d0d7de;
  border-radius: 6px;
  background: #514f4f;
  padding: 6px;
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
  color: #e8eefc;
  background: transparent;
  cursor: pointer;
}
.dropdown__option:hover { background: rgba(255, 255, 255, 0.08); }
.dropdown__item { display: flex; align-items: center; gap: 8px; padding: 6px; }
.notice { color: #b8f7c4; font-size: 13px; margin-bottom: 10px; }
.groups-table { width: 100%; border-collapse: collapse; }
.filters { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
.groups-table th, .groups-table td, .pricing-table th, .pricing-table td { text-align: left; padding: 8px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
.groups-table tbody tr { cursor: pointer; }
.groups-table tbody tr:hover { background: rgba(255, 255, 255, 0.05); }
.groups-table tbody tr.selected {
  background: rgba(93, 120, 255, 0.28);
  box-shadow: inset 3px 0 0 rgba(147, 170, 255, 0.95);
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
.pricing-submit {
  min-height: 39px;
}
.pricing-table {
  width: 100%;
  border-collapse: collapse;
}
@media (max-width: 760px) {
  .pricing-form {
    grid-template-columns: 1fr;
  }
}
</style>
