<template>
  <AppShell title="Навчання">
    <div v-if="!isAllowed" class="panel">
      <div class="panel__title">Доступ заборонено</div>
      <div class="muted">Сторінка доступна лише для admin/staff.</div>
    </div>

    <div v-else class="layout">
      <div class="panel">
        <div class="row">
          <div class="tabs" role="tablist" aria-label="Academics resources">
            <button
              v-for="t in tabs"
              :key="t.key"
              class="tab"
              type="button"
              :class="{ 'tab--active': t.key === active }"
              @click="setActive(t.key)"
            >
              {{ t.label }}
            </button>
          </div>
          <div class="actions">
            <button class="btn btn--ghost" type="button" :disabled="loading || saving" @click="reload">Оновити</button>
            <button class="btn" type="button" :disabled="loading || saving" @click="startCreate">Створити</button>
            <button class="btn btn--ghost" type="button" :disabled="!selectedId || loading || saving" @click="startEdit">
              Редагувати
            </button>
            <button class="btn btn--ghost" type="button" :disabled="!selectedId || loading || saving" @click="onDelete">
              Видалити
            </button>
          </div>
        </div>

        <div style="height: 10px"></div>

        <div v-if="loading" class="muted">Завантаження...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <DataTable
          v-else
          :columns="columns"
          :rows="rows"
          :rowKey="rowKey"
          :onRowClick="onRowClick"
        />
      </div>

      <div class="panel">
        <div class="formwrap">
          <div class="formwrap__header">
            <div class="formwrap__title">{{ formTitle }}</div>
            <div class="formwrap__actions">
              <button v-if="mode === 'view'" class="btn btn--ghost" type="button" :disabled="!selectedId" @click="startEdit">
                Редагувати
              </button>
              <button v-else class="btn btn--ghost" type="button" :disabled="saving" @click="cancelEdit">Скасувати</button>
              <button v-if="mode !== 'view'" class="btn" type="button" :disabled="saving" @click="submitForm">
                {{ saving ? 'Збереження...' : mode === 'create' ? 'Створити' : 'Зберегти' }}
              </button>
            </div>
          </div>

          <div v-if="formError" class="error">{{ formError }}</div>
          <div v-else-if="mode === 'view' && !selectedId" class="muted">Оберіть рядок, щоб побачити деталі.</div>

          <div v-if="mode === 'view' && selectedId" class="muted" style="margin-bottom: 10px">
            Нижче доступний payload detail-ендпоінта.
          </div>

          <form class="formgrid" @submit.prevent="submitForm">
            <!-- Subjects -->
            <template v-if="currentTab.key === 'subjects'">
              <div class="field">
                <div class="field__label">Назва</div>
                <input class="input" v-model="form.subject.name" :disabled="mode === 'view'" />
              </div>
              <div class="field">
                <div class="field__label">Опис</div>
                <textarea class="input ta" v-model="form.subject.description" :disabled="mode === 'view'"></textarea>
              </div>
            </template>

            <!-- Groups -->
            <template v-else-if="currentTab.key === 'groups'">
              <div class="field">
                <div class="field__label">Предмет</div>
                <select class="input" v-model.number="form.group.subject" :disabled="mode === 'view'">
                  <option :value="null">Оберіть...</option>
                  <option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option>
                </select>
              </div>
              <div class="field">
                <div class="field__label">Вчитель</div>
                <select class="input" v-model.number="form.group.teacher" :disabled="mode === 'view'">
                  <option :value="null">Оберіть...</option>
                  <option v-for="t in teachers" :key="t.id" :value="t.id">{{ teacherLabel(t) }}</option>
                </select>
              </div>
              <div class="field">
                <div class="field__label">Місткість</div>
                <input class="input" type="number" min="1" v-model.number="form.group.capacity" :disabled="mode === 'view'" />
              </div>
              <div class="field">
                <div class="field__label">Ціна для учня</div>
                <input class="input" type="number" step="0.01" v-model="form.group.student_price" :disabled="mode === 'view'" />
              </div>
              <div class="field">
                <div class="field__label">Ставка вчителя</div>
                <input class="input" type="number" step="0.01" v-model="form.group.teacher_rate" :disabled="mode === 'view'" />
              </div>
              <div class="field">
                <div class="field__label">Студенти</div>
                <select class="input" multiple v-model="form.group.students" :disabled="mode === 'view'">
                  <option v-for="s in students" :key="s.id" :value="s.id">{{ studentLabel(s) }}</option>
                </select>
              </div>
              <label class="check">
                <input type="checkbox" v-model="form.group.is_active" :disabled="mode === 'view'" />
                <span>Активна</span>
              </label>
              <div v-if="detail?.name" class="muted">Назва генерується автоматично на бекенді.</div>
            </template>

            <!-- Enrollments -->
            <template v-else-if="currentTab.key === 'enrollments'">
              <div class="field">
                <div class="field__label">Група</div>
                <select class="input" v-model.number="form.enrollment.group" :disabled="mode === 'view'">
                  <option :value="null">Оберіть...</option>
                  <option v-for="g in groups" :key="g.id" :value="g.id">{{ groupLabel(g) }}</option>
                </select>
              </div>
              <div class="field">
                <div class="field__label">Учень</div>
                <select class="input" v-model.number="form.enrollment.student" :disabled="mode === 'view'">
                  <option :value="null">Оберіть...</option>
                  <option v-for="s in students" :key="s.id" :value="s.id">{{ studentLabel(s) }}</option>
                </select>
              </div>
              <div class="field">
                <div class="field__label">Статус</div>
                <select class="input" v-model="form.enrollment.status" :disabled="mode === 'view'">
                  <option value="active">active</option>
                  <option value="paused">paused</option>
                  <option value="completed">completed</option>
                  <option value="cancelled">cancelled</option>
                </select>
              </div>
              <div class="field">
                <div class="field__label">Дата початку</div>
                <input class="input" type="date" v-model="form.enrollment.start_date" :disabled="mode === 'view'" />
              </div>
              <div class="field">
                <div class="field__label">Дата завершення</div>
                <input class="input" type="date" v-model="form.enrollment.end_date" :disabled="mode === 'view'" />
              </div>
              <div class="field">
                <div class="field__label">Override ціни для учня</div>
                <input class="input" type="number" step="0.01" v-model="form.enrollment.student_price_override" :disabled="mode === 'view'" />
              </div>
              <div class="field">
                <div class="field__label">Override ставки вчителя</div>
                <input class="input" type="number" step="0.01" v-model="form.enrollment.teacher_rate_override" :disabled="mode === 'view'" />
              </div>
            </template>

            <!-- Lessons -->
            <template v-else-if="currentTab.key === 'lessons'">
              <div class="field">
                <div class="field__label">Група</div>
                <select class="input" v-model.number="form.lesson.group" :disabled="mode === 'view'">
                  <option :value="null">Оберіть...</option>
                  <option v-for="g in groups" :key="g.id" :value="g.id">{{ groupLabel(g) }}</option>
                </select>
              </div>
              <div class="field">
                <div class="field__label">Початок</div>
                <input class="input" type="datetime-local" v-model="form.lesson.starts_at_local" :disabled="mode === 'view'" />
              </div>
              <div class="field">
                <div class="field__label">Статус</div>
                <select class="input" v-model="form.lesson.status" :disabled="mode === 'view'">
                  <option value="scheduled">Заплановано</option>
                  <option value="completed">Завершено</option>
                  <option value="cancelled">Скасовано</option>
                </select>
              </div>
              <div class="field">
                <div class="field__label">Нотатки</div>
                <textarea class="input ta" v-model="form.lesson.notes" :disabled="mode === 'view'"></textarea>
              </div>
            </template>

            <!-- Confirmations -->
            <template v-else-if="currentTab.key === 'confirmations'">
              <div class="field">
                <div class="field__label">Урок</div>
                <select class="input" v-model.number="form.confirmation.lesson_id" :disabled="mode === 'view'" @change="onPickLesson">
                  <option :value="null">Оберіть...</option>
                  <option v-for="l in lessons" :key="l.id" :value="l.id">{{ lessonLabel(l) }}</option>
                </select>
              </div>
              <div class="field">
                <div class="field__label">Учасник</div>
                <select class="input" v-model.number="form.confirmation.participant" :disabled="mode === 'view' || participants.length === 0">
                  <option :value="null">Оберіть...</option>
                  <option v-for="p in participants" :key="p.id" :value="p.id">{{ participantLabel(p) }}</option>
                </select>
                <div v-if="form.confirmation.lesson_id && participants.length === 0" class="muted">
                  В detail уроку не знайдено учасників.
                </div>
              </div>
              <div class="field">
                <div class="field__label">Запит від</div>
                <select class="input" v-model="form.confirmation.requested_from" :disabled="mode === 'view'">
                  <option value="student">student</option>
                  <option value="parent">parent</option>
                  <option value="teacher">teacher</option>
                </select>
              </div>
              <div class="field">
                <div class="field__label">Підтверджує (користувач)</div>
                <select class="input" v-model.number="form.confirmation.confirmer" :disabled="mode === 'view'">
                  <option :value="null">Немає</option>
                  <option v-for="u in users" :key="u.id" :value="u.id">{{ userLabel(u) }}</option>
                </select>
              </div>
              <div class="field">
                <div class="field__label">Статус</div>
                <select class="input" v-model="form.confirmation.status" :disabled="mode === 'view'">
                  <option value="pending">pending</option>
                  <option value="confirmed">confirmed</option>
                  <option value="rejected">rejected</option>
                </select>
              </div>
              <div class="field">
                <div class="field__label">Підтверджено о</div>
                <input class="input" type="datetime-local" v-model="form.confirmation.confirmed_at_local" :disabled="mode === 'view'" />
              </div>
              <div class="field">
                <div class="field__label">Коментар</div>
                <textarea class="input ta" v-model="form.confirmation.comment" :disabled="mode === 'view'"></textarea>
              </div>
            </template>
          </form>

          <div style="height: 10px"></div>
          <JsonViewer v-if="mode === 'view'" :title="detailTitle" :value="detail" emptyText="" />
        </div>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import DataTable from '@/components/DataTable.vue'
