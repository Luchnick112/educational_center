<template>
  <AppShell :title="isCreateRoute ? 'Створити вчителя' : 'Вчителі'">
    <div class="layout" :class="{ 'layout--single': isCreateRoute }">
      <div v-if="!isCreateRoute" class="panel">
        <div class="row">
          <div class="panel__title">Список</div>
          <div class="actions">
            <button class="btn btn--ghost" type="button" :disabled="loading || saving" @click="reload">Оновити</button>
            <button class="btn" type="button" :disabled="loading || saving" @click="startCreate">Створити</button>
            <button class="btn btn--ghost" type="button" :disabled="!selectedId || loading || saving" @click="startEdit">Редагувати</button>
            <button class="btn btn--ghost" type="button" :disabled="!selectedId || loading || saving" @click="onDelete">Видалити</button>
          </div>
        </div>
        <div v-if="loading" class="muted">Завантаження...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <DataTable
          v-else
          :columns="columns"
          :rows="rows"
          :rowKey="(r) => r.id"
          :onRowClick="(r) => loadDetail(r.id)"
        />
      </div>

      <div v-if="!isCreateRoute || mode === 'create'" class="panel">
        <div class="formwrap">
          <div class="formwrap__header">
            <div class="formwrap__title">{{ formTitle }}</div>
            <div class="formwrap__actions">
              <button v-if="mode === 'view'" class="btn btn--ghost" type="button" :disabled="!selectedId" @click="startEdit">Редагувати</button>
              <button v-else class="btn btn--ghost" type="button" :disabled="saving" @click="cancelEdit">Скасувати</button>
              <button v-if="mode !== 'view'" class="btn" type="button" :disabled="saving" @click="submitForm">
                {{ saving ? 'Збереження...' : mode === 'create' ? 'Створити' : 'Зберегти' }}
              </button>
            </div>
          </div>

          <div v-if="formError" class="error">{{ formError }}</div>
          <div v-else-if="mode === 'view' && !selectedId" class="muted">Оберіть рядок зі списку.</div>

          <UserAccountForm
            v-if="mode === 'create'"
            title="Акаунт"
            :model="createUser"
            :showPassword="false"
          />
          <UserAccountForm
            v-else-if="selectedUserDetail"
            title="Акаунт"
            :model="selectedUserDetail"
            :disabled="mode === 'view'"
          />

          <div class="field">
            <div class="field__label">Ставка (за годину)</div>
            <input class="input" type="number" step="0.01" v-model="hourly_rate" :disabled="mode === 'view'" />
          </div>
          <div class="field">
            <div class="field__label">Біо</div>
            <textarea class="input ta" v-model="bio" :disabled="mode === 'view'"></textarea>
          </div>
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
import UserAccountForm from '@/components/UserAccountForm.vue'
import { apiRequest } from '@/lib/api'

type Teacher = {
  id: number
  hourly_rate: string | number | null
  bio: string | null
  user: number
  user_detail?: { first_name?: string; last_name?: string; telegram_username?: string; email?: string; phone?: string }
}

type Mode = 'view' | 'create' | 'edit'

const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)
const formError = ref<string | null>(null)
const rows = ref<Teacher[]>([])
const selectedId = ref<number | null>(null)
const detail = ref<Teacher | null>(null)
const mode = ref<Mode>('view')
const route = useRoute()
const router = useRouter()
const isCreateRoute = computed(() => route.name === 'teachers-create')

const createUser = ref({
  first_name: '',
  last_name: '',
  telegram_username: '',
  email: '',
  phone: '',
  password: '',
})

const selectedUserDetail = computed(() => {
  const u = detail.value?.user_detail
  if (!u) return null
  return {
    first_name: u.first_name || '',
    last_name: u.last_name || '',
    telegram_username: u.telegram_username || '',
    email: (u as any).email || '',
    phone: (u as any).phone || '',
  }
})

async function updateSelectedUserAccount() {
  if (!detail.value || !selectedUserDetail.value) return
  await apiRequest(`/api/users/${detail.value.user}/`, {
    method: 'PATCH',
    body: {
      first_name: selectedUserDetail.value.first_name,
      last_name: selectedUserDetail.value.last_name,
      telegram_username: selectedUserDetail.value.telegram_username || null,
      email: selectedUserDetail.value.email || '',
      phone: selectedUserDetail.value.phone || '',
    },
  })
}

const hourly_rate = ref('')
const bio = ref('')

function teacherProfilePayload() {
  return {
    hourly_rate: hourly_rate.value === '' ? '0.00' : hourly_rate.value,
    bio: bio.value || '',
  }
}

const formTitle = computed(() => {
  if (mode.value === 'create') return 'Створити'
  if (mode.value === 'edit' && selectedId.value) return `Редагувати #${selectedId.value}`
  return 'Деталі'
})

