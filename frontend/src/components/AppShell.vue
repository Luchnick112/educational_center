<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand__title">Educational Center</div>
        <div class="brand__sub">{{ auth.me?.role ?? '...' }}</div>
      </div>

      <nav class="nav">
        <RouterLink class="nav__link" to="/me">Профіль</RouterLink>
        <RouterLink class="nav__link" to="/">Панель</RouterLink>

        <div class="nav__section">Моє</div>
        <RouterLink class="nav__link" to="/my/lessons">Уроки</RouterLink>
        <RouterLink class="nav__link" to="/my/groups">Групи</RouterLink>
        <RouterLink class="nav__link" to="/my/confirmations">Підтвердження</RouterLink>
        <RouterLink class="nav__link" to="/my/payments">Платежі</RouterLink>

        <template v-if="isAdmin">
          <div class="nav__section">Користувачі</div>
          <RouterLink class="nav__link" to="/users/students">Учні</RouterLink>
          <RouterLink class="nav__link" to="/users/parents">Батьки</RouterLink>
          <RouterLink class="nav__link" to="/users/teachers">Вчителі</RouterLink>
        </template>

        <template v-if="isStaffish">
          <div class="nav__section">Навчання</div>
          <RouterLink class="nav__link" to="/academics">Огляд</RouterLink>
        </template>
      </nav>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="topbar__left">
          <button class="btn btn--ghost mobile-menu-button" type="button" @click="mobileNavOpen = !mobileNavOpen">
            Меню
          </button>
          <div class="topbar__title">{{ title }}</div>
        </div>
        <div class="topbar__right">
          <div class="user">
            <div class="user__name">{{ auth.displayName }}</div>
            <button class="btn btn--ghost" type="button" @click="onLogout">Вийти</button>
          </div>
        </div>
      </header>
      <nav v-if="mobileNavOpen" class="mobile-nav">
        <RouterLink class="nav__link" to="/me" @click="closeMobileNav">Профіль</RouterLink>
        <RouterLink class="nav__link" to="/" @click="closeMobileNav">Панель</RouterLink>

        <div class="nav__section">Моє</div>
        <RouterLink class="nav__link" to="/my/lessons" @click="closeMobileNav">Уроки</RouterLink>
        <RouterLink class="nav__link" to="/my/groups" @click="closeMobileNav">Групи</RouterLink>
        <RouterLink class="nav__link" to="/my/confirmations" @click="closeMobileNav">Підтвердження</RouterLink>
        <RouterLink class="nav__link" to="/my/payments" @click="closeMobileNav">Платежі</RouterLink>

        <template v-if="isAdmin">
          <div class="nav__section">Користувачі</div>
          <RouterLink class="nav__link" to="/users/students" @click="closeMobileNav">Учні</RouterLink>
          <RouterLink class="nav__link" to="/users/parents" @click="closeMobileNav">Батьки</RouterLink>
          <RouterLink class="nav__link" to="/users/teachers" @click="closeMobileNav">Вчителі</RouterLink>
        </template>

        <template v-if="isStaffish">
          <div class="nav__section">Навчання</div>
          <RouterLink class="nav__link" to="/academics" @click="closeMobileNav">Огляд</RouterLink>
        </template>
      </nav>
      <main class="content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

defineProps<{ title: string }>()

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const mobileNavOpen = ref(false)

const isStaffish = computed(() => !!auth.me && (auth.me.is_staff || auth.me.role === 'admin'))
const isAdmin = computed(() => !!auth.me && (auth.me.is_staff || auth.me.role === 'admin'))

function closeMobileNav() {
  mobileNavOpen.value = false
}

function onLogout() {
  auth.logOut()
  closeMobileNav()
  router.push({ name: 'login' })
}

watch(
  () => route.fullPath,
  () => closeMobileNav(),
)
</script>