import JsonViewer from '@/components/JsonViewer.vue'
import { apiRequest } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

type TabKey = 'subjects' | 'groups' | 'enrollments' | 'lessons' | 'confirmations'
type Mode = 'view' | 'create' | 'edit'

const tabs: Array<{ key: TabKey; label: string; listPath: string; detailPath: (id: number) => string }> = [
  { key: 'subjects', label: 'Предмети', listPath: '/api/academics/subjects/', detailPath: (id) => `/api/academics/subjects/${id}/` },
  { key: 'groups', label: 'Групи', listPath: '/api/academics/groups/', detailPath: (id) => `/api/academics/groups/${id}/` },
  { key: 'enrollments', label: 'Зарахування', listPath: '/api/academics/enrollments/', detailPath: (id) => `/api/academics/enrollments/${id}/` },
  { key: 'lessons', label: 'Уроки', listPath: '/api/academics/lessons/', detailPath: (id) => `/api/academics/lessons/${id}/` },
  { key: 'confirmations', label: 'Підтвердження', listPath: '/api/academics/confirmations/', detailPath: (id) => `/api/academics/confirmations/${id}/` },
]

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const isAllowed = computed(() => !!auth.me && (auth.me.is_staff || auth.me.role === 'admin'))

const active = computed<TabKey>(() => {
  const raw = (route.query.tab as string | undefined) ?? 'subjects'
  const ok = tabs.some((t) => t.key === raw)
  return (ok ? raw : 'subjects') as TabKey
})

