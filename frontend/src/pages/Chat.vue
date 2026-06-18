<script setup lang="ts">
import { nextTick, onMounted, ref, watch, computed } from 'vue'
import { useKnowledgeStore } from '@/stores/knowledge'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import { streamChat, chatApi } from '@/api/chat'
import { RouterLink } from 'vue-router'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import KbSelector from '@/components/chat/KbSelector.vue'
import CitationViewerDrawer from '@/components/chat/CitationViewerDrawer.vue'
import type { Conversation } from '@/api/types'

const kbStore = useKnowledgeStore()
const chatStore = useChatStore()
const authStore = useAuthStore()

const conversations = ref<Conversation[]>([])
const messagesEl = ref<HTMLElement | null>(null)
let abortCtrl: AbortController | null = null

// 当前会话标题（顶栏左侧）
const activeConvTitle = computed(() => {
  const c = conversations.value.find((x) => x.id === chatStore.currentConvId)
  return c?.title || '新对话'
})

// 用户卡信息
const userName = computed(() => authStore.username || '用户')
const userInitial = computed(() => userName.value.charAt(0).toUpperCase())
const roleLabel = computed(() => (authStore.isAdmin ? '管理员' : '成员'))

onMounted(async () => {
  if (kbStore.list.length === 0) await kbStore.refresh()
  await loadConversations()
})

