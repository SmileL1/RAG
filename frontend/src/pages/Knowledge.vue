<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { NSpin, useDialog, useMessage } from 'naive-ui'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
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
      <button class="btn-neon" @click="showCreate = true">
        <Icon icon="ph:plus-bold" /> &nbsp;新建知识库
      </button>
    </div>

    <NSpin :show="kbStore.loading" description="加载中…">
      <div v-if="empty" class="empty glass-card">
        <div class="empty-icon">📂</div>
        <div class="empty-title">还没有知识库</div>
        <div class="empty-desc">
          上传第一份文档，<span class="text-gradient">开启你的 AI 第二大脑</span> →
        </div>
        <button class="btn-neon" style="margin-top: 24px" @click="showCreate = true">
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
}
.page-title {
  font-size: 26px;
  font-weight: 700;
}
.page-sub {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}
.empty {
  padding: 80px 40px;
  text-align: center;
}
.empty-icon {
  font-size: 64px;
  margin-bottom: 18px;
  opacity: 0.6;
}
.empty-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 10px;
}
.empty-desc {
  color: var(--text-secondary);
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 18px;
}
</style>
