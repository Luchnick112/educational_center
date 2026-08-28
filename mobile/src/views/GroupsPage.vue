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
        <PageState :loading="loading" :error="error" :empty="groups.length === 0" :retry="load" empty-text="Активних груп немає">
          <div class="item-list">
            <article v-for="group in groups" :key="group.id" class="data-item data-item--stacked">
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
            <ion-button @click="closeEditor">Скасувати</ion-button>
          </ion-buttons>
          <ion-title>{{ editingId ? 'Редагувати групу' : 'Нова група' }}</ion-title>
          <ion-buttons slot="end">
            <ion-button strong :disabled="saving" @click="saveGroup">Зберегти</ion-button>
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

          <ion-button class="mobile-submit" expand="block" type="submit" :disabled="saving">
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
import type { Enrollment, ProfileOption, StudyGroup, Subject } from '@/types/api'

const auth = useAuthStore()
const groups = ref<StudyGroup[]>([])
const subjects = ref<Subject[]>([])
const students = ref<ProfileOption[]>([])
const teachers = ref<ProfileOption[]>([])
const enrollments = ref<Enrollment[]>([])
const editorOpen = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const formError = ref('')
const notice = ref('')
const { loading, error, run } = usePageData()

const isAdmin = computed(() => Boolean(auth.me?.is_staff || auth.me?.role === 'admin'))
const canManage = computed(() => isAdmin.value || auth.me?.role === 'teacher')

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

function profileLabel(profile: ProfileOption, fallback: string) {
  const user = profile.user_detail
  if (!user) return `${fallback} #${profile.id}`
  return [user.first_name, user.last_name].filter(Boolean).join(' ')
    || user.telegram_username
    || user.email
    || `${fallback} #${profile.id}`
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
    formError.value = ''
    editorOpen.value = true
  } catch (caught) {
    error.value = caught instanceof ApiError ? errorMessage(caught.payload) : 'Не вдалося завантажити групу'
  }
}

function closeEditor() {
  if (saving.value) return
  editorOpen.value = false
  editingId.value = null
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

onMounted(load)
</script>
