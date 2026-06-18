<script setup lang="ts">
import { useRouter } from 'vue-router'
import { NPopconfirm } from 'naive-ui'
import type { KnowledgeBase } from '@/api/types'

const props = defineProps<{ kb: KnowledgeBase; docCount?: number }>()
const emit = defineEmits<{ remove: [id: number]; chat: [id: number] }>()

const router = useRouter()
function goUpload() {
  router.push(`/knowledge/${props.kb.id}/upload`)
}
function goDocs() {
  router.push(`/knowledge/${props.kb.id}`)
}
function formatDate(s: string) {
  return new Date(s).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}
</script>

<template>
  <div class="kb-card">
    <!-- 头部：图标 + 名称 + 统计 + 删除 -->
    <div class="kb-top">
      <div class="kb-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/></svg>
      </div>
      <div class="kb-headtext">
        <div class="kb-name" :title="kb.name">{{ kb.name }}</div>
        <div class="kb-stats">
          <span class="stat">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            {{ docCount ?? 0 }} 文档
          </span>
          <span class="dot">·</span>
          <span class="stat">{{ kb.embedding_dim }} 维</span>
        </div>
      </div>
      <NPopconfirm @positive-click="emit('remove', kb.id)">
        <template #trigger>
          <button class="kb-del" title="删除知识库">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </template>
        删除该知识库及其所有文档/向量？此操作不可逆
      </NPopconfirm>
    </div>

    <!-- 描述 -->
    <div class="kb-desc" :class="{ placeholder: !kb.description }">
      {{ kb.description || '暂无描述' }}
    </div>

    <!-- 模型 + 日期 -->
    <div class="kb-foot">
      <span class="kb-model">{{ kb.embedding_model }}</span>
      <span class="kb-date">{{ formatDate(kb.created_at) }} 创建</span>
    </div>

    <!-- 操作 -->
    <div class="kb-actions">
      <button class="act-primary" @click="emit('chat', kb.id)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-8.5 8.5 9 9 0 0 1-4-.9L3 20l1.9-5a8.38 8.38 0 0 1-.9-4A8.5 8.5 0 0 1 12.5 3 8.38 8.38 0 0 1 21 11.5Z"/></svg>
        进入对话
      </button>
      <button class="act-ghost" title="查看文档" @click="goDocs">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        文档
      </button>
      <button class="act-ghost icon-only" title="上传文档" @click="goUpload">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.kb-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-glass);
  padding: 18px 18px 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  transition: border-color 0.18s, box-shadow 0.18s, transform 0.18s;
}
.kb-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-pop);
  transform: translateY(-2px);
}

.kb-top { display: flex; align-items: center; gap: 12px; }
.kb-icon {
  width: 42px;
  height: 42px;
  border-radius: 11px;
  background: var(--brand-gradient);
  display: grid;
  place-items: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(91, 79, 232, 0.3);
}
.kb-icon svg { width: 22px; height: 22px; }
.kb-headtext { flex: 1; min-width: 0; }
.kb-name {
  font-family: var(--font-display);
  font-size: 15.5px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kb-stats {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 3px;
  font-size: 12px;
  color: var(--text-muted);
}
.kb-stats .stat { display: inline-flex; align-items: center; gap: 4px; }
.kb-stats svg { width: 13px; height: 13px; }
.kb-stats .dot { opacity: 0.5; }
.kb-del {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  display: grid;
  place-items: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s, color 0.15s;
}
.kb-del svg { width: 16px; height: 16px; }
.kb-del:hover { background: #FBEAEA; color: #D14343; }

.kb-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 41.6px;
}
.kb-desc.placeholder { color: var(--text-muted); font-style: italic; }

.kb-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
  color: var(--text-muted);
}
.kb-model {
  background: var(--accent-soft);
  color: var(--accent);
  padding: 3px 9px;
  border-radius: 6px;
  font-family: var(--font-mono);
  font-size: 11px;
  max-width: 70%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kb-date { flex-shrink: 0; }

.kb-actions {
  display: flex;
  gap: 8px;
  border-top: 1px solid var(--border-subtle);
  padding-top: 14px;
}
.act-primary {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 38px;
  border: none;
  border-radius: 9px;
  background: var(--accent);
  color: #fff;
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: var(--shadow-neon);
  transition: background 0.15s, transform 0.15s;
}
.act-primary svg { width: 16px; height: 16px; }
.act-primary:hover { background: var(--accent-hover); transform: translateY(-1px); }

.act-ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 38px;
  padding: 0 14px;
  border: 1px solid var(--border-strong);
  border-radius: 9px;
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}
.act-ghost svg { width: 16px; height: 16px; }
.act-ghost:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-soft); }
.act-ghost.icon-only { padding: 0; width: 38px; flex-shrink: 0; }
</style>
