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
            <div class="notifications">
              <button
                class="notification-button"
                type="button"
                :class="{ 'notification-button--active': unreadCount > 0 }"
                @click="notificationsOpen = !notificationsOpen"
                aria-label="Повідомлення"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true" class="notification-button__icon">
                  <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
                  <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                </svg>
                <span v-if="unreadCount > 0" class="notification-button__badge">{{ unreadCount }}</span>
              </button>
              <div v-if="notificationsOpen" class="notifications-menu">
                <div class="notifications-menu__title">Повідомлення</div>
                <div v-if="notificationsLoading" class="notifications-menu__empty">Завантаження...</div>
                <div v-else-if="notifications.length === 0" class="notifications-menu__empty">Немає нових повідомлень</div>
                <template v-else>
                  <RouterLink
                    v-for="item in notifications"
                    :key="item.id"
                    class="notification-item"
                    :class="{ 'notification-item--read': isNotificationRead(item.id) }"
                    :to="item.url"
                    @click="markNotificationRead(item)"
                  >
                    <span class="notification-item__title">{{ item.title }}</span>
                    <span class="notification-item__message">{{ item.message }}</span>
                  </RouterLink>
                </template>
              </div>
            </div>
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
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { apiRequest } from '@/lib/api'

defineProps<{ title: string }>()

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const mobileNavOpen = ref(false)
const notificationsOpen = ref(false)
const notificationsLoading = ref(false)
const notifications = ref<NotificationItem[]>([])
const readNotificationIds = ref<Set<string>>(new Set())
let notificationsTimer: number | undefined

type NotificationItem = {
  id: string
  kind: string
  title: string
  message: string
  url: string
  created_at?: string | null
}

const isStaffish = computed(() => !!auth.me && (auth.me.is_staff || auth.me.role === 'admin'))
const isAdmin = computed(() => !!auth.me && (auth.me.is_staff || auth.me.role === 'admin'))
const notificationStorageKey = computed(() => (auth.me ? `notifications:read:${auth.me.id}` : 'notifications:read:anonymous'))
const unreadCount = computed(() => notifications.value.filter((item) => !isNotificationRead(item.id)).length)

function loadReadNotifications() {
  try {
    const raw = localStorage.getItem(notificationStorageKey.value)
    const ids = raw ? JSON.parse(raw) : []
    readNotificationIds.value = new Set(Array.isArray(ids) ? ids.filter((id) => typeof id === 'string') : [])
  } catch {
    readNotificationIds.value = new Set()
  }
}

function saveReadNotifications() {
  localStorage.setItem(notificationStorageKey.value, JSON.stringify([...readNotificationIds.value]))
}

function isNotificationRead(id: string) {
  return readNotificationIds.value.has(id)
}

function markNotificationRead(item: NotificationItem) {
  readNotificationIds.value = new Set(readNotificationIds.value).add(item.id)
  saveReadNotifications()
  notificationsOpen.value = false
}

async function loadNotifications() {
  if (!auth.isAuthed) return
  notificationsLoading.value = true
  try {
    loadReadNotifications()
    notifications.value = await apiRequest<NotificationItem[]>('/api/my/notifications/')
  } catch {
    notifications.value = []
  } finally {
    notificationsLoading.value = false
  }
}

function closeMobileNav() {
  mobileNavOpen.value = false
}

function onLogout() {
  auth.logOut()
  closeMobileNav()
  notifications.value = []
  readNotificationIds.value = new Set()
  notificationsOpen.value = false
  router.push({ name: 'login' })
}

watch(
  () => route.fullPath,
  () => {
    closeMobileNav()
    notificationsOpen.value = false
    void loadNotifications()
  },
)

onMounted(() => {
  void loadNotifications()
  notificationsTimer = window.setInterval(() => void loadNotifications(), 60000)
})

onUnmounted(() => {
  if (notificationsTimer !== undefined) window.clearInterval(notificationsTimer)
})
</script>

<style scoped>
.notifications {
  position: relative;
}
.notification-button {
  position: relative;
  display: inline-grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.06);
  color: #e8eefc;
  cursor: pointer;
}
.notification-button--active {
  border-color: rgba(255, 199, 95, 0.85);
  background: rgba(255, 199, 95, 0.16);
}
.notification-button__icon {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.notification-button__badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: #ffbf47;
  color: #101828;
  font-size: 11px;
  font-weight: 800;
  line-height: 18px;
}
.notifications-menu {
  position: absolute;
  z-index: 40;
  top: calc(100% + 8px);
  right: 0;
  width: min(360px, calc(100vw - 24px));
  max-height: 420px;
  overflow: auto;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: #0f1629;
  box-shadow: 0 18px 44px rgba(0, 0, 0, 0.35);
  padding: 8px;
}
.notifications-menu__title {
  padding: 7px 8px 9px;
  font-size: 12px;
  font-weight: 750;
  color: rgba(232, 238, 252, 0.72);
}
.notifications-menu__empty {
  padding: 10px 8px;
  color: rgba(232, 238, 252, 0.6);
  font-size: 13px;
}
.notification-item {
  display: grid;
  gap: 4px;
  padding: 10px 8px;
  border-radius: 6px;
  text-decoration: none;
}
.notification-item:hover {
  background: rgba(93, 120, 255, 0.1);
}
.notification-item--read {
  opacity: 0.55;
}
.notification-item--read .notification-item__title,
.notification-item--read .notification-item__message {
  color: rgba(232, 238, 252, 0.46);
}
.notification-item__title {
  font-size: 13px;
  font-weight: 750;
}
.notification-item__message {
  color: rgba(232, 238, 252, 0.68);
  font-size: 12px;
  line-height: 1.35;
}
@media (max-width: 560px) {
  .notifications-menu {
    right: -92px;
  }
}
</style>
