<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { NProgress } from 'naive-ui'
import type { Document, DocumentStatus } from '@/api/types'

export interface UploadRow {
  key: string
  filename: string
  size: number
  /** 0~100 上传进度 */
  uploadPct: number
  /** 上传完后服务端的 doc 记录 */
  doc?: Document
  /** 本地错误 */
  error?: string
}

defineProps<{ rows: UploadRow[] }>()

function statusText(s: DocumentStatus | undefined, err?: string) {
  if (err) return '上传失败'
  if (!s) return '上传中…'
  return {
    pending: '排队中',
    processing: '解析中…',
    ready: '已入库',
    failed: '解析失败',
  }[s]
}

function statusColor(s: DocumentStatus | undefined, err?: string) {
  if (err) return 'var(--color-error)'
  if (!s || s === 'pending') return 'var(--color-warning)'
  if (s === 'processing') return 'var(--color-info)'
  if (s === 'ready') return 'var(--color-success)'
  if (s === 'failed') return 'var(--color-error)'
  return 'var(--text-muted)'
}

function statusIcon(s: DocumentStatus | undefined, err?: string) {
  if (err || s === 'failed') return 'ph:x-circle-duotone'
  if (s === 'ready') return 'ph:check-circle-duotone'
  if (s === 'processing' || !s) return 'svg-spinners:ring-resize'
  return 'ph:hourglass-medium-duotone'
}

function fmtSize(b: number) {
  if (b < 1024) return `${b} B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`
  return `${(b / 1024 / 1024).toFixed(1)} MB`
}
</script>

<template>
  <div v-if="rows.length" class="upload-list glass-card">
    <div class="hd">已上传 {{ rows.length }} 项</div>
    <div class="rows">
      <div v-for="r in rows" :key="r.key" class="row">
        <div class="bar" :style="{ background: statusColor(r.doc?.status, r.error) }"></div>
        <div class="info">
          <div class="line1">
            <span class="name" :title="r.filename">{{ r.filename }}</span>
            <span class="size">{{ fmtSize(r.size) }}</span>
          </div>
          <div class="line2">
            <Icon :icon="statusIcon(r.doc?.status, r.error)" />
            <span :style="{ color: statusColor(r.doc?.status, r.error) }">
              {{ statusText(r.doc?.status, r.error) }}
            </span>
            <span v-if="r.doc?.chunk_count" class="dim">
              · 已切 {{ r.doc.chunk_count }} 块
            </span>
            <span v-if="r.error" class="dim error">{{ r.error }}</span>
            <span v-else-if="r.doc?.error_message" class="dim error">
              {{ r.doc.error_message }}
            </span>
          </div>
          <NProgress
            v-if="r.uploadPct < 100 && !r.error"
            :percentage="r.uploadPct"
            :height="3"
            :show-indicator="false"
            color="var(--color-info)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.upload-list {
  padding: 16px 18px;
}
.hd {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 10px;
}
.rows {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.row {
  display: flex;
  gap: 12px;
  padding: 12px 14px;
  background: var(--bg-secondary);
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
}
.bar {
  width: 3px;
  border-radius: 2px;
  flex-shrink: 0;
  transition: background 0.3s;
}
.info {
  flex: 1;
  min-width: 0;
}
.line1 {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}
.name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 70%;
}
.size {
  color: var(--text-muted);
  font-size: 12px;
}
.line2 {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.dim {
  color: var(--text-muted);
}
.error {
  color: var(--color-error);
}
</style>