const loading = ref(false)
const error = ref<string | null>(null)
const rows = ref<any[]>([])
const detail = ref<any | null>(null)
const selectedId = ref<number | null>(null)

const currentTab = computed(() => tabs.find((t) => t.key === active.value)!)
const detailTitle = computed(() => {
  const id = selectedId.value
  return id ? `${currentTab.value.label} #${id}` : `${currentTab.value.label} detail`
})

const mode = ref<Mode>('view')
const saving = ref(false)
const formError = ref<string | null>(null)
const formTitle = computed(() => {
  const id = selectedId.value
  if (mode.value === 'create') return `Create ${currentTab.value.label}`
  if (mode.value === 'edit' && id) return `Edit ${currentTab.value.label} #${id}`
  return `${currentTab.value.label}`
})

type SubjectRow = { id: number; name: string; description?: string }
type TeacherRow = { id: number; user_detail?: { first_name?: string; last_name?: string; telegram_username?: string; email?: string } }
type StudentRow = { id: number; user_detail?: { first_name?: string; last_name?: string; telegram_username?: string; email?: string } }
type GroupRow = { id: number; name?: string; subject?: number; teacher?: number; is_active?: boolean }
  type LessonRow = { id: number; group: number; starts_at: string; status: string }
  type UserRow = { id: number; first_name?: string; last_name?: string; telegram_username?: string; email?: string }
  type ParticipantRow = { id: number; student?: number; student_last_name?: string; attendance_status?: string }
    type LessonParticipantTableRow = {
      // Lesson id (used for detail/edit/delete).
      id: number
      // Unique key for Vue rows; this is LessonParticipant.id.
      participant_id: number
    starts_at: string
    group_id: number | null
    teacher_last_name: string | null
    student_last_name: string | null
      billed_amount: string | number | null
      payroll_amount: string | number | null
    }
    type EnrollmentRow = {
      id: number
      group: number
      student: number
      status: string
      start_date: string
      end_date?: string | null
      student_price_override?: string | null
      teacher_rate_override?: string | null
    }

