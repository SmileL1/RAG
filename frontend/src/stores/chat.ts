import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Citation, Conversation, Message } from '@/api/types'

export interface ChatMessageView {
  id: string | number
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  streaming?: boolean
  error?: string
}

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Conversation[]>([])
  const currentConvId = ref<number | null>(null)
  const messages = ref<ChatMessageView[]>([])
  const sending = ref(false)

  function reset() {
    messages.value = []
    currentConvId.value = null
  }

  function pushMessage(m: ChatMessageView) {
    messages.value = [...messages.value, m]
  }

  function updateLast(patch: Partial<ChatMessageView>) {
    if (messages.value.length === 0) return
    const last = messages.value[messages.value.length - 1]
    messages.value = [
      ...messages.value.slice(0, -1),
      { ...last, ...patch },
    ]
  }

  function appendToLast(token: string) {
    if (messages.value.length === 0) return
    const last = messages.value[messages.value.length - 1]
    messages.value = [
      ...messages.value.slice(0, -1),
      { ...last, content: (last.content || '') + token },
    ]
  }

  return {
    conversations,
    currentConvId,
    messages,
    sending,
    reset,
    pushMessage,
    updateLast,
    appendToLast,
  }
})

export type { Message }
