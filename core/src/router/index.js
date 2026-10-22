import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      meta: { public: true },
      component: () => import('../views/LoginView.vue')
    },
    {
      path: '/register',
      name: 'register',
      meta: { public: true },
      component: () => import('../views/RegisterView.vue')
    },
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue')
    },
    {
      path: '/project/:slug',
      name: 'project',
      component: () => import('../views/ProjectView.vue')
    },
    {
      path: '/project/:slug/settings',
      name: 'project-settings',
      component: () => import('../views/ProjectSettings.vue')
    },
    {
      path: '/folder/:id',
      name: 'folder',
      component: () => import('../views/FolderView.vue')
    },
    {
      // Публичный просмотр по ссылке — без входа (AUTH_PLAN).
      path: '/p/:slug',
      name: 'presentation',
      meta: { public: true },
      component: () => import('../views/MainPresentation.vue')
    },
    {
      path: '/account',
      name: 'account',
      component: () => import('../views/AccountView.vue')
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('../views/AdminUsersView.vue')
    },
    {
      path: '/themes',
      name: 'themes',
      component: () => import('../views/ThemesView.vue')
    },
    {
      // Демо UI-кита (UX_REDESIGN Ф0) — dev-витрина примитивов
      path: '/kit',
      name: 'kit',
      component: () => import('../views/KitView.vue')
    }
  ]
})

// Guard: при AUTH_MODE=on закрытые разделы требуют входа; публичные (/p/:slug, /login, /register) — нет.
router.beforeEach(async (to) => {
  const { useAuth } = await import('../composables/useAuth')
  const { authMode, currentUser, ensureLoaded } = useAuth()
  await ensureLoaded()
  if (to.meta?.public) return true
  if (authMode.value === 'on' && !currentUser.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