const subjects = ref<SubjectRow[]>([])
const teachers = ref<TeacherRow[]>([])
const students = ref<StudentRow[]>([])
const groups = ref<GroupRow[]>([])
  const lessons = ref<LessonRow[]>([])
  const users = ref<UserRow[]>([])
  const participants = ref<ParticipantRow[]>([])
  const enrollments = ref<EnrollmentRow[]>([])
  const enrollmentsLoaded = ref(false)

const form = ref({
  subject: { name: '', description: '' },
  group: {
    subject: null as number | null,
    teacher: null as number | null,
    capacity: 1,
    student_price: '0.00',
    teacher_rate: '0.00',
    is_active: true,
    students: [] as number[],
  },
  enrollment: {
    group: null as number | null,
    student: null as number | null,
    status: 'active',
    start_date: '',
    end_date: '',
    student_price_override: '' as string,
    teacher_rate_override: '' as string,
  },
  lesson: { group: null as number | null, starts_at_local: '', status: 'scheduled', notes: '' },
  confirmation: {
    lesson_id: null as number | null,
    participant: null as number | null,
    requested_from: 'student',
    confirmer: null as number | null,
    status: 'pending',
    confirmed_at_local: '',
    comment: '',
  },
})

const rowKey = (r: any, idx: number) => {
  if (currentTab.value.key === 'lessons' && typeof r?.participant_id === 'number') return r.participant_id
  return typeof r?.id === 'number' ? r.id : idx
}

const columns = computed(() => {
  if (currentTab.value.key === 'lessons') {
    return [
      { key: 'id', label: 'id' },
      { key: 'starts_at', label: 'Дата', render: (r: any) => fmtDt(r?.starts_at) },
      { key: 'group_id', label: 'Група', render: (r: any) => groupNameById(r?.group_id) },
      { key: 'teacher_last_name', label: 'Викладач', render: (r: any) => String(r?.teacher_last_name ?? '-') },
      { key: 'student_last_name', label: 'Студент', render: (r: any) => String(r?.student_last_name ?? '-') },
      { key: 'billed_amount', label: 'Вартість заняття', render: (r: any) => fmtMoney(r?.billed_amount) },
      { key: 'payroll_amount', label: 'Винагорода викладача', render: (r: any) => fmtMoney(r?.payroll_amount) },
    ]
  }

  const first = rows.value[0]
  if (!first || typeof first !== 'object') return [{ key: 'id', label: 'ID' }]

  const keys = Object.keys(first)
  // Keep the table scannable; detail panel shows full payload.
  const preferred = ['id', 'name', 'status', 'starts_at', 'group', 'student', 'teacher', 'subject']
  const ordered = [...preferred.filter((k) => keys.includes(k)), ...keys.filter((k) => !preferred.includes(k))]
  const pick = ordered.slice(0, 8)
  return pick.map((k) => ({
    key: k,
    label: k,
    render: (row: any) => {
      const v = row?.[k]
      if (v === null || v === undefined) return '-'
      if (typeof v === 'object') return JSON.stringify(v)
      return String(v)
    },
  }))
})