async function loadConversations() {
  conversations.value = await chatApi.conversations(kbStore.currentId ?? undefined)
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

// 切换知识库时重新加载该 KB 的会话列表，并清空当前对话
watch(
  () => kbStore.currentId,
  async () => {
    chatStore.reset()
    await loadConversations()
  },
)

watch(
  () => chatStore.messages.length,
  () => scrollBottom(),
)
</script>

<template>
  <div class="chat-layout">
    <!-- 会话侧栏 -->
    <aside class="sidebar">
      <div class="side-head">
        <div class="side-eyebrow">知识库 · 私有 AI 问答</div>
        <button class="new-chat" @click="newConversation">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          新对话
        </button>
      </div>

      <div class="conv-group-title">最近对话</div>
      <div class="conv-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conv"
          :class="{ active: chatStore.currentConvId === conv.id }"
          @click="selectConv(conv)"
        >
          <svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span class="title">{{ conv.title || '新对话' }}</span>
          <button class="del" @click.stop="removeConv(conv.id)" title="删除">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
        <div v-if="conversations.length === 0" class="conv-empty">暂无对话记录</div>
      </div>

      <div class="side-foot">
        <div class="user-chip">
          <div class="avatar">{{ userInitial }}</div>
          <div class="user-meta">
            <div class="n">{{ userName }}</div>
            <div class="r">{{ roleLabel }}</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 主聊天区 -->
    <main class="chat-main">
      <!-- 顶部工具栏 -->
      <header class="topbar">
        <div class="conv-heading">
          <div class="conv-title">{{ activeConvTitle }}</div>
        </div>
        <div class="topbar-spacer" />
        <div v-if="!kbStore.currentId" class="no-kb-tip">⚠ 请先选择知识库</div>
        <KbSelector />
        <RouterLink to="/settings" class="icon-btn" title="检索参数">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>
        </RouterLink>
      </header>

      <!-- 消息列表 -->
      <section class="thread" ref="messagesEl">
        <div class="thread-inner">
          <div v-if="chatStore.messages.length === 0" class="welcome">
            <div class="welcome-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="12" rx="3"/><path d="M12 8V4"/><circle cx="12" cy="3.2" r="1.3" fill="currentColor" stroke="none"/><circle cx="8.5" cy="14" r="1.3" fill="currentColor" stroke="none"/><circle cx="15.5" cy="14" r="1.3" fill="currentColor" stroke="none"/></svg>
            </div>
            <h2 class="welcome-title">让你的文档<span class="text-gradient">开口说话</span></h2>
            <p class="welcome-sub">选择知识库后，输入问题即可开始 AI 问答</p>
          </div>

          <MessageBubble
            v-for="msg in chatStore.messages"
            :key="msg.id"
            :msg="msg"
          />
        </div>
      </section>

      <!-- 输入框 -->
      <div class="composer-wrap">
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

    <!-- 原文溯源右侧查看抽屉（全局单例） -->
    <CitationViewerDrawer />
  </div>
</template>

<style scoped>
.chat-layout {
  display: flex;
  height: 100%;
  overflow: hidden;
}

/* ===== 会话侧栏 ===== */
.sidebar {
  width: 244px;
  flex-shrink: 0;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  padding: 20px 14px 16px;
  overflow: hidden;
}

.side-head { padding: 0 4px; }
.side-eyebrow {
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.new-chat {
  margin-top: 14px;
  width: 100%;
  height: 42px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-family: var(--font-display);
  font-size: 13.5px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  box-shadow: var(--shadow-neon);
  transition: background 0.15s, transform 0.15s;
}
.new-chat:hover { background: var(--accent-hover); transform: translateY(-1px); }
.new-chat svg { width: 16px; height: 16px; }

.conv-group-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.03em;
  padding: 18px 8px 8px;
}
.conv-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.conv {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 9px 10px;
  border-radius: 9px;
  cursor: pointer;
  color: var(--text-muted);
  transition: background 0.13s, color 0.13s, box-shadow 0.13s;
  border: 1px solid transparent;
  min-width: 0;
}
.conv .ico { width: 15px; height: 15px; flex-shrink: 0; opacity: 0.75; }
.conv .title {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.005em;
}
.conv:hover { background: var(--bg-card); color: var(--text-secondary); box-shadow: var(--shadow-glass); }
.conv.active {
  background: var(--bg-card);
  color: var(--text-primary);
  border-color: var(--border-strong);
  box-shadow: var(--shadow-glass);
}
.conv.active .ico { color: var(--accent); opacity: 1; }
.conv.active .title { font-weight: 600; }
.conv .del {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  display: none;
  place-items: center;
  color: var(--text-muted);
  flex-shrink: 0;
  background: transparent;
  border: none;
  cursor: pointer;
}
.conv .del svg { width: 14px; height: 14px; }
.conv:hover .del { display: grid; }
.conv .del:hover { background: #FBEAEA; color: #D14343; }
.conv-empty {
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
  padding: 24px 0;
}

.side-foot { margin-top: auto; padding-top: 14px; border-top: 1px solid var(--border-subtle); }
.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 10px;
}
.user-chip .avatar {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  flex-shrink: 0;
  background: linear-gradient(135deg, #E3E0FB, #CFC9F8);
  color: var(--accent);
  font-family: var(--font-display);
  font-weight: 800;
  font-size: 13px;
  display: grid;
  place-items: center;
}
.user-meta { flex: 1; line-height: 1.3; min-width: 0; }
.user-meta .n {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-meta .r { font-size: 10.5px; color: var(--text-muted); }

/* ===== 主聊天区 ===== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  background: var(--bg-primary);
}

.topbar {
  height: 62px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  padding: 0 26px;
  gap: 14px;
  background: rgba(251, 251, 253, 0.85);
  backdrop-filter: blur(8px);
}
.conv-heading { min-width: 0; }
.conv-title {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.topbar-spacer { flex: 1; }
.no-kb-tip {
  font-size: 12px;
  color: var(--color-warning, #FFB800);
  flex-shrink: 0;
}
.icon-btn {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: 1px solid var(--border-strong);
  background: var(--bg-card);
  display: grid;
  place-items: center;
  color: var(--text-secondary);
  cursor: pointer;
  box-shadow: var(--shadow-glass);
  transition: color 0.15s, border-color 0.15s;
  flex-shrink: 0;
}
.icon-btn svg { width: 18px; height: 18px; }
.icon-btn:hover { color: var(--text-primary); border-color: #CFC9F8; }

/* 消息滚动区 */
.thread {
  flex: 1;
  overflow-y: auto;
  position: relative;
}
.thread-inner {
  max-width: 780px;
  margin: 0 auto;
  padding: 30px 26px 18px;
  display: flex;
  flex-direction: column;
  gap: 26px;
}

/* 欢迎屏 */
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  gap: 14px;
}
.welcome-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: var(--accent-soft);
  border: 1px solid #DCD7FA;
  display: grid;
  place-items: center;
  color: var(--accent);
}
.welcome-icon svg { width: 34px; height: 34px; }
.welcome-title {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.015em;
  color: var(--text-primary);
}
.welcome-sub {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 输入区 */
.composer-wrap {
  flex-shrink: 0;
  padding: 14px 26px 20px;
  background: linear-gradient(0deg, var(--bg-primary) 60%, rgba(251, 251, 253, 0));
}
</style>
