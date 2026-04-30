<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const title = computed(() => (route.meta?.title as string | undefined) ?? '')

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="topbar">
    <div class="title">{{ title }}</div>
    <div class="right">
      <a class="link" href="http://localhost:8000/docs" target="_blank" title="打开 Swagger API 文档">
        <Icon icon="ph:file-code-duotone" />
        <span>API 文档</span>
      </a>
      <button class="link logout-btn" @click="logout" title="退出登录">
        <Icon icon="ph:sign-out-duotone" />
        <span>退出</span>
      </button>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  height: 56px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.70);
  backdrop-filter: blur(12px);
}
.title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}
.right {
  display: flex;
  gap: 8px;
}
.link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 8px;
  transition: background 0.15s, color 0.15s;
  background: transparent;
  border: none;
  cursor: pointer;
}
.link:hover {
  background: rgba(37, 99, 235, 0.08);
  color: #2563EB;
}
.logout-btn:hover {
  background: rgba(239, 68, 68, 0.08);
  color: #EF4444;
}
</style>