async function loadList() {
  loading.value = true
  error.value = null
  rows.value = []
  detail.value = null
  selectedId.value = null
  mode.value = 'view'
  formError.value = null
  try {
    const list = await apiRequest<any[]>(currentTab.value.listPath)
    if (currentTab.value.key === 'lessons') {
      rows.value = lessonRowsToParticipantRows(list)
    } else {
      rows.value = list
    }
  } catch (e: any) {
    error.value = e?.payload?.detail || e?.message || 'Failed to load'
  } finally {
    loading.value = false
  }
}

async function loadDetail(id: number) {
  selectedId.value = id
  mode.value = 'view'
  formError.value = null
  try {
    detail.value = await apiRequest<any>(currentTab.value.detailPath(id))
    hydrateFormFromDetail()
    if (currentTab.value.key === 'groups') {
      await ensureEnrollmentsLoaded(true)
      form.value.group.students = groupEnrollments(id)
        .filter((e) => e.status === 'active')
        .map((e) => e.student)
    }
  } catch (e: any) {
    detail.value = { error: e?.payload || e?.message || 'Failed to load detail' }
  }
}

function onRowClick(row: any) {
  if (currentTab.value.key === 'lessons') {
    const lessonId = row?.id
    if (typeof lessonId !== 'number') return
    loadDetail(lessonId)
    return
  }

  const id = row?.id
  if (typeof id !== 'number') return
  loadDetail(id)
}

function setActive(key: TabKey) {
  router.replace({ query: { ...route.query, tab: key } })
}

function reload() {
  loadList()
}

function startCreate() {
  mode.value = 'create'
  formError.value = null
  participants.value = []
  hydrateFormFromDetail(true)
}

function startEdit() {
  if (!selectedId.value || !detail.value || typeof detail.value !== 'object') return
  mode.value = 'edit'
  formError.value = null
}

function cancelEdit() {
  mode.value = 'view'
  formError.value = null
  hydrateFormFromDetail()
}

function isoFromLocal(dtLocal: string) {
  if (!dtLocal) return null
  // datetime-local returns "YYYY-MM-DDTHH:MM" (no timezone). Treat as local time and convert to ISO.
  const d = new Date(dtLocal)
  if (isNaN(d.getTime())) return null
  return d.toISOString()
}

function localFromIso(iso: string) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function hydrateFormFromDetail(resetForCreate = false) {
  const tab = currentTab.value.key
  if (resetForCreate || !detail.value || typeof detail.value !== 'object') {
    form.value.subject = { name: '', description: '' }
    form.value.group = {
      subject: null,
      teacher: null,
      capacity: 1,
      student_price: '0.00',
      teacher_rate: '0.00',
      is_active: true,
      students: [],
    }
    form.value.enrollment = { group: null, student: null, status: 'active', start_date: '', end_date: '', student_price_override: '', teacher_rate_override: '' }
    form.value.lesson = { group: null, starts_at_local: '', status: 'scheduled', notes: '' }
    form.value.confirmation = { lesson_id: null, participant: null, requested_from: 'student', confirmer: null, status: 'pending', confirmed_at_local: '', comment: '' }
    return
  }

  const d: any = detail.value
  if (tab === 'subjects') {
    form.value.subject = { name: d.name ?? '', description: d.description ?? '' }
  } else if (tab === 'groups') {
    form.value.group = {
      subject: d.subject ?? null,
      teacher: d.teacher ?? null,
      capacity: d.capacity ?? 1,
      student_price: String(d.student_price ?? '0.00'),
      teacher_rate: String(d.teacher_rate ?? '0.00'),
      is_active: !!d.is_active,
      students: [],
    }
  } else if (tab === 'enrollments') {
    form.value.enrollment = {
      group: d.group ?? null,
      student: d.student ?? null,
      status: d.status ?? 'active',
      start_date: d.start_date ?? '',
      end_date: d.end_date ?? '',
      student_price_override: d.student_price_override == null ? '' : String(d.student_price_override),
      teacher_rate_override: d.teacher_rate_override == null ? '' : String(d.teacher_rate_override),
    }
  } else if (tab === 'lessons') {
    form.value.lesson = {
      group: d.group ?? null,
      starts_at_local: d.starts_at ? localFromIso(d.starts_at) : '',
      status: d.status ?? 'scheduled',
      notes: d.notes ?? '',
    }
  } else if (tab === 'confirmations') {
    form.value.confirmation = {
      lesson_id: null,
      participant: d.participant ?? null,
      requested_from: d.requested_from ?? 'student',
      confirmer: d.confirmer ?? null,
      status: d.status ?? 'pending',
      confirmed_at_local: d.confirmed_at ? localFromIso(d.confirmed_at) : '',
      comment: d.comment ?? '',
    }
  }
}

