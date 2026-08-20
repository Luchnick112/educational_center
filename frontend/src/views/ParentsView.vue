<template>
  <AppShell :title="isCreateRoute ? 'Створити батька' : 'Батьки'">
    <div class="layout" :class="{ 'layout--single': isCreateRoute }">
      <div v-if="!isCreateRoute" class="panel list-panel" :class="{ 'mobile-hidden-when-detail': selectedId }">
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
          :onRowClick="(r) => openDetail(r.id)"
        />
      </div>

      <div v-if="!isCreateRoute || mode === 'create'" class="panel detail-panel" :class="{ 'detail-panel--active': selectedId || mode === 'create' }">
        <div class="formwrap">
          <div class="formwrap__header">
            <div class="formwrap__title">{{ formTitle }}</div>
            <div class="formwrap__actions">
              <button v-if="mode === 'view' && selectedId" class="btn btn--ghost" type="button" @click="closeEditorAndRoute">Назад</button>
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
            <div class="field__label">Нотатки для білінгу</div>
            <textarea class="input ta" v-model="billing_notes" :disabled="mode === 'view'"></textarea>
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
import { pushDetailRoute, replaceWithoutDetailRoute, routeQueryId } from '@/lib/detailRoute'

type Parent = {
  id: number
  user: number
  billing_notes: string | null
  user_detail?: { first_name?: string; last_name?: string; telegram_username?: string; email?: string; phone?: string }
}

type Mode = 'view' | 'create' | 'edit'

const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)
const formError = ref<string | null>(null)
const rows = ref<Parent[]>([])
const selectedId = ref<number | null>(null)
const detail = ref<Parent | null>(null)
const mode = ref<Mode>('view')
const route = useRoute()
const router = useRouter()
const isCreateRoute = computed(() => route.name === 'parents-create')
const DETAIL_QUERY_KEY = 'parent'
const LIST_ROUTE_NAME = 'parents'

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

const billing_notes = ref('')

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
    render: (r: Parent) => {
      const u = r.user_detail
      if (!u) return '-'
      return `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.telegram_username || '-'
    },
  },
  { key: 'telegram', label: 'Telegram', render: (r: Parent) => r.user_detail?.telegram_username || '-' },
  { key: 'billing_notes', label: 'Нотатки', render: (r: Parent) => r.billing_notes || '-' },
]

async function reload() {
  loading.value = true
  error.value = null
  try {
    rows.value = await apiRequest<Parent[]>('/api/users/parents/')
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
    detail.value = await apiRequest<Parent>(`/api/users/parents/${id}/`)
    billing_notes.value = detail.value?.billing_notes || ''
  } catch (e: any) {
    formError.value = e?.payload?.detail || e?.message || 'Не вдалося завантажити деталі'
  }
}

async function openDetail(id: number) {
  if (await pushDetailRoute(router, route, DETAIL_QUERY_KEY, id)) return
  await loadDetail(id)
}

function startCreate() {
  router.push({ name: 'parents-create' })
}

function resetCreateForm() {
  mode.value = 'create'
  selectedId.value = null
  detail.value = null
  formError.value = null
  createUser.value = { first_name: '', last_name: '', telegram_username: '', email: '', phone: '', password: '' }
  billing_notes.value = ''
}

function startEdit() {
  if (!selectedId.value || !detail.value) return
  mode.value = 'edit'
  formError.value = null
}

function cancelEdit() {
  if (isCreateRoute.value) {
    router.push({ name: 'parents' })
    return
  }
  mode.value = 'view'
  formError.value = null
  if (detail.value) billing_notes.value = detail.value.billing_notes || ''
}

function clearEditorState() {
  selectedId.value = null
  detail.value = null
  mode.value = 'view'
  formError.value = null
  createUser.value = { first_name: '', last_name: '', telegram_username: '', email: '', phone: '', password: '' }
  billing_notes.value = ''
}

function closeEditor() {
  if (isCreateRoute.value) {
    router.push({ name: LIST_ROUTE_NAME })
  }
  clearEditorState()
}

async function closeEditorAndRoute() {
  clearEditorState()
  if (!isCreateRoute.value) {
    await replaceWithoutDetailRoute(router, route, LIST_ROUTE_NAME, DETAIL_QUERY_KEY)
  }
}

function openDetailFromRoute() {
  if (isCreateRoute.value) return

  const id = routeQueryId(route, DETAIL_QUERY_KEY)
  if (id) {
    void loadDetail(id)
    return
  }

  if (selectedId.value) {
    clearEditorState()
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
          role: 'parent',
          phone: createUser.value.phone || undefined,
        },
      })
      await reload()
      const parent = rows.value.find((p) => p.user === createdUser.id)
      if (parent) {
        await apiRequest(`/api/users/parents/${parent.id}/`, { method: 'PATCH', body: { billing_notes: billing_notes.value } })
      }
      await reload()
      closeEditor()
      return
    }

    if (mode.value === 'edit' && selectedId.value) {
      await updateSelectedUserAccount()
      await apiRequest(`/api/users/parents/${selectedId.value}/`, { method: 'PATCH', body: { billing_notes: billing_notes.value } })
      await reload()
      await closeEditorAndRoute()
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
    await apiRequest(`/api/users/parents/${id}/`, { method: 'DELETE' })
    await reload()
    await closeEditorAndRoute()
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
  void reload().then(openDetailFromRoute)
})

watch(
  () => route.name,
  (name) => {
    if (name === 'parents-create') {
      resetCreateForm()
      loading.value = false
    } else if (mode.value === 'create') {
      closeEditor()
      void reload()
    } else {
      openDetailFromRoute()
    }
  },
)

watch(
  () => route.query[DETAIL_QUERY_KEY],
  () => openDetailFromRoute(),
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
  .mobile-hidden-when-detail {
    display: none;
  }
  .detail-panel--active {
    min-height: calc(100vh - 96px);
  }
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
    position: sticky;
    top: 0;
    z-index: 2;
    padding-bottom: 10px;
    background: var(--surface);
    flex-direction: column;
    align-items: stretch;
  }
  .formwrap__title {
    font-size: 18px;
  }
  .formwrap {
    gap: 14px;
  }
  .input {
    min-height: 42px;
  }
  .ta {
    min-height: 140px;
  }
}
@media (max-width: 420px) {
  .actions,
  .formwrap__actions {
    grid-template-columns: 1fr;
  }
}
</style>
