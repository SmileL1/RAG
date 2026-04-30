<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { useRouter } from 'vue-router'
import { NPopconfirm } from 'naive-ui'
import type { KnowledgeBase } from '@/api/types'

const props = defineProps<{ kb: KnowledgeBase; docCount?: number }>()
const emit = defineEmits<{ remove: [id: number]; chat: [id: number] }>()

const router = useRouter()
function goUpload() {
  router.push(`/knowledge/${props.kb.id}/upload`)
}
function formatDate(s: string) {
  return new Date(s).toLocaleString('zh-CN', { hour12: false })
}
</script>

<template>
  <div class="kb-card glass-card glass-card-neon">
    <div class="kb-head">
      <div class="kb-icon brand-gradient">
        <Icon icon="ph:database-duotone" />
      </div>
      <div class="kb-title">
        <div class="name">{{ kb.name }}</div>
        <div class="meta">
          <span>📦 {{ docCount ?? 0 }} 个文档</span>
          <span>·</span>
          <span>📐 {{ kb.embedding_dim }} 维</span>
        </div>
      </div>
    </div>

    <div class="kb-desc">
      {{ kb.description || '（暂无描述）' }}
    </div>

    <div class="kb-meta-row">
      <span class="model">{{ kb.embedding_model }}</span>
      <span class="date">{{ formatDate(kb.created_at) }}</span>
    </div>

    <div class="kb-actions">
      <button class="btn-soft" @click="emit('chat', kb.id)">
        <Icon icon="ph:chat-circle-dots-duotone" /> 进入对话
      </button>
      <button class="btn-soft" @click="router.push(`/knowledge/${kb.id}`)">
        <Icon icon="ph:files-duotone" /> 查看文档
      </button>
      <button class="btn-soft" @click="goUpload">
        <Icon icon="ph:upload-duotone" /> 上传
      </button>
      <NPopconfirm @positive-click="emit('remove', kb.id)">
        <template #trigger>
          <button class="btn-danger" title="删除">
            <Icon icon="ph:trash-duotone" />
          </button>
        </template>
        删除该知识库及其所有文档/向量？此操作不可逆
      </NPopconfirm>
    </div>
  </div>
</template>

<style scoped>
.kb-card {
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  cursor: default;
  min-height: 200px;
}

.kb-head {
  display: flex;
  gap: 14px;
  align-items: center;
}
.kb-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 22px;
  color: #fff;
  flex-shrink: 0;
  box-shadow: var(--shadow-neon);
}
.kb-title {
  flex: 1;
  min-width: 0;
}
.name {
  font-size: 16px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.meta {
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

.kb-desc {
  flex: 1;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.kb-meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--text-muted);
}
.model {
  background: rgba(0, 212, 255, 0.1);
  color: var(--color-info);
  padding: 2px 8px;
  border-radius: 6px;
  font-family: var(--font-mono);
}

.kb-actions {
  display: flex;
  gap: 8px;
  border-top: 1px solid var(--border-subtle);
  padding-top: 12px;
}
.btn-soft, .btn-danger {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-soft:hover {
  background: rgba(123, 97, 255, 0.15);
  color: var(--text-primary);
  border-color: var(--border-neon);
}
.btn-danger {
  flex: 0 0 36px;
  padding: 8px;
  color: var(--color-error);
}
.btn-danger:hover {
  background: rgba(255, 77, 110, 0.15);
  border-color: var(--color-error);
}
</style>
