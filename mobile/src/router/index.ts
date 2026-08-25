import { createRouter, createWebHistory } from '@ionic/vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/app/lessons' },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginPage.vue'),
  },
  {
    path: '/app',
    component: () => import('@/views/TabsPage.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/app/lessons' },
      { path: 'lessons', name: 'lessons', component: () => import('@/views/LessonsPage.vue') },
      { path: 'groups', name: 'groups', component: () => import('@/views/GroupsPage.vue') },
      { path: 'children', name: 'children', component: () => import('@/views/ChildrenPage.vue') },
      { path: 'payments', name: 'payments', component: () => import('@/views/PaymentsPage.vue') },
      { path: 'profile', name: 'profile', component: () => import('@/views/ProfilePage.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/app/lessons' },
]

const router = createRouter({ history: createWebHistory(import.meta.env.BASE_URL), routes })

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.bootstrap()
  if (to.matched.some((route) => route.meta.requiresAuth) && !auth.isAuthenticated) return { name: 'login' }
  if (to.name === 'login' && auth.isAuthenticated) return { name: 'lessons' }
})

export default router
