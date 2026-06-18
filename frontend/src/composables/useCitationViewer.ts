import { reactive } from 'vue'
import { docApi, type DocChunk } from '@/api/documents'
import type { Citation } from '@/api/types'

// 全局单例：点击任意引用都弹同一个右侧抽屉，展示完整文档并高亮命中段
const state = reactive({
  open: false,
  loading: false,
  error: '',
  citation: null as Citation | null,
  chunks: [] as DocChunk[],
  targetIdx: -1,
})

async function open(c: Citation) {
  state.open = true
  state.citation = c
  state.targetIdx = c.chunk_idx
  state.loading = true
  state.error = ''
  state.chunks = []
  try {
    const res = await docApi.chunks(c.doc_id)
    state.chunks = res.chunks
  } catch (e: unknown) {
    // 取不到全文时，至少回退展示引用自带的命中片段
    state.error = (e as Error).message || '加载完整文档失败'
    state.chunks = [{ chunk_idx: c.chunk_idx, content: c.text }]
  } finally {
    state.loading = false
  }
}

function close() {
  state.open = false
}

export function useCitationViewer() {
  return { state, open, close }
}
