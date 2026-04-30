<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'
import type { Citation } from '@/api/types'

defineProps<{ citations: Citation[] }>()
const open = ref(false)

function scoreDisplay(score: number | null): string {
  if (score === null || score === undefined) return ''
  const pct = score * 100
  if (pct < 0.1) return '< 0.1%'
  if (pct < 1) return pct.toFixed(1) + '%'
  return pct.toFixed(0) + '%'
}
</script>

<template>
  <div v-if="citations.length" class="citations glass-card">
    <button class="head" @click="open = !open">
      <Icon icon="ph:quotes-duotone" />
      <span class="label">来源 · {{ citations.length }} 条</span>
      <Icon
        :icon="open ? 'ph:caret-up-bold' : 'ph:caret-down-bold'"
        class="caret"
      />
    </button>

    <div v-if="open" class="body">
      <div v-for="(c, i) in citations" :key="i" class="cite-item">
        <div class="num text-gradient">[{{ i + 1 }}]</div>
        <div class="cite-content">
          <div class="loc">
            📄 {{ c.filename }}
            <span v-if="c.page" class="page">· 第 {{ c.page }} 页</span>
            <span v-if="c.score != null" class="score">
              · 相关度 {{ scoreDisplay(c.score) }}
            </span>
          </div>
          <div class="text">{{ c.text }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.citations {
  margin-top: 10px;
  padding: 0;
  background: rgba(0, 212, 255, 0.04);
  border-color: rgba(0, 212, 255, 0.18);
}
.head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  width: 100%;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 12px;
}
.head:hover {
  color: var(--text-primary);
}
.label {
  flex: 1;
  text-align: left;
  font-weight: 600;
}
.caret {
  font-size: 14px;
}

.body {
  padding: 4px 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-top: 1px dashed var(--border-subtle);
  margin-top: 0;
  padding-top: 14px;
}
.cite-item {
  display: flex;
  gap: 10px;
  font-size: 12px;
}
.num {
  font-weight: 800;
  flex-shrink: 0;
  width: 22px;
}
.cite-content {
  flex: 1;
  min-width: 0;
}
.loc {
  color: var(--text-secondary);
  margin-bottom: 4px;
  font-size: 11px;
}
.page,
.score {
  margin-left: 4px;
}
.text {
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.03);
  padding: 8px 10px;
  border-radius: 6px;
  border-left: 2px solid var(--color-info);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