function teacherLabel(t: TeacherRow) {
  const u = t.user_detail || {}
  const name = [u.first_name, u.last_name].filter(Boolean).join(' ')
  return name || u.telegram_username || u.email || `Вчитель #${t.id}`
}
function studentLabel(s: StudentRow) {
  const u = s.user_detail || {}
  const name = [u.first_name, u.last_name].filter(Boolean).join(' ')
  return name || u.telegram_username || u.email || `Учень #${s.id}`
}
function groupLabel(g: GroupRow) {
  return g.name || `Група #${g.id}`
}
function lessonLabel(l: LessonRow) {
  return `Урок #${l.id} (${lessonStatusLabel(l.status)})`
}
function participantLabel(p: ParticipantRow) {
  const tail = [p.student_last_name, p.attendance_status].filter(Boolean).join(', ')
  return tail ? `#${p.id} (${tail})` : `Учасник #${p.id}`
}

function lessonStatusLabel(status: string) {
  const map: Record<string, string> = {
    scheduled: 'Заплановано',
    completed: 'Завершено',
    cancelled: 'Скасовано',
  }
  return map[status] || status
}
function userLabel(u: UserRow) {
  const name = [u.first_name, u.last_name].filter(Boolean).join(' ')
  return name || u.telegram_username || u.email || `Користувач #${u.id}`
}

function groupNameById(groupId: number | null | undefined) {
  if (typeof groupId !== 'number') return '-'
  const g = groups.value.find((x) => x.id === groupId)
  return g ? groupLabel(g) : `Група #${groupId}`
}

function fmtMoney(v: any) {
  if (v === null || v === undefined || v === '') return '-'
  const n = typeof v === 'number' ? v : Number(v)
  if (Number.isFinite(n)) return n.toFixed(2)
  return String(v)
}

function fmtDt(iso: any) {
  if (!iso) return '-'
  const d = new Date(String(iso))
  if (isNaN(d.getTime())) return String(iso)
  return d.toLocaleString()
}

function lessonRowsToParticipantRows(list: any[]): LessonParticipantTableRow[] {
  const out: LessonParticipantTableRow[] = []
  for (const l of list) {
    const lessonId = l?.id
    const startsAt = l?.starts_at
    const groupId = l?.group
    const participants = Array.isArray(l?.participants) ? l.participants : []
    const totalBilled = participants.reduce((acc: number, p: any) => acc + Number(p?.billed_amount || 0), 0)
    for (const p of participants) {
      const pid = p?.id
      if (typeof lessonId !== 'number' || typeof pid !== 'number') continue
      out.push({
        id: lessonId,
        participant_id: pid,
        starts_at: String(startsAt ?? ''),
        group_id: typeof groupId === 'number' ? groupId : null,
        teacher_last_name: (p?.teacher_last_name ?? null) as any,
        student_last_name: (p?.student_last_name ?? null) as any,
        billed_amount: totalBilled,
        payroll_amount: p?.payroll_amount ?? null,
      })
    }
  }
  return out
}

