<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import { useMessage } from 'naive-ui'
import { docApi } from '@/api/documents'
import { useKnowledgeStore } from '@/stores/knowledge'
import type { Document } from '@/api/types'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const kbStore = useKnowledgeStore()

const kbId = computed(() => Number(route.params.id))
const kb = computed(() => kbStore.list.find((k) => k.id === kbId.value))

const docs = ref<Document[]>([])
const loading = ref(false)
const deletingId = ref<number | null>(null)

// ── 预览 ────────────────────────────────────────────────
const previewDoc = ref<Document | null>(null)
const previewText = ref('')
const previewLoading = ref(false)
const openingRaw = ref(false)

// MIME 类型可在浏览器内联渲染的格式
const INLINE_MIMES = new Set(['application/pdf', 'text/plain', 'text/html', 'text/markdown'])
function canOpenRaw(doc: Document) {
  return doc.mime_type && INLINE_MIMES.has(doc.mime_type)
}

async function openPreview(doc: Document) {
  previewDoc.value = doc
  previewText.value = ''
  previewLoading.value = true
  try {
    const result = await docApi.text(doc.id)
    previewText.value = result.content || '（未提取到文本内容）'
  } catch (e: unknown) {
    previewText.value = '加载失败：' + (e as Error).message
  } finally {
    previewLoading.value = false
  }
}

function closePreview() {
  previewDoc.value = null
  previewText.value = ''
}

async function openRawFile(doc: Document) {
  openingRaw.value = true
  let blobUrl = ''
  try {
    blobUrl = await docApi.rawBlobUrl(doc.id)
    window.open(blobUrl, '_blank')
    // 延迟释放，等浏览器完成加载
    setTimeout(() => URL.revokeObjectURL(blobUrl), 30_000)
  } catch (e: unknown) {
    message.error((e as Error).message)
    if (blobUrl) URL.revokeObjectURL(blobUrl)
  } finally {
    openingRaw.value = false
  }
}
// ────────────────────────────────────────────────────────

const statusLabel: Record<string, string> = {
  pending: '等待处理',
  processing: '处理中',
  ready: '已就绪',
  failed: '失败',
}
const statusClass: Record<string, string> = {
  pending: 'tag-pending',
  processing: 'tag-processing',
  ready: 'tag-ready',
  failed: 'tag-failed',
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(s: string): string {
  return new Date(s).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: false,
  })
}

async function load() {
  loading.value = true
  try {
    if (kbStore.list.length === 0) await kbStore.refresh()
    docs.value = await docApi.list(kbId.value)
  } catch (e: unknown) {
    message.error((e as Error).message)
  } finally {
    loading.value = false
  }
}

async function removeDoc(doc: Document) {
  if (!confirm(`确定删除文档「${doc.filename}」？此操作不可恢复，相关向量也将删除。`)) return
  deletingId.value = doc.id
  try {
    await docApi.remove(doc.id)
    docs.value = docs.value.filter((d) => d.id !== doc.id)
    message.success('已删除')
  } catch (e: unknown) {
    message.error((e as Error).message)
  } finally {
    deletingId.value = null
  }
}

onMounted(load)
</script>

<template>
  <div class="kb-docs-page">
    <div class="page-header">
      <button class="back-btn" @click="router.push('/knowledge')">
        <Icon icon="ph:arrow-left-bold" />
        知识库列表
      </button>
      <div class="header-info">
        <h2 class="page-title">
          <Icon icon="ph:database-duotone" class="title-icon" />
          {{ kb?.name ?? '知识库' }}
        </h2>
        <span v-if="kb?.description" class="kb-desc">{{ kb.description }}</span>
      </div>
      <button class="btn-neon upload-btn" @click="router.push(`/knowledge/${kbId}/upload`)">
        <Icon icon="ph:upload-duotone" />
        上传文档
      </button>
    </div>

    <div class="glass-card table-card">
      <div v-if="loading" class="center-hint">加载中…</div>
      <div v-else-if="docs.length === 0" class="center-hint">
        <div class="empty-icon">📄</div>
        <div>还没有文档，点击右上角「上传文档」开始吧</div>
      </div>
      <table v-else class="doc-table">
        <thead>
          <tr>
            <th>文件名</th>
            <th>大小</th>
            <th>分块数</th>
            <th>状态</th>
            <th>上传时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="doc in docs" :key="doc.id">
            <td class="col-name">
              <Icon icon="ph:file-text-duotone" class="file-icon" />
              <span class="filename" :title="doc.filename">{{ doc.filename }}</span>
            </td>
            <td class="col-size">{{ formatSize(doc.file_size) }}</td>
            <td class="col-chunks">
              <span v-if="doc.chunk_count > 0">{{ doc.chunk_count }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td>
              <span class="tag" :class="statusClass[doc.status]">
                {{ statusLabel[doc.status] }}
              </span>
              <div v-if="doc.status === 'failed' && doc.error_message" class="error-tip">
                {{ doc.error_message }}
              </div>
            </td>
            <td class="col-date">{{ formatDate(doc.created_at) }}</td>
            <td class="col-actions">
              <button
                class="action-btn"
                title="预览内容"
                @click="openPreview(doc)"
              >
                <Icon icon="ph:eye-duotone" />
              </button>
              <button
                class="action-btn danger"
                :disabled="deletingId === doc.id"
                title="删除"
                @click="removeDoc(doc)"
              >
                <Icon icon="ph:trash-duotone" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 预览模态框 -->
    <Teleport to="body">
      <div v-if="previewDoc" class="modal-mask" @click.self="closePreview">
        <div class="preview-modal glass-card">
          <!-- 头部 -->
          <div class="preview-header">
            <div class="preview-title-row">
              <Icon icon="ph:file-text-duotone" class="preview-file-icon" />
              <span class="preview-filename" :title="previewDoc.filename">
                {{ previewDoc.filename }}
              </span>
              <span class="preview-meta">
                {{ formatSize(previewDoc.file_size) }} · {{ previewDoc.chunk_count }} 块
              </span>
            </div>
            <div class="preview-actions-row">
              <button
                v-if="canOpenRaw(previewDoc)"
                class="btn-outline"
                :disabled="openingRaw"
                @click="openRawFile(previewDoc)"
              >
                <Icon icon="ph:arrow-square-out-duotone" />
                {{ openingRaw ? '打开中…' : '在新标签页查看原文件' }}
              </button>
              <button class="close-btn" title="关闭" @click="closePreview">
                <Icon icon="ph:x-bold" />
              </button>
            </div>
          </div>

          <!-- 内容区 -->
          <div class="preview-body">
            <div v-if="previewLoading" class="preview-loading">
              <Icon icon="ph:circle-notch-bold" class="spin" />
              加载中…
            </div>
            <pre v-else class="preview-text">{{ previewText }}</pre>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.kb-docs-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: 8px;
  border: 1.5px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
}
.back-btn:hover { background: rgba(0, 0, 0, 0.04); color: var(--text-primary); }

