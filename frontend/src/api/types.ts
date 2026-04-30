// 与后端 schemas 对齐的 TS 类型

export interface KnowledgeBase {
  id: number
  name: string
  description: string | null
  embedding_model: string
  embedding_dim: number
  created_at: string
  updated_at: string
}

export interface KnowledgeBaseCreate {
  name: string
  description?: string
}

export type DocumentStatus = 'pending' | 'processing' | 'ready' | 'failed'

export interface Document {
  id: number
  kb_id: number
  filename: string
  file_size: number
  mime_type: string | null
  status: DocumentStatus
  error_message: string | null
  chunk_count: number
  processed_at: string | null
  created_at: string
  updated_at: string
}

export interface Citation {
  doc_id: number
  filename: string
  page: number | null
  chunk_idx: number
  text: string
  score: number | null
}

export interface ChatRequest {
  kb_id: number
  question: string
  conversation_id?: number | null
  use_hyde?: boolean | null
}

export interface Conversation {
  id: number
  kb_id: number | null
  title: string | null
  created_at: string
  updated_at: string
}

export interface Message {
  id: number
  conversation_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  citations: Citation[] | null
  tokens_used: number | null
  created_at: string
  updated_at: string
}
