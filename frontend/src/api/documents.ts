import { http } from './client'
import type { Document } from './types'

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

  remove: (id: number) =>
    http.delete<{ message: string }>(`/documents/${id}`).then((r) => r.data),
}
