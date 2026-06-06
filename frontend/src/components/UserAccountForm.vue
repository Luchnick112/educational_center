<template>
  <div class="ua">
    <div class="ua__title">{{ title }}</div>

    <div class="formgrid">
      <div class="field">
        <div class="field__label">Ім'я</div>
        <input class="input" v-model.trim="model.first_name" :disabled="disabled" />
      </div>
      <div class="field">
        <div class="field__label">Прізвище</div>
        <input class="input" v-model.trim="model.last_name" :disabled="disabled" />
      </div>
      <div class="field">
        <div class="field__label">Telegram username</div>
        <input class="input" v-model.trim="model.telegram_username" placeholder="@username" :disabled="disabled || lockTelegram" />
      </div>
      <div class="field">
        <div class="field__label">Email</div>
        <input class="input" v-model.trim="model.email" :disabled="disabled" />
      </div>
      <div class="field">
        <div class="field__label">Телефон</div>
        <input class="input" v-model.trim="model.phone" :disabled="disabled" />
      </div>
      <div v-if="showPassword" class="field">
        <div class="field__label">Пароль</div>
        <input class="input" type="password" v-model="model.password" autocomplete="new-password" :disabled="disabled" />
      </div>
    </div>

    <div v-if="hint" class="muted">{{ hint }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  model: {
    first_name: string
    last_name: string
    telegram_username: string
    email?: string
    phone?: string
    password?: string
  }
  disabled?: boolean
  showPassword?: boolean
  lockTelegram?: boolean
  hint?: string
}>()
</script>

<style scoped>
.ua {
  display: grid;
  gap: 10px;
}
.ua__title {
  font-weight: 650;
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
