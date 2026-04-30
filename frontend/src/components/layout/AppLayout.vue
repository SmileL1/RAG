<script setup lang="ts">
import Sidebar from './Sidebar.vue'
import TopBar from './TopBar.vue'
import GlowOrb from '@/components/common/GlowOrb.vue'
</script>

<template>
  <div class="layout">
    <!-- 背景柔光 -->
    <GlowOrb color="purple" :size="500" top="-200px" left="-200px" :opacity="0.3" />
    <GlowOrb color="cyan" :size="600" bottom="-300px" right="-200px" :opacity="0.25" />

    <div class="layout-inner">
      <Sidebar />
      <main class="main">
        <TopBar />
        <div class="content">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
.layout-inner {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  display: flex;
  padding: 14px;
  gap: 14px;
}
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-subtle);
  backdrop-filter: blur(8px);
  overflow: hidden;
}
.content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}
</style>
