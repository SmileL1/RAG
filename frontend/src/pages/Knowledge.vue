<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { NSpin, useDialog, useMessage } from 'naive-ui'
import { useRouter } from 'vue-router'
import { useKnowledgeStore } from '@/stores/knowledge'
import { docApi } from '@/api/documents'
import KbCard from '@/components/knowledge/KbCard.vue'
import CreateKbDialog from '@/components/knowledge/CreateKbDialog.vue'

const kbStore = useKnowledgeStore()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()

const showCreate = ref(false)
const docCounts = ref<Record<number, number>>({})

const empty = computed(() => !kbStore.loading && kbStore.list.length === 0)

async function refresh() {
  await kbStore.refresh()
  // 并行拉每个 KB 的文档数（粗略：list().length）
  await Promise.all(
    kbStore.list.map(async (kb) => {
      try {
        const docs = await docApi.list(kb.id)
        docCounts.value[kb.id] = docs.length
      } catch {
        docCounts.value[kb.id] = 0
      }
    }),
  )
}

onMounted(refresh)

function onCreated(id: number) {
  message.success('开始上传你的第一份文档吧')
  router.push(`/knowledge/${id}/upload`)
}

async function onRemove(id: number) {
  try {
    await kbStore.remove(id)
    message.success('已删除')
  } catch (e) {
    dialog.error({ title: '删除失败', content: (e as Error).message })
  }
}

function onChat(id: number) {
  kbStore.currentId = id
  router.push('/')
}
</script>

<template>
  <div class="kb-page">
    <div class="page-head">
      <div>
        <h2 class="page-title">知识库</h2>
        <div class="page-sub">每个知识库是独立的向量空间，互不污染</div>
      </div>
      <button class="create-btn" @click="showCreate = true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        新建知识库
      </button>
    </div>

    <NSpin :show="kbStore.loading" description="加载中…">
      <div v-if="empty" class="empty">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/></svg>
        </div>
        <div class="empty-title">还没有知识库</div>
        <div class="empty-desc">上传第一份文档，<span class="text-gradient">开启你的 AI 第二大脑</span></div>
        <button class="create-btn" style="margin-top: 22px" @click="showCreate = true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          创建第一个知识库
        </button>
      </div>

      <div v-else class="grid">
        <KbCard
          v-for="kb in kbStore.list"
          :key="kb.id"
          :kb="kb"
          :doc-count="docCounts[kb.id]"
          @remove="onRemove"
          @chat="onChat"
        />
      </div>
    </NSpin>

    <CreateKbDialog v-model:show="showCreate" @created="onCreated" />
  </div>
</template>

<style scoped>
.kb-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100%;
}
.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}
.page-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}
.page-sub {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 5px;
}
.create-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 40px;
  padding: 0 18px;
  border: none;
  border-radius: 10px;
  background: var(--accent);
  color: #fff;
  font-family: var(--font-display);
  font-size: 13.5px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: var(--shadow-neon);
  transition: background 0.15s, transform 0.15s;
  flex-shrink: 0;
}
.create-btn svg { width: 16px; height: 16px; }
.create-btn:hover { background: var(--accent-hover); transform: translateY(-1px); }

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 72px 40px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-glass);
}
.empty-icon {
  width: 68px;
  height: 68px;
  border-radius: 18px;
  background: var(--accent-soft);
  border: 1px solid #DCD7FA;
  color: var(--accent);
  display: grid;
  place-items: center;
  margin-bottom: 18px;
}
.empty-icon svg { width: 34px; height: 34px; }
.empty-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.empty-desc {
  font-size: 14px;
  color: var(--text-secondary);
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
</style>
