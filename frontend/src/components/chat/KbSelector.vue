<script setup lang="ts">
import { computed } from 'vue'
import { NSelect } from 'naive-ui'
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
    <span class="label">📚 当前知识库</span>
    <NSelect
      v-model:value="value"
      :options="options"
      placeholder="选择一个知识库"
      size="small"
      style="width: 200px"
    />
  </div>
</template>

<style scoped>
.selector {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.label {
  color: var(--text-secondary);
}
</style>
