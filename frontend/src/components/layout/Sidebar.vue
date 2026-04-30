<script setup lang="ts">
import { computed, h } from 'vue'
import { NIcon, NMenu, type MenuOption } from 'naive-ui'
import { Icon } from '@iconify/vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const renderIcon = (icon: string) => () => h(NIcon, null, () => h(Icon, { icon }))

const menuOptions = computed<MenuOption[]>(() => {
  const base: MenuOption[] = [
    {
      label: () => h(RouterLink, { to: '/' }, () => '对话'),
      key: 'chat',
      icon: renderIcon('ph:chat-circle-dots-duotone'),
    },
    {
      label: () => h(RouterLink, { to: '/knowledge' }, () => '知识库'),
      key: 'knowledge',
      icon: renderIcon('ph:database-duotone'),
    },
    {
      label: () => h(RouterLink, { to: '/settings' }, () => '设置'),
      key: 'settings',
      icon: renderIcon('ph:gear-six-duotone'),
    },
  ]
  if (authStore.isAdmin) {
    base.push({
      label: () => h(RouterLink, { to: '/users' }, () => '用户管理'),
      key: 'users',
      icon: renderIcon('ph:users-three-duotone'),
    })
  }
  return base
})

const activeKey = computed(() => {
  if (route.path.startsWith('/knowledge')) return 'knowledge'
  if (route.path.startsWith('/settings')) return 'settings'
  if (route.path.startsWith('/users')) return 'users'
  return 'chat'
})
</script>

<template>
  <aside class="sidebar glass-card">
    <div class="logo">
      <div class="logo-icon brand-gradient">
        <Icon icon="ph:brain-duotone" />
      </div>
      <div class="logo-text">
        <div class="title text-gradient">知识库</div>
        <div class="subtitle">私有 AI 问答</div>
      </div>
    </div>

    <NMenu
      :value="activeKey"
      :options="menuOptions"
      :collapsed-width="64"
      :indent="18"
      class="menu"
    />
  </aside>
</template>

<style scoped>
.sidebar {
  width: 240px;
  height: 100%;
  padding: 20px 14px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 6px 14px;
  border-bottom: 1px solid var(--border-subtle);
}
.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-size: 20px;
  color: #fff;
  box-shadow: var(--shadow-neon);
  flex-shrink: 0;
}
.logo-text .title {
  font-size: 17px;
  font-weight: 800;
  letter-spacing: 0.3px;
}
.logo-text .subtitle {
  font-size: 11px;
  color: var(--text-muted);
}

.menu {
  flex: 1;
  background: transparent;
}
</style>
