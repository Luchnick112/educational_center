<template>
  <ion-page>
    <MobileHeader title="Уроки" :refresh="load" :loading="loading" />
    <ion-content :fullscreen="true">
      <div class="page-intro">
        <p class="eyebrow">Мій розклад</p>
        <h1>{{ greeting }}</h1>
        <p>{{ lessons.length ? `${lessons.length} останніх занять` : 'Ваші заняття з’являться тут' }}</p>
      </div>

      <div class="page-body">
        <PageState :loading="loading" :error="error" :empty="lessons.length === 0" :retry="load" empty-text="Уроків ще немає">
          <div class="item-list">
            <article v-for="lesson in lessons" :key="lesson.id" class="data-item lesson-item">
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
            </article>
          </div>
        </PageState>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { IonContent, IonPage } from '@ionic/vue'
import MobileHeader from '@/components/MobileHeader.vue'
import PageState from '@/components/PageState.vue'
import { apiRequest } from '@/services/api'
import { usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import type { Lesson, LessonPage, StudyGroup } from '@/types/api'
import { formatDateTime, statusLabel } from '@/utils/format'

const auth = useAuthStore()
const lessons = ref<Lesson[]>([])
const groups = ref<StudyGroup[]>([])
const { loading, error, run } = usePageData()

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

function load() {
  return run(async () => {
    const [lessonPayload, groupPayload] = await Promise.all([
      apiRequest<Lesson[] | LessonPage>('/api/my/lessons/?page=1&page_size=20'),
      apiRequest<StudyGroup[]>('/api/academics/groups/').catch(() => []),
    ])
    lessons.value = Array.isArray(lessonPayload) ? lessonPayload : lessonPayload.results
    groups.value = groupPayload
  })
}

onMounted(load)
</script>
