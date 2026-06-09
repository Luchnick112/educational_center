<template>
  <AppShell title="Учні">
    <div class="layout">
      <div class="panel">
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

      <div class="panel">
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
            <div class="field__label">Ціна заняття</div>
            <input class="input" type="number" min="0" step="0.01" v-model="lesson_price" :disabled="mode === 'view'" />
          </div>
          <div class="field">
            <div class="field__label">Нотатки</div>
            <textarea class="input ta" v-model="notes" :disabled="mode === 'view'"></textarea>
          </div>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppShell from '@/components/AppShell.vue'
import DataTable from '@/components/DataTable.vue'
import UserAccountForm from '@/components/UserAccountForm.vue'
import { apiRequest } from '@/lib/api'

type Student = {
  id: number
  lesson_price?: string | number | null
  notes?: string | null
  user: number
  user_detail?: { id: number; first_name?: string; last_name?: string; telegram_username?: string; role?: string; phone?: string | null; email?: string }
}

type Mode = 'view' | 'create' | 'edit'

const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)
const formError = ref<string | null>(null)
const rows = ref<Student[]>([])
const selectedId = ref<number | null>(null)
const detail = ref<Student | null>(null)
const mode = ref<Mode>('view')

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

const notes = ref('')
const lesson_price = ref('')

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
    render: (r: Student) => {
      const u = r.user_detail
      if (!u) return '-'
      return `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.telegram_username || `User #${u.id}`
    },
  },
  { key: 'telegram', label: 'Telegram', render: (r: Student) => r.user_detail?.telegram_username || '-' },
  { key: 'lesson_price', label: 'Ціна заняття', render: (r: Student) => r.lesson_price == null ? '-' : String(r.lesson_price) },
]

async function reload() {
  loading.value = true
  error.value = null
  try {
    rows.value = await apiRequest<Student[]>('/api/users/students/')
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
    detail.value = await apiRequest<Student>(`/api/users/students/${id}/`)
    lesson_price.value = detail.value?.lesson_price == null ? '' : String(detail.value.lesson_price)
    notes.value = (detail.value as any)?.notes || ''
  } catch (e: any) {
    formError.value = e?.payload?.detail || e?.message || 'Не вдалося завантажити деталі'
  }
}

function startCreate() {
  mode.value = 'create'
  selectedId.value = null
  detail.value = null
  formError.value = null
  createUser.value = { first_name: '', last_name: '', telegram_username: '', email: '', phone: '', password: '' }
  lesson_price.value = ''
  notes.value = ''
}

function startEdit() {
  if (!selectedId.value || !detail.value) return
  mode.value = 'edit'
  formError.value = null
}

function cancelEdit() {
  mode.value = 'view'
  formError.value = null
  if (detail.value) {
    lesson_price.value = detail.value.lesson_price == null ? '' : String(detail.value.lesson_price)
    notes.value = (detail.value as any)?.notes || ''
  }
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
          role: 'student',
          phone: createUser.value.phone || undefined,
        },
      })
      await reload()
      const student = rows.value.find((s) => s.user === createdUser.id)
      if (student) {
        await apiRequest(`/api/users/students/${student.id}/`, {
          method: 'PATCH',
          body: {
            lesson_price: lesson_price.value === '' ? null : lesson_price.value,
            notes: notes.value || '',
          },
        })
        await loadDetail(student.id)
      }
      mode.value = 'view'
      return
    }

    if (mode.value === 'edit' && selectedId.value) {
      await updateSelectedUserAccount()
      await apiRequest(`/api/users/students/${selectedId.value}/`, {
        method: 'PATCH',
        body: {
          lesson_price: lesson_price.value === '' ? null : lesson_price.value,
          notes: notes.value || '',
        },
      })
      await reload()
      await loadDetail(selectedId.value)
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
  const ok = window.confirm(`Видалити #${id}?`)
  if (!ok) return
  saving.value = true
  formError.value = null
  try {
    await apiRequest(`/api/users/students/${id}/`, { method: 'DELETE' })
    await reload()
    selectedId.value = null
    detail.value = null
    lesson_price.value = ''
    notes.value = ''
  } catch (e: any) {
    formError.value = e?.payload ? JSON.stringify(e.payload) : e?.message || 'Не вдалося видалити'
  } finally {
    saving.value = false
  }
}

onMounted(reload)
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
</style>
