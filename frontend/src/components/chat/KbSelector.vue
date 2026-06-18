<script setup lang="ts">
import { computed } from 'vue'
import { NSelect } from 'naive-ui'
import { Icon } from '@iconify/vue'
import { useKnowledgeStore } from '@/stores/knowledge'

const kbStore = useKnowledgeStore()

const options = computed(() =>
  kbStore.list.map((k) => ({ label: k.name, value: k.id })),
)

const value = computed({
  get: () => kbStore.currentId,
  set: (v: number | null) => {
    kbStore.currentId = v
  },
})
</script>

<template>
  <div class="selector">
    <div class="kb-dot">
      <Icon icon="ph:stack-duotone" />
    </div>
    <div class="kb-meta">
      <div class="kb-eyebrow">当前知识库</div>
      <NSelect
        v-model:value="value"
        :options="options"
        placeholder="选择一个知识库"
        size="small"
        :consistent-menu-width="false"
        style="width: 190px"
      />
    </div>
  </div>
</template>

<style scoped>
.selector {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px 6px 8px;
  background: var(--bg-card);
  border: 1px solid var(--border-strong);
  border-radius: 12px;
  box-shadow: var(--shadow-glass);
  flex-shrink: 0;
}
.kb-dot {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: var(--accent-soft);
  display: grid;
  place-items: center;
  color: var(--accent);
  font-size: 17px;
  flex-shrink: 0;
}
.kb-meta {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.kb-eyebrow {
  font-size: 9.5px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  padding-left: 2px;
}
</style>
