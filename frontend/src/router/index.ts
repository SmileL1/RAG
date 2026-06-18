import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import AppLayout from '@/components/layout/AppLayout.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: AppLayout,
    children: [
      {
        path: '',
        name: 'chat',
        component: () => import('@/pages/Chat.vue'),
        meta: { title: '对话', fullBleed: true },
      },
      {
        path: 'knowledge',
        name: 'knowledge',
        component: () => import('@/pages/Knowledge.vue'),
        meta: { title: '知识库' },
      },
      {
        path: 'knowledge/:id',
        name: 'kb-documents',
        component: () => import('@/pages/KbDocuments.vue'),
        meta: { title: '文档列表' },
      },
      {
        path: 'knowledge/:id/upload',
        name: 'upload',
        component: () => import('@/pages/Upload.vue'),
        meta: { title: '上传文档' },
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('@/pages/Settings.vue'),
        meta: { title: '设置' },
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('@/pages/Users.vue'),
        meta: { title: '用户管理', adminOnly: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta?.public) return true

  const token = localStorage.getItem('rag_token')
  if (!token) return { name: 'login' }

  // admin 专属页面：非 admin 跳首页
  if (to.meta?.adminOnly) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
      if (!payload.is_admin) return { name: 'chat' }
    } catch {
      return { name: 'chat' }
    }
  }

  return true
})

router.afterEach((to) => {
  const baseTitle = 'RAG · AI 第二大脑'
  const subTitle = (to.meta?.title as string | undefined) ?? ''
  document.title = subTitle ? `${subTitle} - ${baseTitle}` : baseTitle
})

export default router
