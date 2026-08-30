<template>
  <ion-page>
    <MobileHeader
      title="Уроки"
      :refresh="load"
      :loading="loading"
      :action="canManage ? openCreate : undefined"
      action-label="Створити урок"
    />
    <ion-content :fullscreen="true">
      <div class="page-intro">
        <p class="eyebrow">Мій розклад</p>
        <h1>{{ greeting }}</h1>
        <p>{{ lessonsCaption }}</p>
      </div>

      <div class="page-body">
        <p v-if="notice" class="action-notice">{{ notice }}</p>

        <section class="filter-panel" aria-label="Фільтри уроків">
          <div class="filter-panel__header">
            <h2>Фільтри</h2>
            <ion-button fill="clear" size="small" :disabled="!hasLessonFilters || loading" @click="clearLessonFilters">
              Очистити
            </ion-button>
          </div>
          <div class="filter-grid filter-grid--lessons">
            <label class="mobile-field">
              <span>З</span>
              <input v-model="lessonFilters.date_from" class="mobile-control" type="date" @change="load" />
            </label>
            <label class="mobile-field">
              <span>До</span>
              <input v-model="lessonFilters.date_to" class="mobile-control" type="date" @change="load" />
            </label>
            <label v-if="isAdmin" class="mobile-field">
              <span>Викладач</span>
              <select v-model="lessonFilters.teacher" class="mobile-control" @change="load">
                <option value="">Усі викладачі</option>
                <option v-for="teacher in teachers" :key="teacher.id" :value="String(teacher.id)">
                  {{ profileLabel(teacher, 'Викладач') }}
                </option>
              </select>
            </label>
            <label v-if="canManage" class="mobile-field">
              <span>Група</span>
              <select v-model="lessonFilters.group" class="mobile-control" @change="load">
                <option value="">Усі групи</option>
                <option value="individual">Індивідуальні</option>
                <option value="group">Групові</option>
                <option v-for="group in groups" :key="group.id" :value="String(group.id)">
                  {{ group.name || `Група #${group.id}` }}
                </option>
              </select>
            </label>
          </div>
        </section>

        <PageState
          :loading="loading"
          :error="error"
          :empty="lessons.length === 0"
          :retry="load"
          :empty-text="hasLessonFilters ? 'За вибраними фільтрами уроків немає' : 'Уроків ще немає'"
        >
          <div class="item-list">
            <article
              v-for="lesson in lessons"
              :key="lesson.id"
              class="data-item lesson-item interactive-item"
              role="button"
              tabindex="0"
              @click="openDetail(lesson)"
              @keydown.enter="openDetail(lesson)"
            >
              <div class="date-tile" aria-hidden="true">
                <strong>{{ day(lesson.starts_at) }}</strong>
                <span>{{ month(lesson.starts_at) }}</span>
              </div>
              <div class="data-item__main">
                <div class="data-item__topline">
                  <h2>{{ groupName(lesson.group) }}</h2>
                  <span class="status" :data-status="lesson.status">{{ statusLabel(lesson.status) }}</span>
                </div>
                <p>{{ formatDateTime(lesson.starts_at) }}</p>
                <p v-if="lesson.notes" class="data-item__note">{{ lesson.notes }}</p>
              </div>
              <ion-icon class="item-chevron" :icon="chevronForwardOutline" aria-hidden="true" />
            </article>
          </div>
        </PageState>
      </div>
    </ion-content>

    <ion-modal :is-open="createOpen" @didDismiss="closeCreate">
      <ion-header class="ion-no-border">
        <ion-toolbar>
          <ion-buttons slot="start"><ion-button @click="closeCreate">Скасувати</ion-button></ion-buttons>
          <ion-title>Новий урок</ion-title>
          <ion-buttons slot="end"><ion-button strong :disabled="saving" @click="createLesson">Створити</ion-button></ion-buttons>
        </ion-toolbar>
      </ion-header>
      <ion-content>
        <form class="mobile-form" @submit.prevent="createLesson">
          <p v-if="formError" class="form-error form-error--panel">{{ formError }}</p>
          <label class="mobile-field">
            <span>Група</span>
            <select v-model.number="createForm.group" class="mobile-control" required>
              <option :value="null" disabled>Оберіть групу</option>
              <option v-for="group in activeGroups" :key="group.id" :value="group.id">{{ group.name || `Група #${group.id}` }}</option>
            </select>
          </label>
          <label class="mobile-field">
            <span>Дата і час</span>
            <input v-model="createForm.starts_at" class="mobile-control" type="datetime-local" required />
          </label>
          <label class="mobile-field">
            <span>Нотатки</span>
            <textarea v-model="createForm.notes" class="mobile-control" placeholder="Необов’язково" />
          </label>
          <ion-button class="mobile-submit" expand="block" type="submit" :disabled="saving">
            <ion-spinner v-if="saving" name="crescent" />
            <span v-else>Створити урок</span>
          </ion-button>
        </form>
      </ion-content>
    </ion-modal>

    <ion-modal :is-open="detailOpen" @didDismiss="closeDetail">
      <ion-header class="ion-no-border">
        <ion-toolbar>
          <ion-buttons slot="start"><ion-button @click="closeDetail">Закрити</ion-button></ion-buttons>
          <ion-title>Урок</ion-title>
          <ion-buttons v-if="canManage && selectedLesson" slot="end">
            <ion-button strong :disabled="saving" @click="saveLesson">Зберегти</ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      <ion-content>
        <div v-if="detailLoading" class="page-state"><ion-spinner name="crescent" /></div>
        <form v-else-if="selectedLesson" class="mobile-form" @submit.prevent="saveLesson">
          <p v-if="formError" class="form-error form-error--panel">{{ formError }}</p>

          <section class="detail-summary">
            <div>
              <span>Група</span>
              <strong>{{ groupName(selectedLesson.group) }}</strong>
            </div>
            <span class="status" :data-status="selectedLesson.status">{{ statusLabel(selectedLesson.status) }}</span>
          </section>

          <label class="mobile-field">
            <span>Дата і час</span>
            <input v-model="detailForm.starts_at" class="mobile-control" type="datetime-local" :disabled="!canEditTime" required />
          </label>
          <label class="mobile-field">
            <span>Нотатки</span>
            <textarea v-model="detailForm.notes" class="mobile-control" :disabled="!canManage" placeholder="Нотатки або причина скасування" />
          </label>

          <fieldset class="choice-list participant-list">
            <legend>Присутність учнів</legend>
            <p v-if="!selectedLesson.participants?.length" class="field-hint">Учасників уроку немає</p>
            <label v-for="participant in selectedLesson.participants" :key="participant.id" class="choice-row">
              <span>{{ participantName(participant) }}</span>
              <select
                class="attendance-select"
                :value="participant.attendance_status"
                :disabled="!canMarkAttendance || savingAttendance === participant.id"
                :aria-label="`Присутність: ${participantName(participant)}`"
                @change="markAttendance(participant, $event)"
              >
                <option value="pending" disabled>Не позначено</option>
                <option value="present">Присутній</option>
                <option value="absent">Відсутній</option>
              </select>
            </label>
          </fieldset>

          <ion-button v-if="canManage" class="mobile-submit" expand="block" type="submit" fill="outline" :disabled="saving">
            Зберегти час і нотатки
          </ion-button>

          <div v-if="canManage" class="workflow-actions">
            <ion-button
              v-if="selectedLesson.status === 'scheduled'"
              color="primary"
              :disabled="saving"
              @click="completeLesson"
            >
              <ion-icon slot="start" :icon="checkmarkCircleOutline" />
              Завершити
            </ion-button>
            <ion-button
              v-if="selectedLesson.status === 'scheduled'"
              color="danger"
              fill="outline"
              :disabled="saving"
              @click="cancelLesson"
            >
              <ion-icon slot="start" :icon="closeCircleOutline" />
              Скасувати
            </ion-button>
            <ion-button
              v-if="selectedLesson.status !== 'scheduled'"
              fill="outline"
              :disabled="saving"
              @click="restoreLesson"
            >
              <ion-icon slot="start" :icon="refreshOutline" />
              Повернути в заплановані
            </ion-button>
          </div>
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
  IonContent,
  IonHeader,
  IonIcon,
  IonModal,
  IonPage,
  IonSpinner,
  IonTitle,
  IonToolbar,
} from '@ionic/vue'
import {
  checkmarkCircleOutline,
  chevronForwardOutline,
  closeCircleOutline,
  refreshOutline,
} from 'ionicons/icons'
import MobileHeader from '@/components/MobileHeader.vue'
import PageState from '@/components/PageState.vue'
import { ApiError, apiRequest, errorMessage } from '@/services/api'
import { usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import type { Lesson, LessonPage, LessonParticipant, ProfileOption, StudyGroup } from '@/types/api'
import { formatDateTime, statusLabel } from '@/utils/format'

const auth = useAuthStore()
const lessons = ref<Lesson[]>([])
const groups = ref<StudyGroup[]>([])
const teachers = ref<ProfileOption[]>([])
const createOpen = ref(false)
const detailOpen = ref(false)
const detailLoading = ref(false)
const selectedLesson = ref<Lesson | null>(null)
const saving = ref(false)
const savingAttendance = ref<number | null>(null)
const formError = ref('')
const notice = ref('')
const { loading, error, run } = usePageData()

const isAdmin = computed(() => Boolean(auth.me?.is_staff || auth.me?.role === 'admin'))
const canManage = computed(() => isAdmin.value || auth.me?.role === 'teacher')
const canMarkAttendance = computed(() => canManage.value && selectedLesson.value?.status === 'scheduled')
const canEditTime = computed(() => {
  if (!canManage.value || !selectedLesson.value) return false
  return isAdmin.value || ['scheduled', 'cancelled'].includes(selectedLesson.value.status)
})
const activeGroups = computed(() => groups.value.filter((group) => group.is_active !== false))

const lessonFilters = reactive({
  date_from: '',
  date_to: '',
  teacher: '',
  group: '',
})

const hasLessonFilters = computed(() => Object.values(lessonFilters).some(Boolean))
const lessonsCaption = computed(() => {
  if (lessons.value.length) return `${lessons.value.length} занять`
  return hasLessonFilters.value ? 'Змініть параметри фільтра' : 'Ваші заняття з’являться тут'
})

const createForm = reactive({ group: null as number | null, starts_at: '', notes: '' })
const detailForm = reactive({ starts_at: '', notes: '' })

const greeting = computed(() => {
  const firstName = auth.me?.first_name?.trim()
  return firstName ? `Вітаємо, ${firstName}` : 'Ваші заняття'
})

function datePart(value: string, part: 'day' | 'month') {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return part === 'day'
    ? new Intl.DateTimeFormat('uk-UA', { day: '2-digit' }).format(date)
    : new Intl.DateTimeFormat('uk-UA', { month: 'short' }).format(date).replace('.', '')
}

const day = (value: string) => datePart(value, 'day')
const month = (value: string) => datePart(value, 'month')
const groupName = (id: number) => groups.value.find((group) => group.id === id)?.name || `Група #${id}`

function profileLabel(profile: ProfileOption, fallback: string) {
  const user = profile.user_detail
  if (!user) return `${fallback} #${profile.id}`
  return [user.first_name, user.last_name].filter(Boolean).join(' ')
    || user.telegram_username
    || user.email
    || `${fallback} #${profile.id}`
}

function participantName(participant: LessonParticipant) {
  return [participant.student_first_name, participant.student_last_name].filter(Boolean).join(' ')
    || `Учень #${participant.student}`
}

function localDateTime(value: Date | string) {
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const pad = (part: number) => String(part).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function nextLessonTime() {
  const date = new Date()
  date.setMinutes(0, 0, 0)
  date.setHours(date.getHours() + 1)
  return localDateTime(date)
}

function toIso(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date.toISOString()
}

function lessonsPath() {
  const params = new URLSearchParams({ page: '1', page_size: '20' })
  if (lessonFilters.date_from) params.set('date_from', lessonFilters.date_from)
  if (lessonFilters.date_to) params.set('date_to', lessonFilters.date_to)
  if (lessonFilters.teacher) params.set('teacher', lessonFilters.teacher)
  if (lessonFilters.group === 'individual' || lessonFilters.group === 'group') {
    params.set('group_format', lessonFilters.group)
  } else if (lessonFilters.group) {
    params.set('group', lessonFilters.group)
  }
  return `/api/my/lessons/?${params.toString()}`
}

function load() {
  return run(async () => {
    const [lessonPayload, groupPayload, teacherPayload] = await Promise.all([
      apiRequest<Lesson[] | LessonPage>(lessonsPath()),
      apiRequest<StudyGroup[]>('/api/academics/groups/').catch(() => []),
      isAdmin.value ? apiRequest<ProfileOption[]>('/api/users/teachers/').catch(() => []) : Promise.resolve([]),
    ])
    lessons.value = Array.isArray(lessonPayload) ? lessonPayload : lessonPayload.results
    groups.value = groupPayload
    teachers.value = teacherPayload
  })
}

async function clearLessonFilters() {
  Object.assign(lessonFilters, { date_from: '', date_to: '', teacher: '', group: '' })
  await load()
}

function openCreate() {
  createForm.group = activeGroups.value[0]?.id ?? null
  createForm.starts_at = nextLessonTime()
  createForm.notes = ''
  formError.value = ''
  createOpen.value = true
}

function closeCreate() {
  if (saving.value) return
  createOpen.value = false
  formError.value = ''
}

async function createLesson() {
  const startsAt = toIso(createForm.starts_at)
  if (!createForm.group || !startsAt) {
    formError.value = 'Оберіть групу та коректний час уроку.'
    return
  }
  saving.value = true
  formError.value = ''
  try {
    await apiRequest('/api/academics/lessons/', {
      method: 'POST',
      body: { group: createForm.group, starts_at: startsAt, status: 'scheduled', notes: createForm.notes },
    })
    createOpen.value = false
    notice.value = 'Урок створено.'
    await load()
  } catch (caught) {
    formError.value = requestError(caught, 'Не вдалося створити урок')
  } finally {
    saving.value = false
  }
}

async function openDetail(lesson: Lesson) {
  detailOpen.value = true
  detailLoading.value = true
  formError.value = ''
  try {
    selectedLesson.value = await apiRequest<Lesson>(`/api/academics/lessons/${lesson.id}/`)
    detailForm.starts_at = localDateTime(selectedLesson.value.starts_at)
    detailForm.notes = selectedLesson.value.notes || ''
  } catch (caught) {
    formError.value = requestError(caught, 'Не вдалося завантажити урок')
    selectedLesson.value = lesson
  } finally {
    detailLoading.value = false
  }
}

function closeDetail() {
  if (saving.value || savingAttendance.value) return
  detailOpen.value = false
  selectedLesson.value = null
  formError.value = ''
}

async function refreshDetail() {
  if (!selectedLesson.value) return
  selectedLesson.value = await apiRequest<Lesson>(`/api/academics/lessons/${selectedLesson.value.id}/`)
  detailForm.starts_at = localDateTime(selectedLesson.value.starts_at)
  detailForm.notes = selectedLesson.value.notes || ''
  await load()
}

async function saveLesson() {
  if (!selectedLesson.value || !canManage.value) return
  const startsAt = toIso(detailForm.starts_at)
  if (!startsAt) {
    formError.value = 'Вкажіть коректну дату та час.'
    return
  }
  saving.value = true
  formError.value = ''
  try {
    await apiRequest(`/api/academics/lessons/${selectedLesson.value.id}/`, {
      method: 'PATCH',
      body: { starts_at: startsAt, notes: detailForm.notes },
    })
    notice.value = 'Урок оновлено.'
    await refreshDetail()
  } catch (caught) {
    formError.value = requestError(caught, 'Не вдалося оновити урок')
  } finally {
    saving.value = false
  }
}

async function markAttendance(participant: LessonParticipant, event: Event) {
  if (!selectedLesson.value || !canMarkAttendance.value) return
  const target = event.target as HTMLSelectElement
  const previous = participant.attendance_status
  const attendanceStatus = target.value
  participant.attendance_status = attendanceStatus
  savingAttendance.value = participant.id
  formError.value = ''
  try {
    await apiRequest(`/api/academics/lessons/${selectedLesson.value.id}/mark-attendance/`, {
      method: 'POST',
      body: { participant_id: participant.id, attendance_status: attendanceStatus },
    })
    await refreshDetail()
  } catch (caught) {
    participant.attendance_status = previous
    target.value = previous
    formError.value = requestError(caught, 'Не вдалося змінити присутність')
  } finally {
    savingAttendance.value = null
  }
}

async function completeLesson() {
  if (!selectedLesson.value) return
  saving.value = true
  formError.value = ''
  try {
    await apiRequest(`/api/academics/lessons/${selectedLesson.value.id}/complete/`, {
      method: 'POST',
      body: { notes: detailForm.notes },
    })
    notice.value = 'Урок завершено.'
    await refreshDetail()
  } catch (caught) {
    formError.value = requestError(caught, 'Не вдалося завершити урок')
  } finally {
    saving.value = false
  }
}

async function cancelLesson() {
  if (!selectedLesson.value) return
  const reason = detailForm.notes.trim()
  if (!reason) {
    formError.value = 'Вкажіть причину скасування в нотатках.'
    return
  }
  saving.value = true
  formError.value = ''
  try {
    if (isAdmin.value) {
      await apiRequest(`/api/academics/lessons/${selectedLesson.value.id}/cancel/`, {
        method: 'POST',
        body: { reason },
      })
    } else {
      await apiRequest(`/api/academics/lessons/${selectedLesson.value.id}/`, {
        method: 'PATCH',
        body: { status: 'cancelled', notes: reason },
      })
    }
    notice.value = 'Урок скасовано.'
    await refreshDetail()
  } catch (caught) {
    formError.value = requestError(caught, 'Не вдалося скасувати урок')
  } finally {
    saving.value = false
  }
}

async function restoreLesson() {
  if (!selectedLesson.value) return
  saving.value = true
  formError.value = ''
  try {
    await apiRequest(`/api/academics/lessons/${selectedLesson.value.id}/`, {
      method: 'PATCH',
      body: { status: 'scheduled', starts_at: toIso(detailForm.starts_at), notes: detailForm.notes },
    })
    notice.value = 'Урок повернуто в заплановані.'
    await refreshDetail()
  } catch (caught) {
    formError.value = requestError(caught, 'Не вдалося змінити статус уроку')
  } finally {
    saving.value = false
  }
}

function requestError(caught: unknown, fallback: string) {
  return caught instanceof ApiError ? errorMessage(caught.payload, fallback) : fallback
}

onMounted(load)
</script>
