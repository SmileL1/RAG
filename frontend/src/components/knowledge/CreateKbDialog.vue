<script setup lang="ts">
import { ref, watch } from 'vue'
import { NForm, NFormItem, NInput, NModal, useMessage } from 'naive-ui'
import { useKnowledgeStore } from '@/stores/knowledge'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{ 'update:show': [v: boolean]; created: [id: number] }>()

const kbStore = useKnowledgeStore()
const message = useMessage()

const name = ref('')
const description = ref('')
const submitting = ref(false)

watch(
  () => props.show,
  (v) => {
    if (v) {
      name.value = ''
      description.value = ''
    }
  },
)

async function submit() {
  if (!name.value.trim()) {
    message.warning('请输入知识库名称')
    return
  }
  submitting.value = true
  try {
    const kb = await kbStore.create({
      name: name.value.trim(),
      description: description.value.trim() || undefined,
    })
    message.success(`已创建：${kb.name}`)
    emit('update:show', false)
    emit('created', kb.id)
  } catch (e) {
    message.error((e as Error).message || '创建失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <NModal
    :show="show"
    preset="card"
    title="✨ 新建知识库"
    style="width: 480px"
    :bordered="false"
    @update:show="(v: boolean) => emit('update:show', v)"
  >
    <NForm label-placement="top">
      <NFormItem label="名称" required>
        <NInput
          v-model:value="name"
          placeholder="给知识库起个名字，例如：员工手册、产品文档、法律法规"
          maxlength="64"
          show-count
          autofocus
          @keyup.enter="submit"
        />
      </NFormItem>
      <NFormItem label="描述">
        <NInput
          v-model:value="description"
          placeholder="描述这个知识库的用途，方便以后识别（可不填）"
          type="textarea"
          :rows="3"
          maxlength="200"
          show-count
        />
      </NFormItem>
    </NForm>
    <div class="hint">
      💡 创建后会绑定当前 Embedding 模型 · 切换模型需新建知识库
    </div>

    <template #action>
      <div class="footer">
        <button class="cancel-btn" @click="emit('update:show', false)">取消</button>
        <button class="btn-neon" :disabled="submitting" @click="submit">
          {{ submitting ? '创建中…' : '创建知识库' }}
        </button>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.hint {
  margin-top: 6px;
  padding: 10px 14px;
  background: rgba(123, 97, 255, 0.08);
  border-radius: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}
.footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.cancel-btn {
  padding: 8px 20px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
}
.cancel-btn:hover {
  border-color: var(--border-neon);
  color: var(--text-primary);
}
.btn-neon {
  padding: 8px 22px;
  font-size: 13px;
}
.btn-neon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
