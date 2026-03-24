import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/tasks' },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('@/views/TaskList.vue'),
      },
      {
        path: 'tasks/create',
        name: 'TaskCreate',
        component: () => import('@/views/TaskCreate.vue'),
      },
      {
        path: 'tasks/:id',
        name: 'TaskDetail',
        component: () => import('@/views/TaskDetail.vue'),
      },
      {
        path: 'presets',
        name: 'Presets',
        component: () => import('@/views/PresetList.vue'),
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
      },
    ]
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        redirect: '/admin/dashboard'
      },
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue')
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UserManagement.vue')
      },
      {
        path: 'tasks',
        name: 'AdminTasks',
        component: () => import('@/views/admin/TaskMonitor.vue')
      },
      {
        path: 'presets',
        name: 'AdminPresets',
        component: () => import('@/views/PresetList.vue'),
        meta: { adminView: true }
      },
      {
        path: 'groups',
        name: 'AdminGroups',
        component: () => import('@/views/admin/GroupManagement.vue')
      }
    ]
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // 等待 session 恢复完成
  await authStore.restoreSession()

  // 检查是否需要认证
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // 已登录用户访问登录页，重定向到任务页
  if (to.name === 'Login' && authStore.isAuthenticated) {
    next({ name: 'Tasks' })
    return
  }

  // 检查是否需要管理员权限
  if (to.meta.requiresAdmin && !authStore.user?.is_admin) {
    next({ name: 'Tasks' })
    return
  }

  next()
})

export default router
