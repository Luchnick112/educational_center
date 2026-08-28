<template>
  <ion-page>
    <MobileHeader
      title="Користувачі"
      :refresh="load"
      :loading="loading"
      :action="openCreate"
      action-label="Створити користувача"
    />
    <ion-content :fullscreen="true">
      <div class="page-intro page-intro--compact">
        <p class="eyebrow">Адміністрування</p>
        <h1>Користувачі</h1>
        <p>{{ users.length }} облікових записів</p>
      </div>

      <div class="page-body">
        <p v-if="notice" class="action-notice">{{ notice }}</p>

        <div class="list-filters">
          <label class="mobile-field">
            <span>Пошук</span>
            <input
              v-model="query"
              class="mobile-control"
              type="search"
              placeholder="Ім’я, телефон або email"
            />
          </label>
          <label class="mobile-field">
            <span>Роль</span>
            <select v-model="roleFilter" class="mobile-control">
              <option value="">Усі ролі</option>
              <option v-for="option in roleOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
        </div>

        <PageState
          :loading="loading"
          :error="error"
          :empty="filteredUsers.length === 0"
          :retry="load"
          :empty-text="users.length ? 'За цими фільтрами нічого не знайдено' : 'Користувачів немає'"
        >
          <div class="item-list">
            <article v-for="user in filteredUsers" :key="user.id" class="data-item user-item">
              <div class="avatar" aria-hidden="true">{{ initials(user) }}</div>
              <div class="data-item__main user-item__identity">
                <h2>{{ userName(user) }}</h2>
                <p v-if="user.telegram_username">{{ user.telegram_username }}</p>
                <p v-if="user.email">{{ user.email }}</p>
                <p v-if="user.phone">{{ user.phone }}</p>
                <div class="user-item__meta">
                  <span class="role-badge" :data-role="user.role">{{ roleLabel(user.role) }}</span>
                  <span v-if="!user.is_active" class="inactive-label">Неактивний</span>
                </div>
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
          <ion-title>Новий користувач</ion-title>
          <ion-buttons slot="end">
            <ion-button strong :disabled="saving" @click="saveUser">Створити</ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>

      <ion-content>
        <form class="mobile-form" @submit.prevent="saveUser">
          <p v-if="formError" class="form-error form-error--panel">{{ formError }}</p>

          <div class="mobile-form-grid">
            <label class="mobile-field">
              <span>Ім’я</span>
              <input v-model.trim="form.first_name" class="mobile-control" autocomplete="given-name" />
            </label>
            <label class="mobile-field">
              <span>Прізвище</span>
              <input v-model.trim="form.last_name" class="mobile-control" autocomplete="family-name" />
            </label>
          </div>

          <label class="mobile-field">
            <span>Роль</span>
            <select v-model="form.role" class="mobile-control" required>
              <option v-for="option in roleOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>

          <label class="mobile-field">
            <span>Telegram</span>
            <input
              v-model.trim="form.telegram_username"
              class="mobile-control"
              type="text"
              autocomplete="off"
              placeholder="@username"
            />
          </label>

          <label class="mobile-field">
            <span>Email</span>
            <input v-model.trim="form.email" class="mobile-control" type="email" autocomplete="email" />
          </label>

          <label class="mobile-field">
            <span>Телефон</span>
            <input v-model.trim="form.phone" class="mobile-control" type="tel" autocomplete="tel" />
          </label>

          <label class="mobile-field">
            <span>Початковий пароль</span>
            <input
              v-model="form.password"
              class="mobile-control"
              type="password"
              minlength="8"
              autocomplete="new-password"
              placeholder="Необов’язково"
            />
          </label>

          <ion-button class="mobile-submit" expand="block" type="submit" :disabled="saving">
            <ion-spinner v-if="saving" name="crescent" />
            <span v-else>Створити користувача</span>
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
  IonContent,
  IonHeader,
  IonModal,
  IonPage,
  IonSpinner,
  IonTitle,
  IonToolbar,
} from '@ionic/vue'
import MobileHeader from '@/components/MobileHeader.vue'
import PageState from '@/components/PageState.vue'
import { ApiError, apiRequest, errorMessage } from '@/services/api'
import { usePageData } from '@/composables/usePageData'
import type { UserAccount, UserRole } from '@/types/api'

const roleOptions = [
  { value: 'student', label: 'Учень' },
  { value: 'parent', label: 'Батьки' },
  { value: 'teacher', label: 'Викладач' },
  { value: 'admin', label: 'Адміністратор' },
] as const

const users = ref<UserAccount[]>([])
const query = ref('')
const roleFilter = ref('')
const editorOpen = ref(false)
const saving = ref(false)
const formError = ref('')
const notice = ref('')
const { loading, error, run } = usePageData()

const form = reactive({
  first_name: '',
  last_name: '',
  role: 'student' as UserRole,
  telegram_username: '',
  email: '',
  phone: '',
  password: '',
})

const filteredUsers = computed(() => {
  const needle = query.value.trim().toLocaleLowerCase('uk')
  return users.value.filter((user) => {
    if (roleFilter.value && user.role !== roleFilter.value) return false
    if (!needle) return true
    return [
      user.first_name,
      user.last_name,
      user.telegram_username,
      user.email,
      user.phone,
    ].some((value) => String(value ?? '').toLocaleLowerCase('uk').includes(needle))
  })
})

const load = () => run(async () => {
  users.value = await apiRequest<UserAccount[]>('/api/users/')
})

function roleLabel(role: UserRole) {
  return roleOptions.find((option) => option.value === role)?.label ?? role
}

function userName(user: UserAccount) {
  return [user.first_name, user.last_name].filter(Boolean).join(' ')
    || user.telegram_username
    || user.email
    || user.phone
    || `Користувач #${user.id}`
}

function initials(user: UserAccount) {
  const value = [user.first_name, user.last_name]
    .filter(Boolean)
    .map((part) => part.charAt(0))
    .join('')
  return value.slice(0, 2).toUpperCase() || '#'
}

function resetForm() {
  Object.assign(form, {
    first_name: '',
    last_name: '',
    role: 'student',
    telegram_username: '',
    email: '',
    phone: '',
    password: '',
  })
  formError.value = ''
}

function openCreate() {
  resetForm()
  editorOpen.value = true
}

function closeEditor() {
  if (saving.value) return
  editorOpen.value = false
  formError.value = ''
}

async function saveUser() {
  if (!form.telegram_username && !form.email && !form.phone) {
    formError.value = 'Вкажіть Telegram, email або телефон.'
    return
  }

  saving.value = true
  formError.value = ''
  try {
    const body: Record<string, string> = {
      first_name: form.first_name,
      last_name: form.last_name,
      role: form.role,
      telegram_username: form.telegram_username,
      email: form.email,
      phone: form.phone,
    }
    if (form.password) body.password = form.password

    await apiRequest<UserAccount>('/api/users/register/', { method: 'POST', body })
    editorOpen.value = false
    notice.value = 'Користувача створено.'
    await load()
  } catch (caught) {
    formError.value = caught instanceof ApiError
      ? errorMessage(caught.payload, 'Не вдалося створити користувача')
      : 'Не вдалося створити користувача'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
