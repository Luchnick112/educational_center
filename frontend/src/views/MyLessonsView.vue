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
          <div v-if="lessonGroupOpen" class="dropdown__menu">
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
        <button class="btn btn--ghost filter-clear" type="button" :disabled="!hasDateInterval" @click="clearDateFilters">
          Очистити
        </button>
      </div>
      <div v-if="canSeePayroll && hasDateInterval" class="period-totals">
        <div>Винагорода вчителя за період: {{ formatPayrollAmount(payrollAmountTotal) }}</div>
        <div v-if="isAdmin">Вартість занять за період: {{ formatPayrollAmount(billedAmountTotal) }}</div>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div v-else-if="loading" class="muted">Завантаження...</div>
      <DataTable v-else :columns="columns" :rows="rows" :onRowClick="onLessonClick" />
    </div>

    <div v-if="canManageLessons && selectedLesson" class="panel form">
      <div class="panel__title">Редагувати урок #{{ selectedLesson.id }}</div>
      <div class="grid">
        <div class="dropdown">
          <button class="input dropdown__trigger" type="button" @click="editLessonGroupOpen = !editLessonGroupOpen">
            {{ selectedEditLessonGroupLabel }}
          </button>
          <div v-if="editLessonGroupOpen" class="dropdown__menu">
            <button class="dropdown__option" type="button" @click="selectEditLessonGroup(null)">Група...</button>
            <button class="dropdown__option" v-for="g in groups" :key="g.id" type="button" @click="selectEditLessonGroup(g.id)">
              {{ g.name || `Група #${g.id}` }}
            </button>
          </div>
        </div>
        <input class="input" type="datetime-local" step="900" v-model="editLessonForm.starts_at_local" />
        <textarea class="input ta" v-model="editLessonForm.notes" placeholder="Нотатки"></textarea>
        <button class="btn" type="button" :disabled="savingLesson" @click="updateLesson">{{ savingLesson ? 'Збереження...' : 'Зберегти урок' }}</button>
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
type Group = { id: number; name?: string }

const auth = useAuthStore()
const canManageLessons = ref(false)
const isAdmin = ref(false)
const loading = ref(true)
const savingLesson = ref(false)
const error = ref<string | null>(null)
const lessonGroupOpen = ref(false)
const editLessonGroupOpen = ref(false)
const createLessonFormOpen = ref(false)
const dateFilterFrom = ref('')
const dateFilterTo = ref('')
const rows = ref<Lesson[]>([])
const selectedLesson = ref<Lesson | null>(null)
const groups = ref<Group[]>([])

const lessonForm = ref({ group: null as number | null, starts_at_local: '', notes: '' })
const editLessonForm = ref({ group: null as number | null, starts_at_local: '', notes: '' })

const columns = computed(() => {
  const items = [
    { key: 'id', label: 'ID' },
    { key: 'group', label: 'Група', render: (r: Lesson) => groupLabel(r.group) },
    { key: 'status', label: 'Статус', render: (r: Lesson) => lessonStatusLabel(r.status) },
    { key: 'starts_at', label: 'Початок', render: (r: Lesson) => formatLessonDateTime(r.starts_at) },
  ]
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
const canSeePayroll = computed(() => canManageLessons.value)
const payrollAmountTotal = computed(() => rows.value.reduce((sum, lesson) => sum + payrollAmountValue(lesson.payroll_amount), 0))
const billedAmountTotal = computed(() => rows.value.reduce((sum, lesson) => sum + payrollAmountValue(lesson.billed_amount), 0))

const selectedLessonGroupLabel = computed(() => {
  if (!lessonForm.value.group) return 'Група...'
  return groups.value.find((g) => g.id === lessonForm.value.group)?.name || `Група #${lessonForm.value.group}`
})

const selectedEditLessonGroupLabel = computed(() => {
  if (!editLessonForm.value.group) return 'Група...'
  return groups.value.find((g) => g.id === editLessonForm.value.group)?.name || `Група #${editLessonForm.value.group}`
})

function selectLessonGroup(groupId: number | null) {
  lessonForm.value.group = groupId
  lessonGroupOpen.value = false
}

function selectEditLessonGroup(groupId: number | null) {
  editLessonForm.value.group = groupId
  editLessonGroupOpen.value = false
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

function groupLabel(groupId: number) {
  return groups.value.find((g) => g.id === groupId)?.name || `Група #${groupId}`
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

function onLessonClick(lesson: Lesson) {
  selectedLesson.value = lesson
  editLessonForm.value = {
    group: lesson.group,
    starts_at_local: localFromIso(lesson.starts_at),
    notes: lesson.notes || '',
  }
}

async function loadTeacherGroups() {
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

function clearDateFilters() {
  if (!dateFilterFrom.value && !dateFilterTo.value) return
  dateFilterFrom.value = ''
  dateFilterTo.value = ''
  void reloadLessons()
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
  if (!selectedLesson.value || !editLessonForm.value.group || !editLessonForm.value.starts_at_local) return
  savingLesson.value = true
  error.value = null
  try {
    const updated = await apiRequest<Lesson>(`/api/academics/lessons/${selectedLesson.value.id}/`, {
      method: 'PATCH',
      body: {
        group: editLessonForm.value.group,
        starts_at: new Date(editLessonForm.value.starts_at_local).toISOString(),
        notes: editLessonForm.value.notes,
      },
    })
    selectedLesson.value = updated
    await reloadLessons()
  } catch (e: any) {
    error.value = e?.payload?.detail || e?.message || 'Не вдалося оновити урок'
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
  grid-template-columns: minmax(160px, 1fr) minmax(160px, 1fr) auto;
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
  background: #514f4f;
  padding: 6px;
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
.dropdown__option:hover {
  background: rgba(255, 255, 255, 0.08);
}
@media (max-width: 640px) {
  .filters {
    grid-template-columns: 1fr;
  }
}
</style>
