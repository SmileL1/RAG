<script setup lang="ts">
// 占位页：后续实装 模型/Embedding 切换、API Key 配置
</script>

<template>
  <div class="settings-page">
    <h2 class="title">设置</h2>
    <div class="grid">
      <section class="glass-card">
        <div class="section-icon">
          <Icon icon="ph:robot-duotone" />
        </div>
        <h3>LLM 模型</h3>
        <p class="desc">当前：<code>deepseek-chat</code></p>
        <p class="hint">可切换：DeepSeek / OpenAI / 通义千问 / Kimi</p>
      </section>
      <section class="glass-card">
        <div class="section-icon">
          <Icon icon="ph:cpu-duotone" />
        </div>
        <h3>Embedding</h3>
        <p class="desc">当前：<code>dashscope:text-embedding-v3</code></p>
        <p class="hint">本地 bge-m3 / 阿里云 DashScope，可在 .env 切换</p>
      </section>
      <section class="glass-card">
        <div class="section-icon">
          <Icon icon="ph:funnel-duotone" />
        </div>
        <h3>检索 & Rerank</h3>
        <p class="desc">召回 Top-20 → Rerank Top-5</p>
        <p class="hint">Reranker: bge-reranker-v2-m3（本地运行）</p>
      </section>
      <section class="glass-card">
        <div class="section-icon">
          <Icon icon="ph:database-duotone" />
        </div>
        <h3>向量数据库</h3>
        <p class="desc">当前：<code>Qdrant（本地模式）</code></p>
        <p class="hint">数据存储于 ./data/qdrant，重启不丢失</p>
      </section>
    </div>
  </div>
</template>

<script lang="ts">
import { Icon } from '@iconify/vue'
export default { components: { Icon } }
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 18px;
}
section {
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.section-icon {
  font-size: 28px;
  color: #2563EB;
  margin-bottom: 4px;
}
section h3 {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}
.desc {
  font-size: 13px;
  color: var(--text-secondary);
}
.desc code {
  background: rgba(37, 99, 235, 0.08);
  color: #2563EB;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 12px;
}
.hint {
  font-size: 12px;
  color: var(--text-muted);
}
</style>
