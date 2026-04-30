import { defineStore } from 'pinia'
import { ref } from 'vue'
import { kbApi } from '@/api/knowledgeBase'
import type { KnowledgeBase, KnowledgeBaseCreate } from '@/api/types'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const list = ref<KnowledgeBase[]>([])
  const currentId = ref<number | null>(null)
  const loading = ref(false)

  async function refresh() {
    loading.value = true
    try {
      list.value = await kbApi.list()
      if (currentId.value === null && list.value.length > 0) {
        currentId.value = list.value[0].id
      }
    } finally {
      loading.value = false
    }
  }

  async function create(payload: KnowledgeBaseCreate) {
    const kb = await kbApi.create(payload)
    list.value = [kb, ...list.value]
    currentId.value = kb.id
    return kb
  }

  async function remove(id: number) {
    await kbApi.remove(id)
    list.value = list.value.filter((k) => k.id !== id)
    if (currentId.value === id) {
      currentId.value = list.value[0]?.id ?? null
    }
  }

  return { list, currentId, loading, refresh, create, remove }
})
