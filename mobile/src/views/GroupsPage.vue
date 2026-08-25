<template>
  <ion-page>
    <MobileHeader title="Групи" :refresh="load" :loading="loading" />
    <ion-content :fullscreen="true">
      <div class="page-intro page-intro--compact">
        <p class="eyebrow">Навчання</p>
        <h1>Мої групи</h1>
        <p>Склад і прогрес навчальних груп.</p>
      </div>
      <div class="page-body">
        <PageState :loading="loading" :error="error" :empty="groups.length === 0" :retry="load" empty-text="Активних груп немає">
          <div class="item-list">
            <article v-for="group in groups" :key="group.id" class="data-item data-item--stacked">
              <div class="data-item__topline">
                <h2>{{ group.name || `Група #${group.id}` }}</h2>
                <span class="format-badge">{{ group.format === 'individual' ? 'Індивідуальна' : 'Групова' }}</span>
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
  </ion-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { IonContent, IonPage } from '@ionic/vue'
import MobileHeader from '@/components/MobileHeader.vue'
import PageState from '@/components/PageState.vue'
import { apiRequest } from '@/services/api'
import { usePageData } from '@/composables/usePageData'
import type { StudyGroup } from '@/types/api'

const groups = ref<StudyGroup[]>([])
const { loading, error, run } = usePageData()
const load = () => run(async () => { groups.value = await apiRequest<StudyGroup[]>('/api/academics/groups/') })
onMounted(load)
</script>
