<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'

const props = defineProps<{
  disabled?: boolean   // 无知识库时禁用发送
  streaming?: boolean  // 正在流式生成
  placeholder?: string
}>()
const emit = defineEmits<{ submit: [text: string]; abort: [] }>()

const text = ref('')

function send() {
  const v = text.value.trim()
  if (!v || props.disabled || props.streaming) return
  emit('submit', v)
  text.value = ''
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    send()
  }
}
</script>

<template>
  <div class="input-wrap glass-card glass-card-neon">
    <textarea
      v-model="text"
      :placeholder="placeholder ?? '问点什么…（Enter 发送，Shift+Enter 换行）'"
      :disabled="streaming"
      rows="1"
      @keydown="onKeydown"
    />
    <div class="actions">
      <!-- 流式生成中：显示中止按钮 -->
      <button
        v-if="streaming"
        class="abort"
        @click="emit('abort')"
        title="停止生成"
      >
        <Icon icon="ph:stop-fill" />
      </button>
      <!-- 正常状态：显示发送按钮 -->
      <button
        v-else
        class="send"
        :disabled="disabled || !text.trim()"
        @click="send"
        title="发送"
      >
        <Icon icon="ph:paper-plane-tilt-fill" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.input-wrap {
  display: flex;
  align-items: flex-end;
  padding: 12px 14px;
  gap: 10px;
  background: rgba(255, 255, 255, 0.95);
}
textarea {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  max-height: 200px;
  min-height: 24px;
  font-family: inherit;
}
textarea::placeholder {
  color: var(--text-muted);
}
textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.actions {
  display: flex;
  gap: 8px;
}
.send,
.abort {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  border: none;
  cursor: pointer;
  display: grid;
  place-items: center;
  font-size: 16px;
  color: #fff;
  background: var(--brand-gradient);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
  transition: opacity 0.2s, transform 0.2s, box-shadow 0.2s;
}
.send:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  box-shadow: none;
}
.send:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.38);
}
.abort {
  background: linear-gradient(135deg, #EF4444, #F97316);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.25);
  animation: pulse-abort 1.5s ease-in-out infinite;
}
.abort:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.4);
}

@keyframes pulse-abort {
  0%, 100% { box-shadow: 0 2px 8px rgba(239, 68, 68, 0.25); }
  50% { box-shadow: 0 2px 16px rgba(239, 68, 68, 0.50); }
}
</style>