.header-info {
  flex: 1;
  min-width: 0;
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.title-icon { color: #2563EB; font-size: 22px; }
.kb-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
  display: block;
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 10px;
  cursor: pointer;
  border: none;
  white-space: nowrap;
  flex-shrink: 0;
}

.table-card {
  padding: 0;
  overflow: hidden;
}
.center-hint {
  padding: 60px 40px;
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.empty-icon { font-size: 48px; opacity: 0.5; }

.doc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.doc-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-subtle);
  background: rgba(37, 99, 235, 0.03);
  white-space: nowrap;
}
.doc-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-subtle);
  color: var(--text-primary);
  vertical-align: middle;
}
.doc-table tr:last-child td { border-bottom: none; }
.doc-table tr:hover td { background: rgba(37, 99, 235, 0.03); }

.col-name {
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 360px;
}
.file-icon { font-size: 18px; color: #2563EB; flex-shrink: 0; }
.filename {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}
.col-size { color: var(--text-muted); white-space: nowrap; }
.col-chunks { color: var(--text-muted); }
.text-muted { color: var(--text-muted); }
.col-date { color: var(--text-muted); font-size: 12px; white-space: nowrap; }
.col-actions { width: 70px; display: flex; gap: 4px; }

.tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}
.tag-ready      { background: rgba(34, 197, 94, 0.12); color: #16a34a; }
.tag-pending    { background: rgba(251, 191, 36, 0.12); color: #d97706; }
.tag-processing { background: rgba(59, 130, 246, 0.12); color: #2563EB; }
.tag-failed     { background: rgba(239, 68, 68, 0.10); color: #dc2626; }

.error-tip {
  font-size: 11px;
  color: #dc2626;
  margin-top: 4px;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-btn {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: grid;
  place-items: center;
  font-size: 15px;
  transition: background 0.15s, color 0.15s;
}
.action-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.action-btn:hover { background: rgba(37, 99, 235, 0.08); color: #2563EB; }
.action-btn.danger:hover { background: rgba(239, 68, 68, 0.08); color: #dc2626; }

/* ===== 预览模态框 ===== */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  backdrop-filter: blur(3px);
}

.preview-modal {
  width: min(860px, 92vw);
  height: min(80vh, 720px);
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.preview-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}
.preview-file-icon { font-size: 20px; color: #2563EB; flex-shrink: 0; }
.preview-filename {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.preview-meta {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
  flex-shrink: 0;
}

.preview-actions-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border-radius: 8px;
  border: 1.5px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}
.btn-outline:hover { border-color: #2563EB; color: #2563EB; background: rgba(37,99,235,0.06); }
.btn-outline:disabled { opacity: 0.4; cursor: not-allowed; }

.close-btn {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  display: grid;
  place-items: center;
  font-size: 14px;
  transition: background 0.15s, color 0.15s;
}
.close-btn:hover { background: rgba(239, 68, 68, 0.08); color: #dc2626; }

.preview-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.preview-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 100%;
  color: var(--text-muted);
  font-size: 14px;
}

.preview-text {
  margin: 0;
  font-family: var(--font-mono, 'Fira Code', 'Consolas', monospace);
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
.spin { animation: spin 1s linear infinite; }
</style>
