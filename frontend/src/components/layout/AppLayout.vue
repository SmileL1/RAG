<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './Sidebar.vue'

const route = useRoute()
const fullBleed = computed(() => Boolean(route.meta?.fullBleed))
</script>

<template>
  <div class="layout">
    <Sidebar />
    <main class="main">
      <div class="content" :class="{ bleed: fullBleed }">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-primary);
}
.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.content {
  flex: 1;
  min-height: 0;
}
/* 普通页：带边距、可滚动 */
.content:not(.bleed) {
  overflow: auto;
  padding: 28px 32px;
}
/* 对话页：全屏铺满，内部自行滚动 */
.content.bleed {
  overflow: hidden;
}
</style>
