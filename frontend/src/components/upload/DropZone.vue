<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'

const props = defineProps<{ accept?: string }>()
const emit = defineEmits<{ files: [files: File[]] }>()

const dragOver = ref(false)
const inputEl = ref<HTMLInputElement | null>(null)

function onDragOver(e: DragEvent) {
  e.preventDefault()
  dragOver.value = true
}
function onDragLeave() {
  dragOver.value = false
}
function onDrop(e: DragEvent) {
  e.preventDefault()
  dragOver.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  if (files.length) emit('files', files)
}
function onPick() {
  inputEl.value?.click()
}
function onChange(e: Event) {
  const t = e.target as HTMLInputElement
  const files = Array.from(t.files || [])
  if (files.length) emit('files', files)
  t.value = ''
}
</script>

<template>
  <div
    class="dropzone glass-card glass-card-neon"
    :class="{ dragging: dragOver }"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
    @click="onPick"
  >
    <input
      ref="inputEl"
      type="file"
      multiple
      :accept="props.accept ?? '.pdf,.docx,.md,.txt,.html'"
      hidden
      @change="onChange"
    />
    <div class="icon">
      <Icon icon="ph:cloud-arrow-up-duotone" />
    </div>
    <div class="big">把文件拖到这里，或点击选择</div>
    <div class="small">
      支持 PDF · Word · Markdown · TXT · HTML &nbsp;|&nbsp; 单文件最大 100MB
    </div>
  </div>
</template>

<style scoped>
.dropzone {
  padding: 64px 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s ease;
}
.dropzone:hover,
.dropzone.dragging {
  background: rgba(123, 97, 255, 0.08);
  transform: scale(1.005);
}
.dropzone.dragging {
  box-shadow: 0 0 48px rgba(123, 97, 255, 0.4);
}
.icon {
  font-size: 64px;
  margin-bottom: 16px;
  background: var(--brand-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.big {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}
.small {
  font-size: 13px;
  color: var(--text-secondary);
}
</style>
