<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Citation } from '@/api/types'
import { useCitationViewer } from '@/composables/useCitationViewer'

const props = defineProps<{ citations: Citation[] }>()
const open = ref(false) // 默认折叠，避免回答过长
const { open: openViewer } = useCitationViewer()

function ext(filename: string): string {
  const m = filename.toLowerCase().match(/\.([a-z0-9]+)$/)
  return m ? m[1] : ''
}
function docKind(filename: string): 'pdf' | 'doc' | 'sheet' | 'web' | 'text' {
  const e = ext(filename)
  if (e === 'pdf') return 'pdf'
  if (e === 'doc' || e === 'docx') return 'doc'
  if (e === 'xls' || e === 'xlsx' || e === 'csv') return 'sheet'
  if (e === 'html' || e === 'htm') return 'web'
  return 'text'
}

// reranker 绝对分校准差（常压到近 0），改用本次结果集内的相对相关度展示
const maxScore = computed(() => {
  const vals = props.citations.map((c) => c.score ?? 0)
  return Math.max(0, ...vals)
})
function relPct(score: number | null): number {
  if (score === null || score === undefined) return 0
  if (maxScore.value <= 0) return 0
  return Math.round((score / maxScore.value) * 100)
}
function relLevel(score: number | null): 'high' | 'mid' | 'low' {
  const p = relPct(score)
  if (p >= 80) return 'high'
  if (p >= 40) return 'mid'
  return 'low'
}
</script>

<template>
  <div v-if="citations.length" class="cite-wrap">
    <button class="cite-head" @click="open = !open">
      <svg class="head-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
      <span class="ct">原文溯源</span>
      <span class="cite-count">{{ citations.length }} 处</span>
      <svg class="caret" :class="{ open }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
    </button>

    <div v-show="open" class="cite-grid">
      <div v-for="(c, i) in citations" :key="i" class="cite" title="点击查看原文" @click="openViewer(c)">
        <div class="cite-top">
          <div class="doc-ico" :class="docKind(c.filename)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          </div>
          <div class="cite-name">
            <div class="fn">《{{ c.filename }}》</div>
            <div class="loc">
              <template v-if="c.page != null">第 {{ c.page }} 页<span class="sep">·</span></template>
              命中段落 #{{ c.chunk_idx }}
            </div>
          </div>
          <div class="rel-block">
            <div class="rel-label">相关度</div>
            <div class="rel-val" :class="relLevel(c.score)">{{ relPct(c.score) }}<span class="pct">%</span></div>
            <div class="rel-bar"><i :class="relLevel(c.score)" :style="{ width: relPct(c.score) + '%' }" /></div>
          </div>
        </div>
        <div class="cite-excerpt">摘录「{{ c.text }}」</div>
        <div class="cite-view">查看原文
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cite-wrap { margin-top: 16px; }
.cite-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 11px;
  width: 100%;
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
}
.head-ico { width: 15px; height: 15px; color: var(--text-secondary); flex-shrink: 0; }
.ct {
  font-family: var(--font-display);
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
  text-transform: uppercase;
}
.cite-count {
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  background: var(--accent-soft);
  padding: 1px 9px;
  border-radius: 20px;
}
.caret {
  width: 14px;
  height: 14px;
  margin-left: auto;
  color: var(--text-muted);
  transition: transform 0.18s;
}
.caret.open { transform: rotate(180deg); }

.cite-grid { display: flex; flex-direction: column; gap: 10px; }
.cite {
  background: var(--bg-card);
  border: 1px solid var(--border-strong);
  border-radius: 12px;
  padding: 13px 15px;
  box-shadow: var(--shadow-glass);
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
}
.cite:hover {
  border-color: var(--border-neon);
  box-shadow: var(--shadow-pop);
  transform: translateY(-1px);
}
.cite-top { display: flex; align-items: center; gap: 11px; margin-bottom: 9px; }
.doc-ico {
  width: 30px;
  height: 36px;
  border-radius: 6px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  background: var(--accent-soft);
  border: 1px solid #DAD5FA;
  color: var(--accent);
}
.doc-ico svg { width: 15px; height: 15px; }
.doc-ico.doc { background: #E4F1FB; border-color: #C7E2F6; color: #1F6FB2; }
.doc-ico.sheet { background: #E6F6EF; border-color: #C6EAD9; color: #0E9F6E; }
.doc-ico.web { background: #FBEEE2; border-color: #F4D9C2; color: #C2691F; }

.cite-name { flex: 1; min-width: 0; }
.fn {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.01em;
}
.loc { font-size: 11px; color: var(--text-muted); margin-top: 2px; font-variant-numeric: tabular-nums; }
.loc .sep { margin: 0 6px; opacity: 0.5; }

.rel-block { flex-shrink: 0; text-align: right; width: 80px; }
.rel-label {
  font-size: 9.5px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 3px;
}
.rel-val {
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  color: var(--color-success);
}
.rel-val .pct { font-size: 10px; margin-left: 1px; opacity: 0.8; }
.rel-val.mid { color: #5B8C2A; }
.rel-val.low { color: var(--text-muted); }
.rel-bar { height: 4px; border-radius: 3px; background: var(--border-strong); margin-top: 6px; overflow: hidden; }
.rel-bar i { display: block; height: 100%; border-radius: 3px; background: linear-gradient(90deg, #27B981, var(--color-success)); }
.rel-bar i.mid { background: linear-gradient(90deg, #9BCB5A, #5B8C2A); }
.rel-bar i.low { background: var(--text-muted); }

.cite-excerpt {
  font-size: 12.5px;
  line-height: 1.62;
  color: var(--text-secondary);
  padding-left: 12px;
  border-left: 2px solid var(--border-strong);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.cite-view {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 9px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--accent);
  opacity: 0;
  transition: opacity 0.15s;
}
.cite-view svg { width: 13px; height: 13px; }
.cite:hover .cite-view { opacity: 1; }
</style>
