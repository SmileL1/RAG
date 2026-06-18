<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  disabled?: boolean
  streaming?: boolean
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
  <div class="composer" :class="{ disabled }">
    <textarea
      v-model="text"
      :placeholder="placeholder ?? '问点什么…（Enter 发送，Shift+Enter 换行）'"
      :disabled="streaming || disabled"
      rows="1"
      class="composer-input"
      @keydown="onKeydown"
    />
    <div class="composer-bar">
      <div class="comp-spacer" />
      <div class="comp-hint">
        <kbd>Enter</kbd> 发送<span class="dot">·</span><kbd>Shift</kbd>+<kbd>Enter</kbd> 换行
      </div>
      <button
        v-if="streaming"
        class="send-btn abort"
        title="停止生成"
        @click="emit('abort')"
      >
        <svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
      </button>
      <button
        v-else
        class="send-btn"
        :disabled="disabled || !text.trim()"
        title="发送"
        @click="send"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.composer {
  max-width: 780px;
  margin: 0 auto;
  background: var(--bg-card);
  border: 1px solid var(--border-strong);
  border-radius: 16px;
  box-shadow: var(--shadow-pop);
  padding: 14px 14px 11px;
  transition: border-color 0.18s, box-shadow 0.18s;
}
.composer:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-ring), var(--shadow-pop);
}
.composer.disabled { opacity: 0.7; }

.composer-input {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  resize: none;
  font-family: var(--font-body);
  font-size: 14.5px;
  line-height: 1.6;
  color: var(--text-primary);
  letter-spacing: -0.003em;
  min-height: 24px;
  max-height: 200px;
}
.composer-input::placeholder { color: var(--text-muted); }
.composer-input:disabled { cursor: not-allowed; }

.composer-bar {
  display: flex;
  align-items: center;
  margin-top: 11px;
  gap: 10px;
}
.comp-spacer { flex: 1; }
.comp-hint {
  font-size: 11.5px;
  color: var(--text-muted);
}
.comp-hint .dot { margin: 0 6px; opacity: 0.4; }
.comp-hint kbd {
  font-family: var(--font-mono);
  font-size: 10.5px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-strong);
  border-bottom-width: 2px;
  border-radius: 5px;
  padding: 1px 5px;
  color: var(--text-secondary);
  margin: 0 1px;
}

.send-btn {
  width: 42px;
  height: 38px;
  border-radius: 10px;
  border: none;
  background: var(--accent);
  color: #fff;
  display: grid;
  place-items: center;
  cursor: pointer;
  box-shadow: var(--shadow-neon);
  transition: background 0.15s, transform 0.15s, opacity 0.15s;
  flex-shrink: 0;
}
.send-btn svg { width: 18px; height: 18px; }
.send-btn:hover:not(:disabled) { background: var(--accent-hover); transform: translateY(-1px); }
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; box-shadow: none; }
.send-btn.abort {
  background: var(--color-error);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.28);
  animation: pulse-abort 1.5s ease-in-out infinite;
}
.send-btn.abort:hover { background: #DC2626; }
@keyframes pulse-abort {
  0%, 100% { box-shadow: 0 2px 8px rgba(239, 68, 68, 0.25); }
  50% { box-shadow: 0 2px 16px rgba(239, 68, 68, 0.5); }
}
</style>
