import { http } from './client'
import type { KnowledgeBase, KnowledgeBaseCreate } from './types'

export const kbApi = {
  list: () => http.get<KnowledgeBase[]>('/kb').then((r) => r.data),
  get: (id: number) => http.get<KnowledgeBase>(`/kb/${id}`).then((r) => r.data),
  create: (payload: KnowledgeBaseCreate) =>
    http.post<KnowledgeBase>('/kb', payload).then((r) => r.data),
  update: (id: number, payload: Partial<KnowledgeBaseCreate>) =>
    http.patch<KnowledgeBase>(`/kb/${id}`, payload).then((r) => r.data),
  remove: (id: number) =>
    http.delete<{ message: string }>(`/kb/${id}`).then((r) => r.data),
}