const columns = [
  { key: 'id', label: 'ID' },
  {
    key: 'name',
    label: "Ім'я",
    render: (r: Teacher) => {
      const u = r.user_detail
      if (!u) return '-'
      return `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.telegram_username || '-'
    },
  },
  { key: 'telegram', label: 'Telegram', render: (r: Teacher) => r.user_detail?.telegram_username || '-' },
  { key: 'hourly_rate', label: 'Ставка', render: (r: Teacher) => (r.hourly_rate ?? '-') as any },
]

async function reload() {
  loading.value = true
  error.value = null
  try {
    rows.value = await apiRequest<Teacher[]>('/api/users/teachers/')
  } catch (e: any) {
    error.value = e?.payload?.detail || e?.message || 'Не вдалося завантажити'
    rows.value = []
  } finally {
    loading.value = false
  }
}

async function loadDetail(id: number) {
  selectedId.value = id
  mode.value = 'view'
  formError.value = null
  try {
    detail.value = await apiRequest<Teacher>(`/api/users/teachers/${id}/`)
    hourly_rate.value = detail.value?.hourly_rate == null ? '' : String(detail.value.hourly_rate)
    bio.value = detail.value?.bio || ''
  } catch (e: any) {
    formError.value = e?.payload?.detail || e?.message || 'Не вдалося завантажити деталі'
  }
}

function startCreate() {
  router.push({ name: 'teachers-create' })
}

function resetCreateForm() {
  mode.value = 'create'
  selectedId.value = null
  detail.value = null
  formError.value = null
  createUser.value = { first_name: '', last_name: '', telegram_username: '', email: '', phone: '', password: '' }
  hourly_rate.value = ''
  bio.value = ''
}

function startEdit() {
  if (!selectedId.value || !detail.value) return
  mode.value = 'edit'
  formError.value = null
}

function cancelEdit() {
  if (isCreateRoute.value) {
    router.push({ name: 'teachers' })
    return
  }
  mode.value = 'view'
  formError.value = null
  if (detail.value) {
    hourly_rate.value = detail.value.hourly_rate == null ? '' : String(detail.value.hourly_rate)
    bio.value = detail.value.bio || ''
  }
}

function closeEditor() {
  if (isCreateRoute.value) {
    router.push({ name: 'teachers' })
  }
  selectedId.value = null
  detail.value = null
  mode.value = 'view'
  formError.value = null
  createUser.value = { first_name: '', last_name: '', telegram_username: '', email: '', phone: '', password: '' }
  hourly_rate.value = ''
  bio.value = ''
}

async function submitForm() {
  if (mode.value === 'view') return
  saving.value = true
  formError.value = null
  try {
    if (mode.value === 'create') {
      const createdUser = await apiRequest<any>('/api/users/register/', {
        method: 'POST',
        auth: true,
        body: {
          first_name: createUser.value.first_name,
          last_name: createUser.value.last_name,
          telegram_username: createUser.value.telegram_username,
          email: createUser.value.email || undefined,
          role: 'teacher',
          phone: createUser.value.phone || undefined,
        },
      })
      await reload()
      const teacher = rows.value.find((t) => t.user === createdUser.id)
      if (teacher) {
        await apiRequest(`/api/users/teachers/${teacher.id}/`, {
          method: 'PATCH',
          body: teacherProfilePayload(),
        })
      }
      await reload()
      closeEditor()
      return
    }

    if (mode.value === 'edit' && selectedId.value) {
      await updateSelectedUserAccount()
      await apiRequest(`/api/users/teachers/${selectedId.value}/`, {
        method: 'PATCH',
        body: teacherProfilePayload(),
      })
      await reload()
      closeEditor()
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
  const ok = window.confirm(`Видалити #${id}?`)
  if (!ok) return
  saving.value = true
  formError.value = null
  try {
    await apiRequest(`/api/users/teachers/${id}/`, { method: 'DELETE' })
    await reload()
    selectedId.value = null
    detail.value = null
    hourly_rate.value = ''
    bio.value = ''
  } catch (e: any) {
    formError.value = e?.payload ? JSON.stringify(e.payload) : e?.message || 'Не вдалося видалити'
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  if (isCreateRoute.value) {
    resetCreateForm()
    loading.value = false
    return
  }
  reload()
})

watch(
  () => route.name,
  (name) => {
    if (name === 'teachers-create') {
      resetCreateForm()
      loading.value = false
    } else if (mode.value === 'create') {
      closeEditor()
      void reload()
    }
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
.layout--single {
  grid-template-columns: minmax(0, 720px);
}
.actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.formwrap {
  display: grid;
  gap: 12px;
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
.field {
  display: grid;
  gap: 6px;
}
.field__label {
  font-size: 12px;
  color: var(--muted);
}
.ta {
  min-height: 90px;
  resize: vertical;
}
@media (max-width: 980px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 640px) {
  .actions,
  .formwrap__actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    width: 100%;
  }
  .actions .btn,
  .formwrap__actions .btn {
    width: 100%;
  }
  .formwrap__header {
    flex-direction: column;
    align-items: stretch;
  }
}
@media (max-width: 420px) {
  .actions,
  .formwrap__actions {
    grid-template-columns: 1fr;
  }
}
</style>
