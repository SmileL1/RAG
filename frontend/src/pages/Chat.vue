<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'
import { useKnowledgeStore } from '@/stores/knowledge'
import { useChatStore } from '@/stores/chat'
import { streamChat, chatApi } from '@/api/chat'
import { Icon } from '@iconify/vue'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import KbSelector from '@/components/chat/KbSelector.vue'
import type { Conversation } from '@/api/types'

const kbStore = useKnowledgeStore()
const chatStore = useChatStore()

const conversations = ref<Conversation[]>([])
const messagesEl = ref<HTMLElement | null>(null)
let abortCtrl: AbortController | null = null

onMounted(async () => {
  if (kbStore.list.length === 0) await kbStore.refresh()
  await loadConversations()
})

async function loadConversations() {
  conversations.value = await chatApi.conversations()
}

async function selectConv(conv: Conversation) {
  if (chatStore.sending) {
    // 先中止当前流，再切换
    abortCtrl?.abort()
    abortCtrl = null
    chatStore.sending = false
  }
  chatStore.reset()
  chatStore.currentConvId = conv.id
  const msgs = await chatApi.messages(conv.id)
  chatStore.messages = msgs.map((m) => ({
    id: m.id,
    role: m.role as 'user' | 'assistant',
    content: m.content,
    citations: m.citations ?? undefined,
  }))
  scrollBottom()
}

async function newConversation() {
  if (chatStore.sending) return
  chatStore.reset()
}

async function removeConv(id: number) {
  await chatApi.removeConversation(id)
  conversations.value = conversations.value.filter((c) => c.id !== id)
  if (chatStore.currentConvId === id) chatStore.reset()
}

async function send(text: string) {
  if (!kbStore.currentId) return
  chatStore.sending = true

  chatStore.pushMessage({ id: Date.now(), role: 'user', content: text })
  const assistantId = Date.now() + 1
  chatStore.pushMessage({ id: assistantId, role: 'assistant', content: '', streaming: true })
  scrollBottom()

  abortCtrl = new AbortController()
  try {
    const gen = streamChat(
      {
        kb_id: kbStore.currentId,
        question: text,
        conversation_id: chatStore.currentConvId,
      },
      abortCtrl.signal,
    )

    for await (const ev of gen) {
      if (ev.type === 'meta') {
        chatStore.currentConvId = ev.conversation_id
      } else if (ev.type === 'token') {
        chatStore.appendToLast(ev.content)
        scrollBottom()
      } else if (ev.type === 'citation') {
        chatStore.updateLast({ citations: ev.citations })
      } else if (ev.type === 'done') {
        chatStore.updateLast({ streaming: false })
        await loadConversations()
      } else if (ev.type === 'error') {
        chatStore.updateLast({ streaming: false, error: ev.message })
      }
    }
  } catch (e: unknown) {
    const err = e as Error
    if (err.name !== 'AbortError') {
      chatStore.updateLast({ streaming: false, error: err.message })
    } else {
      chatStore.updateLast({ streaming: false })
    }
  } finally {
    chatStore.sending = false
    abortCtrl = null
  }
}

function abort() {
  abortCtrl?.abort()
}

function scrollBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    }
  })
}

watch(
  () => chatStore.messages.length,
  () => scrollBottom(),
)
</script>

<template>
  <div class="chat-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar glass-card">
      <button class="new-btn btn-neon" @click="newConversation">
        <Icon icon="ph:plus-bold" />
        新对话
      </button>

      <div class="conv-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conv-item"
          :class="{ active: chatStore.currentConvId === conv.id }"
          @click="selectConv(conv)"
        >
          <Icon icon="ph:chat-circle-text" class="conv-icon" />
          <span class="conv-title">{{ conv.title || '新对话' }}</span>
          <button
            class="del-btn"
            @click.stop="removeConv(conv.id)"
            title="删除"
          >
            <Icon icon="ph:trash" />
          </button>
        </div>
        <div v-if="conversations.length === 0" class="empty-hint">
          暂无对话记录
        </div>
      </div>
    </aside>

    <!-- 主聊天区 -->
    <main class="chat-main">
      <!-- 顶部工具栏 -->
      <div class="topbar glass-card">
        <KbSelector />
        <div v-if="!kbStore.currentId" class="no-kb-tip">
          ⚠ 请先选择或创建知识库
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="messages" ref="messagesEl">
        <div v-if="chatStore.messages.length === 0" class="welcome">
          <div class="welcome-icon">
            <Icon icon="ph:robot-duotone" />
          </div>
          <h2 class="welcome-title">
            让你的文档<span class="text-gradient">开口说话</span>
          </h2>
          <p class="welcome-sub">选择知识库后，输入问题即可开始 AI 问答</p>
        </div>

        <MessageBubble
          v-for="msg in chatStore.messages"
          :key="msg.id"
          :msg="msg"
        />
      </div>

      <!-- 输入框 -->
      <div class="input-area">
        <ChatInput
          :disabled="!kbStore.currentId"
          :streaming="chatStore.sending"
          :placeholder="
            kbStore.currentId
              ? '问点什么…（Enter 发送，Shift+Enter 换行）'
              : '请先选择知识库…'
          "
          @submit="send"
          @abort="abort"
        />
      </div>
    </main>
  </div>
</template>

<style scoped>
.chat-layout {
  display: flex;
  height: 100%;
  gap: 16px;
  overflow: hidden;
}

/* ===== 侧边栏 ===== */
.sidebar {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 12px;
  overflow: hidden;
}

.new-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 9px 0;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border-radius: 10px;
  text-decoration: none;
}

.conv-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  transition: background 0.15s;
  min-width: 0;
}

.conv-item:hover {
  background: rgba(37, 99, 235, 0.07);
  color: var(--text-primary);
}

.conv-item.active {
  background: rgba(37, 99, 235, 0.12);
  color: #2563EB;
}

.conv-icon {
  flex-shrink: 0;
  font-size: 15px;
}

.conv-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.del-btn {
  flex-shrink: 0;
  display: none;
  background: transparent;
  border: none;
  color: var(--color-error);
  cursor: pointer;
  font-size: 14px;
  padding: 2px;
  border-radius: 4px;
}

.conv-item:hover .del-btn {
  display: block;
}

.empty-hint {
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
  padding: 24px 0;
}

/* ===== 主聊天区 ===== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
  overflow: hidden;
}

.topbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  flex-shrink: 0;
}

.no-kb-tip {
  font-size: 12px;
  color: var(--color-warning, #FFB800);
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 4px 4px 0;
}

/* 欢迎屏 */
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  gap: 12px;
  padding: 40px 20px;
}

.welcome-icon {
  font-size: 56px;
  color: var(--color-info);
  opacity: 0.7;
}

.welcome-title {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.3px;
}

.welcome-sub {
  font-size: 14px;
  color: var(--text-secondary);
}

.input-area {
  flex-shrink: 0;
}
</style>
