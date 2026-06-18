<script setup lang="ts">
import { computed } from 'vue'
import CitationCard from './CitationCard.vue'
import { renderMarkdown } from '@/composables/useMarkdown'
import type { ChatMessageView } from '@/stores/chat'

const props = defineProps<{ msg: ChatMessageView }>()

const isUser = computed(() => props.msg.role === 'user')
const html = computed(() =>
  isUser.value ? '' : renderMarkdown(props.msg.content || ''),
)
const statusText = computed(() => {
  const n = props.msg.citations?.length ?? 0
  return n > 0 ? `已生成 · 引用 ${n} 处来源` : '已生成'
})
</script>

<template>
  <!-- 用户消息：右对齐气泡，无头像 -->
  <div v-if="isUser" class="msg-user">
    <div class="bubble-user">{{ msg.content }}</div>
  </div>

  <!-- AI 消息：头像 + 名条 + 卡片 -->
  <div v-else class="msg-ai">
    <div class="ai-ava">
      <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="12" rx="3"/><path d="M12 8V4"/><circle cx="12" cy="3" r="1.4" fill="#fff" stroke="none"/><circle cx="8.5" cy="14" r="1.3" fill="#fff" stroke="none"/><circle cx="15.5" cy="14" r="1.3" fill="#fff" stroke="none"/></svg>
    </div>
    <div class="ai-body">
      <div class="ai-name">
        <span class="nm">知识库助手</span>
        <span class="stream-tag" :class="{ live: msg.streaming }">
          <span class="pulse" />
          {{ msg.streaming ? '生成中…' : statusText }}
        </span>
      </div>

      <div class="ai-card">
        <div class="md prose" v-html="html" />
        <span v-if="msg.streaming" class="cursor">▍</span>
        <div v-if="msg.error" class="err">⚠ {{ msg.error }}</div>
        <CitationCard v-if="msg.citations" :citations="msg.citations" />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ===== 用户消息 ===== */
.msg-user { display: flex; justify-content: flex-end; }
.bubble-user {
  max-width: 78%;
  background: var(--accent);
  color: #fff;
  padding: 13px 17px;
  border-radius: 14px 14px 4px 14px;
  font-size: 14.5px;
  line-height: 1.62;
  letter-spacing: -0.003em;
  white-space: pre-wrap;
  word-break: break-word;
  box-shadow: 0 4px 16px rgba(91, 79, 232, 0.22);
}

/* ===== AI 消息 ===== */
.msg-ai { display: flex; gap: 14px; }
.ai-ava {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  flex-shrink: 0;
  margin-top: 2px;
  background: linear-gradient(180deg, #6A5FF0, #5141D6);
  display: grid;
  place-items: center;
  box-shadow: 0 3px 10px rgba(91, 79, 232, 0.32);
}
.ai-ava svg { width: 19px; height: 19px; }
.ai-body { flex: 1; min-width: 0; }
.ai-name { display: flex; align-items: center; gap: 8px; margin-bottom: 7px; }
.ai-name .nm {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}
.stream-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10.5px;
  font-weight: 600;
  color: var(--color-success);
  background: var(--color-success-soft);
  padding: 2px 8px;
  border-radius: 20px;
}
.stream-tag .pulse { width: 6px; height: 6px; border-radius: 50%; background: var(--color-success); }
.stream-tag.live .pulse { animation: pulse-ring 1.6s infinite; }
@keyframes pulse-ring {
  0% { box-shadow: 0 0 0 0 rgba(14, 159, 110, 0.45); }
  70% { box-shadow: 0 0 0 6px rgba(14, 159, 110, 0); }
  100% { box-shadow: 0 0 0 0 rgba(14, 159, 110, 0); }
}

.ai-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  padding: 18px 20px;
  box-shadow: var(--shadow-glass);
}

.cursor {
  display: inline-block;
  margin-left: 2px;
  animation: blink 1s steps(2) infinite;
  color: var(--accent);
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
.err {
  margin-top: 8px;
  color: var(--color-error);
  font-size: 12px;
}

/* ===== Markdown 排版 ===== */
.prose {
  font-size: 14.5px;
  line-height: 1.72;
  color: var(--text-secondary);
  letter-spacing: -0.003em;
}
.md :deep(p) { margin: 0 0 12px; }
.md :deep(p:last-child) { margin-bottom: 0; }
.md :deep(strong) { color: var(--text-primary); font-weight: 600; }
.md :deep(code) {
  background: var(--accent-soft);
  color: var(--accent);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 12.5px;
}
.md :deep(pre) { margin: 10px 0; border-radius: 10px; overflow-x: auto; }
.md :deep(pre code) {
  background: transparent;
  color: inherit;
  padding: 14px 16px;
  display: block;
  font-size: 12.5px;
  line-height: 1.6;
}
/* 列表：干净的标准列表，紫色序号/项目符，嵌套自然缩进 */
.md :deep(ol), .md :deep(ul) {
  margin: 8px 0 12px;
  padding-left: 24px;
}
.md :deep(ol) { list-style: decimal; }
.md :deep(ul) { list-style: disc; }
.md :deep(li) {
  margin: 5px 0;
  line-height: 1.7;
  padding-left: 4px;
}
.md :deep(li::marker) { color: var(--accent); font-weight: 700; }
/* 嵌套列表更紧凑 */
.md :deep(li > ol), .md :deep(li > ul) { margin: 4px 0 4px; }
.md :deep(blockquote) {
  border-left: 3px solid var(--accent);
  padding: 4px 12px;
  margin: 10px 0;
  background: var(--accent-soft);
  color: var(--text-secondary);
  border-radius: 0 8px 8px 0;
}
.md :deep(table) { border-collapse: collapse; margin: 10px 0; width: 100%; }
.md :deep(th), .md :deep(td) {
  border: 1px solid var(--border-subtle);
  padding: 7px 11px;
  font-size: 13px;
  text-align: left;
}
.md :deep(th) { background: var(--bg-secondary); font-weight: 700; color: var(--text-primary); }
</style>
