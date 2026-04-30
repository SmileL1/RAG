<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import CitationCard from './CitationCard.vue'
import { renderMarkdown } from '@/composables/useMarkdown'
import type { ChatMessageView } from '@/stores/chat'

const props = defineProps<{ msg: ChatMessageView }>()

const isUser = computed(() => props.msg.role === 'user')
const html = computed(() =>
  isUser.value ? '' : renderMarkdown(props.msg.content || ''),
)
</script>

<template>
  <div class="row" :class="{ user: isUser }">
    <div class="avatar" :class="{ user: isUser }">
      <Icon :icon="isUser ? 'ph:user-fill' : 'ph:robot-duotone'" />
    </div>

    <div class="bubble-wrap">
      <div class="bubble" :class="{ user: isUser, streaming: msg.streaming }">
        <div v-if="isUser" class="user-text">{{ msg.content }}</div>
        <div v-else class="md" v-html="html"></div>
        <span v-if="msg.streaming" class="cursor">▍</span>
      </div>

      <div v-if="msg.error" class="err">⚠ {{ msg.error }}</div>

      <CitationCard v-if="!isUser && msg.citations" :citations="msg.citations" />
    </div>
  </div>
</template>

<style scoped>
.row {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  align-items: flex-start;
}
.row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-size: 18px;
  flex-shrink: 0;
  background: var(--brand-gradient);
  color: #fff;
  box-shadow: var(--shadow-neon);
}
.avatar.user {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
  box-shadow: none;
}

.bubble-wrap {
  max-width: 78%;
  display: flex;
  flex-direction: column;
}
.row.user .bubble-wrap {
  align-items: flex-end;
}

.bubble {
  padding: 12px 16px;
  border-radius: 14px;
  border: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.04);
  line-height: 1.7;
  font-size: 14px;
  word-break: break-word;
}
.bubble.user {
  background: var(--brand-gradient);
  color: #fff;
  border: none;
}
.user-text {
  white-space: pre-wrap;
}

.cursor {
  display: inline-block;
  margin-left: 2px;
  animation: blink 1s steps(2) infinite;
  color: var(--color-info);
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.err {
  margin-top: 6px;
  color: var(--color-error);
  font-size: 12px;
}

/* Markdown 内部样式 */
.md :deep(p) {
  margin: 0 0 8px;
}
.md :deep(p:last-child) {
  margin-bottom: 0;
}
.md :deep(code) {
  background: rgba(0, 212, 255, 0.12);
  color: var(--color-info);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 12.5px;
}
.md :deep(pre) {
  margin: 8px 0;
  border-radius: 8px;
  overflow-x: auto;
}
.md :deep(pre code) {
  background: transparent;
  color: inherit;
  padding: 12px;
  display: block;
  font-size: 12.5px;
  line-height: 1.6;
}
.md :deep(ul), .md :deep(ol) {
  margin: 6px 0 8px;
  padding-left: 22px;
}
.md :deep(blockquote) {
  border-left: 3px solid var(--color-info);
  padding: 4px 12px;
  margin: 8px 0;
  background: rgba(0, 212, 255, 0.05);
  color: var(--text-secondary);
  border-radius: 0 6px 6px 0;
}
.md :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
}
.md :deep(th), .md :deep(td) {
  border: 1px solid var(--border-subtle);
  padding: 6px 10px;
}
.md :deep(strong) {
  color: var(--text-primary);
  font-weight: 700;
}
</style>
