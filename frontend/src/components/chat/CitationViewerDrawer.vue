<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useCitationViewer } from '@/composables/useCitationViewer'
import { docApi } from '@/api/documents'

const { state, close } = useCitationViewer()

const bodyRef = ref<HTMLElement | null>(null)
const hitRef = ref<HTMLElement | null>(null)

// 把片段按顺序拼成连续原文，并把「整个命中段」完整高亮（不做易误判的去重叠）
const docParts = computed(() => {
  let before = ''
  let hit = ''
  let after = ''
  let passedHit = false
  for (const ck of state.chunks) {
    if (ck.chunk_idx === state.targetIdx) {
      hit = ck.content
      passedHit = true
      continue
    }
    if (!passedHit) before += ck.content + '\n'
    else after += '\n' + ck.content
  }
  return { before, hit, after }
})

// 加载完成后滚动到高亮处
watch(
  () => [state.open, state.loading, state.chunks.length],
  async () => {
    if (!state.open || state.loading) return
    await nextTick()
    const body = bodyRef.value
    const hit = hitRef.value
    if (body && hit) body.scrollTop = Math.max(0, hit.offsetTop - 90)
  },
)

async function downloadRaw() {
  if (!state.citation) return
  try {
    const url = await docApi.rawBlobUrl(state.citation.doc_id)
    window.open(url, '_blank')
    setTimeout(() => URL.revokeObjectURL(url), 60000)
  } catch {
    /* 文件可能已从磁盘删除，忽略 */
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="state.open" class="cv-root">
        <div class="cv-mask" @click="close" />
        <aside class="cv-panel">
          <header class="cv-head">
            <div class="cv-title-wrap">
              <div class="cv-eyebrow">原文溯源 · 完整文档</div>
              <div class="cv-fn">《{{ state.citation?.filename }}》</div>
              <div class="cv-meta">
                <template v-if="state.citation?.page != null">第 {{ state.citation?.page }} 页<span class="sep">·</span></template>
                命中段落 #{{ state.citation?.chunk_idx }}<span class="sep">·</span>黄色高亮为命中处
              </div>
            </div>
            <div class="cv-head-actions">
              <button class="cv-raw" title="在新标签打开/下载原始文件" @click="downloadRaw">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                下载原文件
              </button>
              <button class="cv-close" title="关闭" @click="close">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
          </header>

          <div ref="bodyRef" class="cv-body">
            <div v-if="state.loading" class="cv-state">正在加载完整文档…</div>
            <template v-else>
              <p v-if="state.error" class="cv-warn">⚠ {{ state.error }}（已回退显示命中片段）</p>
              <div class="cv-legend">
                <span class="cv-legend-swatch" />
                <span>黄色高亮部分为本次回答引用的<b>命中内容</b></span>
              </div>
              <div class="cv-doc">{{ docParts.before }}<mark v-if="docParts.hit" ref="hitRef" class="hl">{{ docParts.hit }}</mark>{{ docParts.after }}</div>
            </template>
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.cv-root { position: fixed; inset: 0; z-index: 2000; }
.cv-mask {
  position: absolute;
  inset: 0;
  background: rgba(20, 22, 27, 0.32);
  backdrop-filter: blur(2px);
}
.cv-panel {
  position: absolute;
  top: 0;
  right: 0;
  height: 100%;
  width: 680px;
  max-width: 94vw;
  background: var(--bg-card);
  border-left: 1px solid var(--border-strong);
  box-shadow: -12px 0 36px rgba(20, 22, 27, 0.16);
  display: flex;
  flex-direction: column;
}

.cv-head {
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 20px 22px 16px;
  border-bottom: 1px solid var(--border-subtle);
}
.cv-title-wrap { flex: 1; min-width: 0; }
.cv-eyebrow {
  font-family: var(--font-display);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
}
.cv-fn {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin-top: 4px;
  letter-spacing: -0.01em;
  word-break: break-all;
}
.cv-meta { font-size: 12px; color: var(--text-muted); margin-top: 4px; font-variant-numeric: tabular-nums; }
.cv-meta .sep { margin: 0 6px; opacity: 0.5; }

.cv-head-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.cv-raw {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--border-strong);
  background: var(--bg-card);
  color: var(--text-secondary);
  padding: 7px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
  white-space: nowrap;
}
.cv-raw svg { width: 14px; height: 14px; }
.cv-raw:hover { border-color: var(--accent); color: var(--accent); }
.cv-close {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-card);
  color: var(--text-secondary);
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  flex-shrink: 0;
}
.cv-close svg { width: 16px; height: 16px; }
.cv-close:hover { background: var(--bg-secondary); color: var(--text-primary); }

.cv-body {
  flex: 1;
  overflow-y: auto;
  padding: 18px 22px 28px;
}
.cv-state { color: var(--text-muted); font-size: 13px; padding: 24px 0; text-align: center; }
.cv-warn { font-size: 12px; color: var(--color-warning); margin: 0 0 10px; }

.cv-legend {
  position: sticky;
  top: -18px;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: -4px 0 14px;
  padding: 9px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: 9px;
  font-size: 12px;
  color: var(--text-secondary);
}
.cv-legend b { color: var(--text-primary); font-weight: 700; }
.cv-legend-swatch {
  width: 22px;
  height: 14px;
  border-radius: 3px;
  flex-shrink: 0;
  background: #FFE680;
  border: 1px solid #F2C94C;
}

/* 完整文档：连续阅读，命中文字内联荧光高亮 */
.cv-doc {
  font-size: 13.5px;
  line-height: 1.9;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}
.cv-doc .hl {
  background: linear-gradient(180deg, transparent 8%, #FFE680 8%, #FFE680 92%, transparent 92%);
  color: var(--text-primary);
  font-weight: 500;
  padding: 0 1px;
  border-radius: 2px;
  scroll-margin-top: 90px;
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
}

/* 抽屉动画 */
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.2s ease; }
.drawer-enter-active .cv-panel, .drawer-leave-active .cv-panel { transition: transform 0.24s cubic-bezier(0.22, 1, 0.36, 1); }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from .cv-panel, .drawer-leave-to .cv-panel { transform: translateX(100%); }
</style>
