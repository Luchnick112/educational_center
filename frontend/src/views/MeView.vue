<template>
  <AppShell title="Профіль">
    <div class="panel">
      <div class="row">
        <div class="panel__title">Акаунт</div>
        <div class="actions">
          <button v-if="!editing" class="btn btn--ghost" type="button" @click="startEdit">Редагувати</button>
          <button v-if="editing" class="btn btn--ghost" type="button" :disabled="saving" @click="cancelEdit">Скасувати</button>
          <button v-if="editing" class="btn" type="button" :disabled="saving" @click="saveProfile">
            {{ saving ? 'Збереження...' : 'Зберегти' }}
          </button>
        </div>
      </div>

      <div v-if="formError" class="error">{{ formError }}</div>

      <form v-if="editing" class="formgrid" @submit.prevent="saveProfile">
        <label class="field">
          <span class="field__label">Ім'я</span>
          <input v-model.trim="form.first_name" class="input" autocomplete="given-name" />
        </label>
        <label class="field">
          <span class="field__label">Прізвище</span>
          <input v-model.trim="form.last_name" class="input" autocomplete="family-name" />
        </label>
        <label class="field">
          <span class="field__label">Telegram username</span>
          <input v-model.trim="form.telegram_username" class="input" autocomplete="username" placeholder="@username" />
        </label>
        <label class="field">
          <span class="field__label">Email</span>
          <input v-model.trim="form.email" class="input" type="email" autocomplete="email" />
        </label>
        <label class="field">
          <span class="field__label">Телефон</span>
          <input v-model.trim="form.phone" class="input" autocomplete="tel" placeholder="+380501112233" />
        </label>
      </form>

      <div v-else class="kv">
        <div class="kv__k">Ім'я</div>
        <div class="kv__v">{{ auth.displayName }}</div>
        <div class="kv__k">Роль</div>
        <div class="kv__v">{{ auth.me?.role }}</div>
        <div class="kv__k">Telegram</div>
        <div class="kv__v">{{ auth.me?.telegram_username || '-' }}</div>
        <div class="kv__k">Email</div>
        <div class="kv__v">{{ auth.me?.email || '-' }}</div>
        <div class="kv__k">Телефон</div>
        <div class="kv__v">{{ auth.me?.phone || '-' }}</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel__title">Статистика</div>
      <div v-if="loading" class="muted">Завантаження...</div>
      <div v-else class="cards">
        <div v-for="(value, key) in stats" :key="key" class="card">
          <div class="card__k">{{ key }}</div>
          <div class="card__v">{{ value }}</div>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import AppShell from '@/components/AppShell.vue'
import { useAuthStore } from '@/stores/auth'
import { apiRequest } from '@/lib/api'

const auth = useAuthStore()
const loading = ref(true)
const saving = ref(false)
const editing = ref(false)
const formError = ref<string | null>(null)
const stats = ref<Record<string, number>>({})
const form = reactive({
  first_name: '',
  last_name: '',
  telegram_username: '',
  email: '',
  phone: '',
})

type DashboardResponse = { user: unknown; role: string; stats: Record<string, number> }

function syncForm() {
  form.first_name = auth.me?.first_name || ''
  form.last_name = auth.me?.last_name || ''
  form.telegram_username = auth.me?.telegram_username || ''
  form.email = auth.me?.email || ''
  form.phone = auth.me?.phone || ''
}

function startEdit() {
  syncForm()
  formError.value = null
  editing.value = true
}

function cancelEdit() {
  syncForm()
  formError.value = null
  editing.value = false
}

async function saveProfile() {
  saving.value = true
  formError.value = null
  try {
    await apiRequest('/api/users/me/', {
      method: 'PATCH',
      body: {
        first_name: form.first_name,
        last_name: form.last_name,
        telegram_username: form.telegram_username || null,
        email: form.email || '',
        phone: form.phone || '',
      },
    })
    await auth.refreshMe()
    syncForm()
    editing.value = false
  } catch (e: any) {
    formError.value = e?.payload ? JSON.stringify(e.payload) : e?.message || 'Не вдалося зберегти'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    syncForm()
    const res = await apiRequest<DashboardResponse>('/api/users/dashboard/')
    stats.value = res.stats ?? {}
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.formgrid {
  display: grid;
  gap: 12px;
}
.field {
  display: grid;
  gap: 6px;
}
.field__label {
  font-size: 12px;
  color: var(--muted);
}
</style>
