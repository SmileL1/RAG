<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

interface NavItem {
  key: string
  to: string
  label: string
  icon: 'chat' | 'kb' | 'gear' | 'users'
}

const items = computed<NavItem[]>(() => {
  const base: NavItem[] = [
    { key: 'chat', to: '/', label: '对话', icon: 'chat' },
    { key: 'knowledge', to: '/knowledge', label: '知识库', icon: 'kb' },
    { key: 'settings', to: '/settings', label: '设置', icon: 'gear' },
  ]
  if (authStore.isAdmin) base.push({ key: 'users', to: '/users', label: '用户', icon: 'users' })
  return base
})

const activeKey = computed(() => {
  if (route.path.startsWith('/knowledge')) return 'knowledge'
  if (route.path.startsWith('/settings')) return 'settings'
  if (route.path.startsWith('/users')) return 'users'
  return 'chat'
})

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <nav class="railnav">
    <div class="brand-mark" title="知识库">
      <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9.5 3.5A2.5 2.5 0 0 0 7 6v.2A2.8 2.8 0 0 0 5 9a2.8 2.8 0 0 0 .7 1.85A2.9 2.9 0 0 0 5 13a2.8 2.8 0 0 0 2 2.68V16a2.5 2.5 0 0 0 2.5 2.5"/>
        <path d="M14.5 3.5A2.5 2.5 0 0 1 17 6v.2A2.8 2.8 0 0 1 19 9a2.8 2.8 0 0 1-.7 1.85A2.9 2.9 0 0 1 19 13a2.8 2.8 0 0 1-2 2.68V16a2.5 2.5 0 0 1-2.5 2.5"/>
        <path d="M12 3.5v15"/>
      </svg>
    </div>

    <div class="rail-items">
      <RouterLink
        v-for="it in items"
        :key="it.key"
        :to="it.to"
        class="rail-btn"
        :class="{ active: activeKey === it.key }"
        :title="it.label"
      >
        <span class="rail-stack">
          <svg v-if="it.icon === 'chat'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-8.5 8.5 9 9 0 0 1-4-.9L3 20l1.9-5a8.38 8.38 0 0 1-.9-4A8.5 8.5 0 0 1 12.5 3 8.38 8.38 0 0 1 21 11.5Z"/></svg>
          <svg v-else-if="it.icon === 'kb'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/></svg>
          <svg v-else-if="it.icon === 'gear'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"/></svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          <span class="rail-label">{{ it.label }}</span>
        </span>
      </RouterLink>
    </div>

    <div class="rail-spacer" />
    <div class="rail-foot">
      <a class="rail-btn sm" href="http://localhost:8000/docs" target="_blank" title="API 文档">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
      </a>
      <button class="rail-btn sm" title="退出登录" @click="logout">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
      </button>
    </div>
  </nav>
</template>

<style scoped>
.railnav {
  width: 76px;
  flex-shrink: 0;
  height: 100%;
  background: var(--bg-card);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 18px 0 16px;
}
.brand-mark {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: var(--brand-gradient);
  display: grid;
  place-items: center;
  box-shadow: 0 4px 14px rgba(91, 79, 232, 0.4);
}
.brand-mark svg { width: 24px; height: 24px; }

.rail-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 22px;
  width: 100%;
  align-items: center;
}
.rail-btn {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  position: relative;
  color: var(--text-muted);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  text-decoration: none;
  border: none;
  background: transparent;
}
.rail-btn svg { width: 21px; height: 21px; }
.rail-btn:hover { background: var(--bg-secondary); color: var(--text-secondary); }
.rail-btn.active { background: var(--accent-soft); color: var(--accent); }
.rail-btn.active::before {
  content: '';
  position: absolute;
  left: -15px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  border-radius: 0 3px 3px 0;
  background: var(--accent);
}
.rail-stack { display: flex; flex-direction: column; align-items: center; gap: 3px; }
.rail-label {
  font-family: var(--font-display);
  font-size: 9.5px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.rail-spacer { flex: 1; }
.rail-foot { display: flex; flex-direction: column; gap: 4px; align-items: center; }
.rail-foot .rail-btn.sm { width: 42px; height: 42px; }
.rail-foot .rail-btn:hover { color: var(--text-primary); }
</style>
