import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue') },
    { path: '/me', name: 'me', component: () => import('@/views/MeView.vue'), meta: { requiresAuth: true } },
    { path: '/', name: 'dashboard', component: () => import('@/views/DashboardView.vue'), meta: { requiresAuth: true } },
    { path: '/my/lessons', name: 'my-lessons', component: () => import('@/views/MyLessonsView.vue'), meta: { requiresAuth: true } },
    { path: '/my/groups', name: 'my-groups', component: () => import('@/views/MyGroupsView.vue'), meta: { requiresAuth: true } },
    { path: '/my/confirmations', name: 'my-confirmations', component: () => import('@/views/MyConfirmationsView.vue'), meta: { requiresAuth: true } },
    { path: '/my/payments', name: 'my-payments', component: () => import('@/views/MyPaymentsView.vue'), meta: { requiresAuth: true } },
    { path: '/my/children', name: 'my-children', component: () => import('@/views/MyChildrenView.vue'), meta: { requiresAuth: true } },

    { path: '/users/students', name: 'students', component: () => import('@/views/StudentsView.vue'), meta: { requiresAuth: true } },
    { path: '/users/parents', name: 'parents', component: () => import('@/views/ParentsView.vue'), meta: { requiresAuth: true } },
    { path: '/users/teachers', name: 'teachers', component: () => import('@/views/TeachersView.vue'), meta: { requiresAuth: true } },

    { path: '/academics', name: 'academics', component: () => import('@/views/AcademicsView.vue'), meta: { requiresAuth: true, requiresStaff: true } },

    // Prevent blank screen on unknown routes.
    { path: '/:pathMatch(.*)*', redirect: '/me' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.bootstrap()

  if (to.meta.requiresAuth && !auth.isAuthed) {
    return { name: 'login', query: { next: to.fullPath } }
  }
  if ((to.name === 'login' || to.name === 'register') && auth.isAuthed) {
    return { name: 'me' }
  }

  if (to.meta.requiresStaff) {
    const me = auth.me
    const allowed = !!me && (me.is_staff || me.role === 'admin')
    if (!allowed) return { name: 'me' }
  }
})

export default router
