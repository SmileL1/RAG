<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import { useMessage } from 'naive-ui'
import DropZone from '@/components/upload/DropZone.vue'
import UploadList, { type UploadRow } from '@/components/upload/UploadList.vue'
import { docApi } from '@/api/documents'
import { kbApi } from '@/api/knowledgeBase'
import type { Document, KnowledgeBase } from '@/api/types'
import { usePolling } from '@/composables/usePolling'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const kbId = Number(route.params.id)

const kb = ref<KnowledgeBase | null>(null)
const rows = ref<UploadRow[]>([])
const existingDocs = ref<Document[]>([])

onMounted(async () => {
  try {
    kb.value = await kbApi.get(kbId)
    existingDocs.value = await docApi.list(kbId)
  } catch (e) {
    message.error('加载知识库信息失败：' + (e as Error).message)
    router.push('/knowledge')
  }
})

async function onFiles(files: File[]) {
  for (const f of files) {
    const key = `${f.name}-${f.size}-${Date.now()}-${Math.random()}`
    const row: UploadRow = {
      key,
      filename: f.name,
      size: f.size,
      uploadPct: 0,
    }
    rows.value = [row, ...rows.value]
    uploadOne(row, f)
  }
}

async function uploadOne(row: UploadRow, file: File) {
  try {
    const doc = await docApi.upload(kbId, file, (pct) => {
      const idx = rows.value.findIndex((r) => r.key === row.key)
      if (idx >= 0) {
        rows.value[idx] = { ...rows.value[idx], uploadPct: pct }
      }
    })
    const idx = rows.value.findIndex((r) => r.key === row.key)
    if (idx >= 0) {
      rows.value[idx] = { ...rows.value[idx], uploadPct: 100, doc }
    }
  } catch (e) {
    const idx = rows.value.findIndex((r) => r.key === row.key)
    if (idx >= 0) {
      rows.value[idx] = { ...rows.value[idx], error: (e as Error).message }
    }
  }
}

// 后台轮询所有 pending/processing 的文档
const polling = usePolling(async () => {
  const targets = rows.value.filter((r) => r.doc && (r.doc.status === 'pending' || r.doc.status === 'processing'))
  if (targets.length === 0) return false  // 全部完成 → 停轮询
  await Promise.all(
    targets.map(async (r) => {
      try {
        const fresh = await docApi.status(r.doc!.id)
        const idx = rows.value.findIndex((x) => x.key === r.key)
        if (idx >= 0) {
          rows.value[idx] = { ...rows.value[idx], doc: { ...rows.value[idx].doc!, ...fresh } }
        }
      } catch (e) {
        // 单个失败不影响其他
        console.warn('poll status failed', e)
      }
    }),
  )
  return true
}, 2500)

const hasPending = computed(() =>
  rows.value.some((r) => r.doc && (r.doc.status === 'pending' || r.doc.status === 'processing')),
)

// 一旦有上传完成的 doc，启动轮询
import { watch } from 'vue'
watch(
  () => rows.value.map((r) => r.doc?.id).join(','),
  () => {
    if (hasPending.value && !polling.running.value) polling.start()
  },
)
</script>

<template>
  <div class="upload-page">
    <button class="back" @click="router.back()">
      <Icon icon="ph:arrow-left-bold" /> &nbsp;返回
    </button>

    <div class="head">
      <h2 class="title">
        上传文档
        <span v-if="kb" class="kb-name">→ {{ kb.name }}</span>
      </h2>
      <div class="sub">
        <span v-if="kb">已有 {{ existingDocs.length }} 个文档 · {{ kb.embedding_model }}</span>
      </div>
    </div>

    <DropZone @files="onFiles" />

    <UploadList :rows="rows" />
  </div>
</template>

<style scoped>
.upload-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.back {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  background: transparent;
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  padding: 6px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
}
.back:hover {
  border-color: var(--border-neon);
  color: var(--text-primary);
}
.head {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.title {
  font-size: 24px;
  font-weight: 700;
}
.kb-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-left: 8px;
}
.sub {
  font-size: 12px;
  color: var(--text-muted);
}
</style>
