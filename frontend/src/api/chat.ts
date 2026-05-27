import { http } from './client'
import type { ChatRequest, Citation, Conversation, Message } from './types'

/* ===== SSE 事件类型 ===== */
export type ChatStreamEvent =
  | { type: 'meta'; conversation_id: number; user_message_id: number }
  | { type: 'token'; content: string }
  | { type: 'citation'; citations: Citation[] }
  | { type: 'done'; message_id: number; conversation_id: number; chunks_used: number }
  | { type: 'error'; message: string }

/**
 * 流式问答（SSE）。返回 AsyncIterable，调用方 `for await` 消费每个事件。
 *
 * 用 fetch + ReadableStream 自己实现 SSE 解析（依赖更轻、可中止）。
 */
export async function* streamChat(
  payload: ChatRequest,
  signal?: AbortSignal,
): AsyncGenerator<ChatStreamEvent, void, unknown> {
  const token = localStorage.getItem('rag_token')
  const resp = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
    signal,
  })
  if (!resp.ok || !resp.body) {
    const text = await resp.text().catch(() => '')
    throw new Error(`SSE 连接失败 ${resp.status} ${text}`)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // SSE 帧以 \n\n 分隔
    let sepIdx: number
    while ((sepIdx = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, sepIdx)
      buffer = buffer.slice(sepIdx + 2)
      const ev = parseSseFrame(frame)
      if (ev) yield ev
    }
  }
}

function parseSseFrame(frame: string): ChatStreamEvent | null {
  let event = 'message'
  const dataLines: string[] = []
  for (const line of frame.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
  }
  if (!dataLines.length) return null
  try {
    const data = JSON.parse(dataLines.join('\n'))
    return { type: event, ...data } as ChatStreamEvent
  } catch {
    return null
  }
}

/* ===== 普通 REST ===== */

export const chatApi = {
  conversations: (kbId?: number) =>
    http
      .get<Conversation[]>('/chat/conversations', { params: kbId ? { kb_id: kbId } : {} })
      .then((r) => r.data),
  messages: (convId: number) =>
    http.get<Message[]>(`/chat/conversations/${convId}/messages`).then((r) => r.data),
  removeConversation: (id: number) =>
    http.delete<{ message: string }>(`/chat/conversations/${id}`).then((r) => r.data),
}