function todayDate() {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

async function ensureEnrollmentsLoaded(refresh = false) {
  if (enrollmentsLoaded.value && !refresh) return
  enrollments.value = await apiRequest<EnrollmentRow[]>('/api/academics/enrollments/')
  enrollmentsLoaded.value = true
}

function groupEnrollments(groupId: number) {
  return enrollments.value.filter((e) => e.group === groupId)
}

async function syncGroupStudents(groupId: number, studentIds: number[]) {
  await ensureEnrollmentsLoaded(true)

  const byStudent = new Map<number, EnrollmentRow>()
  for (const e of groupEnrollments(groupId)) byStudent.set(e.student, e)

  const desired = new Set(studentIds.filter((x) => typeof x === 'number'))
  const start = todayDate()

  // Add/reactivate selected students.
  for (const sid of desired) {
    const existing = byStudent.get(sid)
    if (!existing) {
      const created = await apiRequest<EnrollmentRow>('/api/academics/enrollments/', {
        method: 'POST',
        body: { group: groupId, student: sid, status: 'active', start_date: start },
      })
      enrollments.value.push(created)
      byStudent.set(sid, created)
      continue
    }

    if (existing.status !== 'active' || existing.end_date) {
      const updated = await apiRequest<EnrollmentRow>(`/api/academics/enrollments/${existing.id}/`, {
        method: 'PATCH',
        body: { status: 'active', end_date: null },
      })
      const idx = enrollments.value.findIndex((x) => x.id === updated.id)
      if (idx >= 0) enrollments.value[idx] = updated
      byStudent.set(sid, updated)
    }
  }

  // Cancel active enrollments that were unselected.
  for (const e of groupEnrollments(groupId)) {
    if (e.status === 'active' && !desired.has(e.student)) {
      const updated = await apiRequest<EnrollmentRow>(`/api/academics/enrollments/${e.id}/`, {
        method: 'PATCH',
        body: { status: 'cancelled', end_date: start },
      })
      const idx = enrollments.value.findIndex((x) => x.id === updated.id)
      if (idx >= 0) enrollments.value[idx] = updated
    }
  }
}

async function ensureLookups() {
  // Load only what's needed for the current tab.
  const tab = currentTab.value.key
  const needsSubjects = tab === 'groups'
  const needsTeachers = tab === 'groups'
  const needsGroups = tab === 'enrollments' || tab === 'lessons'
  const needsStudents = tab === 'enrollments' || tab === 'groups'
  const needsLessons = tab === 'confirmations'
  const needsUsers = tab === 'confirmations'

  try {
    if (needsSubjects && subjects.value.length === 0) subjects.value = await apiRequest<SubjectRow[]>('/api/academics/subjects/')
    if (needsTeachers && teachers.value.length === 0) teachers.value = await apiRequest<TeacherRow[]>('/api/users/teachers/')
    if (needsGroups && groups.value.length === 0) groups.value = await apiRequest<GroupRow[]>('/api/academics/groups/')
    if (needsStudents && students.value.length === 0) students.value = await apiRequest<StudentRow[]>('/api/users/students/')
    if (needsLessons && lessons.value.length === 0) lessons.value = await apiRequest<LessonRow[]>('/api/academics/lessons/')
    if (needsUsers && users.value.length === 0) users.value = await apiRequest<UserRow[]>('/api/users/')
  } catch (e: any) {
    // Lookup failures shouldn't block list/detail, but will block create/edit UX.
    formError.value = e?.payload?.detail || e?.message || 'Не вдалося завантажити довідники'
  }
}

async function onPickLesson() {
  participants.value = []
  const lessonId = form.value.confirmation.lesson_id
  if (!lessonId) return
  try {
    const ld = await apiRequest<any>(`/api/academics/lessons/${lessonId}/`)
    const list = Array.isArray(ld?.participants) ? ld.participants : []
    participants.value = list
  } catch {
    participants.value = []
  }
}

function payloadForSubmit() {
  const tab = currentTab.value.key
  if (tab === 'subjects') {
    return { name: form.value.subject.name, description: form.value.subject.description }
  }
  if (tab === 'groups') {
    return {
      subject: form.value.group.subject,
      teacher: form.value.group.teacher,
      capacity: form.value.group.capacity,
      student_price: form.value.group.student_price,
      teacher_rate: form.value.group.teacher_rate,
      is_active: form.value.group.is_active,
    }
  }
  if (tab === 'enrollments') {
    return {
      group: form.value.enrollment.group,
      student: form.value.enrollment.student,
      status: form.value.enrollment.status,
      start_date: form.value.enrollment.start_date,
      end_date: form.value.enrollment.end_date || null,
      student_price_override: form.value.enrollment.student_price_override === '' ? null : form.value.enrollment.student_price_override,
      teacher_rate_override: form.value.enrollment.teacher_rate_override === '' ? null : form.value.enrollment.teacher_rate_override,
    }
  }
  if (tab === 'lessons') {
    return {
      group: form.value.lesson.group,
      starts_at: isoFromLocal(form.value.lesson.starts_at_local),
      status: form.value.lesson.status,
      notes: form.value.lesson.notes,
    }
  }
  if (tab === 'confirmations') {
    return {
      participant: form.value.confirmation.participant,
      requested_from: form.value.confirmation.requested_from,
      confirmer: form.value.confirmation.confirmer,
      status: form.value.confirmation.status,
      confirmed_at: isoFromLocal(form.value.confirmation.confirmed_at_local),
      comment: form.value.confirmation.comment,
    }
  }
  return {}
}

async function submitForm() {
  if (mode.value === 'view') return
  await ensureLookups()
  saving.value = true
  formError.value = null
  saving.value = true
  try {
      const payload = payloadForSubmit()
      if (mode.value === 'create') {
        const created = await apiRequest<any>(currentTab.value.listPath, { method: 'POST', body: payload })
        if (currentTab.value.key === 'groups' && typeof created?.id === 'number') {
          await syncGroupStudents(created.id, form.value.group.students || [])
        }
        await loadList()
        if (typeof created?.id === 'number') await loadDetail(created.id)
        mode.value = 'view'
        return
      }

      if (mode.value === 'edit' && selectedId.value) {
        const updated = await apiRequest<any>(currentTab.value.detailPath(selectedId.value), { method: 'PATCH', body: payload })
        if (currentTab.value.key === 'groups' && typeof updated?.id === 'number') {
          await syncGroupStudents(updated.id, form.value.group.students || [])
        }
        // Reload list + detail to reflect server truth.
        await loadList()
        if (typeof updated?.id === 'number') await loadDetail(updated.id)
        mode.value = 'view'
      }
  } catch (e: any) {
    formError.value = e?.payload ? JSON.stringify(e.payload) : e?.message || 'Не вдалося зберегти'
  } finally {
    saving.value = false
  }
}

async function onDelete() {
  const id = selectedId.value
  if (!id) return
  const ok = window.confirm(`Видалити ${currentTab.value.label} #${id}?`)
  if (!ok) return
  saving.value = true
  formError.value = null
  try {
    await apiRequest(currentTab.value.detailPath(id), { method: 'DELETE' })
    await loadList()
  } catch (e: any) {
    formError.value = e?.payload ? JSON.stringify(e.payload) : e?.message || 'Не вдалося видалити'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await auth.bootstrap()
  if (isAllowed.value) {
    await ensureLookups()
    await loadList()
  }
})

watch(
  () => active.value,
  async () => {
    if (!isAllowed.value) return
    participants.value = []
    formError.value = null
    await ensureLookups()
    await loadList()
  },
)
</script>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 14px;
  align-items: start;
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.formwrap {
  display: grid;
  gap: 10px;
}
.formwrap__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.formwrap__title {
  font-weight: 650;
}
.formwrap__actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.formgrid {
  display: grid;
  gap: 12px;
}
.ta {
  min-height: 90px;
  resize: vertical;
}
.check {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 13px;
  color: rgba(232, 238, 252, 0.9);
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tab {
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(232, 238, 252, 0.9);
  border-radius: 6px;
  padding: 8px 10px;
  cursor: pointer;
  font-size: 13px;
}

.tab--active {
  border-color: rgba(93, 120, 255, 0.7);
  background: rgba(93, 120, 255, 0.18);
}

@media (max-width: 980px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
