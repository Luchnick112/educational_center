<template>
  <ion-page>
    <MobileHeader title="Діти" :refresh="load" :loading="loading" />
    <ion-content :fullscreen="true">
      <div class="page-intro page-intro--compact">
        <p class="eyebrow">Родина</p>
        <h1>Мої діти</h1>
        <p>Навчальні профілі, пов’язані з вашим акаунтом.</p>
      </div>
      <div class="page-body">
        <PageState :loading="loading" :error="error" :empty="children.length === 0" :retry="load" empty-text="Пов’язаних профілів немає">
          <div class="item-list">
            <article v-for="child in children" :key="child.id" class="data-item profile-item">
              <div class="avatar">{{ initials(child) }}</div>
              <div class="data-item__main">
                <h2>{{ studentName(child) }}</h2>
                <p>{{ child.user_detail?.email || child.user_detail?.telegram_username || 'Контакт не вказано' }}</p>
              </div>
            </article>
          </div>
        </PageState>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { IonContent, IonPage } from '@ionic/vue'
import MobileHeader from '@/components/MobileHeader.vue'
import PageState from '@/components/PageState.vue'
import { apiRequest } from '@/services/api'
import { usePageData } from '@/composables/usePageData'
import type { Student } from '@/types/api'

const children = ref<Student[]>([])
const { loading, error, run } = usePageData()
const studentName = (student: Student) =>
  [student.user_detail?.first_name, student.user_detail?.last_name].filter(Boolean).join(' ') || `Учень #${student.id}`
const initials = (student: Student) =>
  [student.user_detail?.first_name, student.user_detail?.last_name].filter(Boolean).map((part) => part?.[0]).join('').toUpperCase() || 'У'
const load = () => run(async () => { children.value = await apiRequest<Student[]>('/api/my/children/') })
onMounted(load)
</script>
