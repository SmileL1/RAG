import { http } from './client'
import type { Document } from './types'

export interface ChunkContextItem {
  chunk_idx: number
  content: string
  is_hit: boolean
}
export interface ChunkContext {
  filename: string
  doc_id: number
  target_idx: number
  chunks: ChunkContextItem[]
}

export interface DocChunk {
  chunk_idx: number
  content: string
}
export interface DocChunks {
  filename: string
  doc_id: number
  chunks: DocChunk[]
}

export const docApi = {
  list: (kbId: number) =>
    http.get<Document[]>(`/kb/${kbId}/documents`).then((r) => r.data),

  get: (id: number) =>
    http.get<Document>(`/documents/${id}`).then((r) => r.data),

  status: (id: number) =>
    http.get<Document>(`/documents/${id}/status`).then((r) => r.data),

  text: (id: number) =>
    http
      .get<{ filename: string; content: string; chunk_count: number }>(`/documents/${id}/text`)
      .then((r) => r.data),

  chunkContext: (id: number, idx: number, window = 1) =>
    http
      .get<ChunkContext>(`/documents/${id}/chunk-context`, { params: { idx, window } })
      .then((r) => r.data),

  chunks: (id: number) =>
    http.get<DocChunks>(`/documents/${id}/chunks`).then((r) => r.data),

  /** 以带鉴权的 fetch 下载原始文件并返回 Blob URL（调用方负责 revokeObjectURL）。 */
  rawBlobUrl: async (id: number): Promise<string> => {
    const token = localStorage.getItem('rag_token') ?? ''
    const resp = await fetch(`/api/documents/${id}/raw`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!resp.ok) throw new Error('获取文件失败')
    const blob = await resp.blob()
    return URL.createObjectURL(blob)
  },

  upload: async (kbId: number, file: File, onProgress?: (pct: number) => void) => {
    const fd = new FormData()
    fd.append('file', file)
    const resp = await http.post<Document>(`/kb/${kbId}/documents`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total && onProgress) onProgress(Math.round((e.loaded / e.total) * 100))
      },
    })
    return resp.data
  },

  retry: (id: number) =>
    http.post<Document>(`/documents/${id}/retry`).then((r) => r.data),

  remove: (id: number) =>
    http.delete<{ message: string }>(`/documents/${id}`).then((r) => r.data),
}
