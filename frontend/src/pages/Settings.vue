<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useMessage } from 'naive-ui'
import { settingsApi, type AppSettings, type SettingsPatch } from '@/api/settings'
import { authApi } from '@/api/auth'

const message = useMessage()

const loading = ref(false)
const saving = ref(false)
const current = ref<AppSettings | null>(null)

// 改密表单
const pwdForm = ref({ oldPassword: '', newPassword: '', confirmPassword: '' })
const changingPwd = ref(false)

async function changePassword() {
  if (!pwdForm.value.oldPassword || !pwdForm.value.newPassword) {
    message.warning('请填写完整密码信息')
    return
  }
  if (pwdForm.value.newPassword !== pwdForm.value.confirmPassword) {
    message.warning('两次输入的新密码不一致')
    return
  }
  if (pwdForm.value.newPassword.length < 6) {
    message.warning('新密码至少 6 位')
    return
  }
  changingPwd.value = true
  try {
    await authApi.changePassword(pwdForm.value.oldPassword, pwdForm.value.newPassword)
    message.success('密码已修改，下次登录使用新密码')
    pwdForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
  } catch (e: unknown) {
    message.error((e as Error).message)
  } finally {
    changingPwd.value = false
  }
}

// 供应商预设：选中后自动填入对应 API 地址与默认模型
const LLM_PRESETS: Record<string, { label: string; base: string; model: string }> = {
  deepseek: { label: 'DeepSeek', base: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  qwen: { label: '通义千问 (DashScope)', base: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus' },
  kimi: { label: 'Kimi (Moonshot)', base: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k' },
  openai: { label: 'OpenAI', base: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  ollama: { label: 'Ollama 本地', base: 'http://localhost:11434/v1', model: '' },
  custom: { label: '自定义', base: '', model: '' },
}

const providerOptions = computed(() => {
  const opts = Object.entries(LLM_PRESETS).map(([value, p]) => ({ value, label: p.label }))
  const cur = form.value.LLM_PROVIDER
  if (cur && !(cur in LLM_PRESETS)) opts.unshift({ value: cur, label: cur })
  return opts
})

function onProviderChange(e: Event) {
  const value = (e.target as HTMLSelectElement).value
  form.value.LLM_PROVIDER = value
  const preset = LLM_PRESETS[value]
  // 选预设（非自定义）时自动填地址+模型，方便一键切换；仍可手动改
  if (preset && value !== 'custom') {
    form.value.LLM_API_BASE = preset.base
    form.value.LLM_MODEL = preset.model
  }
  if (value === 'ollama') fetchOllamaModels()
}

// ===== Ollama 本地模型 =====
const isOllama = computed(() => {
  const b = form.value.LLM_API_BASE || ''
  return form.value.LLM_PROVIDER === 'ollama' || b.includes('11434') || b.includes('ollama')
})
const ollamaModels = ref<string[]>([])
const ollamaMsg = ref('')
const loadingModels = ref(false)

async function fetchOllamaModels() {
  loadingModels.value = true
  ollamaMsg.value = ''
  try {
    const res = await settingsApi.ollamaModels(form.value.LLM_API_BASE)
    ollamaModels.value = res.models
    ollamaMsg.value = res.message
    // 若当前模型不在列表里，自动选第一个本地模型
    if (res.models.length && !res.models.includes(form.value.LLM_MODEL || '')) {
      form.value.LLM_MODEL = res.models[0]
    }
  } catch (e: unknown) {
    ollamaMsg.value = (e as Error).message
  } finally {
    loadingModels.value = false
  }
}

// 可编辑字段的本地副本
const form = ref<SettingsPatch>({})
// API Key 单独管理：输入框默认空，留空表示不修改；非空才提交
const apiKeyInput = ref('')
const showKey = ref(false)
const testing = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await settingsApi.get()
    current.value = data
    apiKeyInput.value = '' // 不回填明文，仅用占位符展示遮蔽串
    form.value = {
      LLM_PROVIDER: data.LLM_PROVIDER,
      LLM_API_BASE: data.LLM_API_BASE,
      LLM_MODEL: data.LLM_MODEL,
      LLM_TEMPERATURE: data.LLM_TEMPERATURE,
      LLM_MAX_TOKENS: data.LLM_MAX_TOKENS,
      RETRIEVE_TOP_K: data.RETRIEVE_TOP_K,
      RERANK_ENABLED: data.RERANK_ENABLED,
      RERANK_TOP_K: data.RERANK_TOP_K,
      USE_HYDE: data.USE_HYDE,
    }
    if (isOllama.value) fetchOllamaModels()
  } catch (e: unknown) {
    message.error((e as Error).message)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const payload: SettingsPatch = { ...form.value }
    const key = apiKeyInput.value.trim()
    if (key) payload.LLM_API_KEY = key // 仅在填写了新 key 时才提交
    const updated = await settingsApi.patch(payload)
    current.value = updated
    apiKeyInput.value = ''
    message.success('已保存并写入 .env，重启后依然生效')
  } catch (e: unknown) {
    message.error((e as Error).message)
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  testing.value = true
  try {
    const res = await settingsApi.testLlm()
    if (res.ok) {
      message.success(`连接成功${res.reply ? '：' + res.reply : ''}`)
    } else {
      message.error('连接失败：' + res.message)
    }
  } catch (e: unknown) {
    message.error((e as Error).message)
  } finally {
    testing.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="settings-page">
    <div class="page-header">
      <h2 class="page-title">设置</h2>
      <p class="page-sub">标注 <span class="badge-ro">只读</span> 的项需修改 .env 后重启生效</p>
    </div>

    <div v-if="loading" class="center-hint">加载中…</div>

    <template v-else-if="current">
      <!-- LLM 配置 -->
      <div class="section glass-card">
        <div class="section-title">
          <Icon icon="ph:robot-duotone" class="section-icon" />
          LLM 模型
        </div>
        <div class="fields">
          <div class="field">
            <label>供应商 <span class="field-hint">选预设会自动填入地址与默认模型，仍可手动改</span></label>
            <select class="select" :value="form.LLM_PROVIDER" @change="onProviderChange">
              <option v-for="opt in providerOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div class="field">
            <label>API 地址</label>
            <input v-model="form.LLM_API_BASE" type="text" placeholder="https://api.deepseek.com/v1" />
          </div>
          <div class="field">
            <label>
              模型名称
              <span v-if="isOllama" class="field-hint">本机 Ollama 已安装的模型，可直接选</span>
            </label>
            <!-- Ollama：本地模型下拉 + 刷新 -->
            <div v-if="isOllama" class="ollama-row">
              <select v-if="ollamaModels.length" class="select" v-model="form.LLM_MODEL">
                <option v-for="m in ollamaModels" :key="m" :value="m">{{ m }}</option>
              </select>
              <input v-else v-model="form.LLM_MODEL" type="text" placeholder="如 llama3.1 / qwen2.5（或点刷新检测）" />
              <button class="test-btn" :disabled="loadingModels" @click="fetchOllamaModels">
                <Icon :icon="loadingModels ? 'ph:circle-notch-bold' : 'ph:arrows-clockwise-duotone'" :class="{ spin: loadingModels }" />
                {{ loadingModels ? '检测中…' : '刷新' }}
              </button>
            </div>
            <input v-else v-model="form.LLM_MODEL" type="text" placeholder="deepseek-chat" />
            <span v-if="isOllama && ollamaMsg" class="ollama-msg" :class="{ warn: !ollamaModels.length }">{{ ollamaMsg }}</span>
          </div>
          <div class="field">
            <label>
              API Key
              <span class="field-hint">
                <template v-if="isOllama">Ollama 本地无需 Key，留空即可</template>
                <template v-else>{{ current.LLM_API_KEY_SET ? '已设置 ' + current.LLM_API_KEY_MASKED + '，留空则不修改' : '尚未设置' }}</template>
              </span>
            </label>
            <div class="key-wrap">
              <input
                v-model="apiKeyInput"
                :type="showKey ? 'text' : 'password'"
                placeholder="粘贴新的 API Key（sk-...）"
                autocomplete="off"
                spellcheck="false"
              />
              <button class="key-eye" type="button" tabindex="-1" @click="showKey = !showKey" :title="showKey ? '隐藏' : '显示'">
                <Icon :icon="showKey ? 'ph:eye-slash-duotone' : 'ph:eye-duotone'" />
              </button>
            </div>
          </div>
          <div class="field field-half">
            <label>Temperature <span class="field-hint">0~2，越高越随机</span></label>
            <input v-model.number="form.LLM_TEMPERATURE" type="number" min="0" max="2" step="0.1" />
          </div>
          <div class="field field-half">
            <label>Max Tokens <span class="field-hint">最大输出长度</span></label>
            <input v-model.number="form.LLM_MAX_TOKENS" type="number" min="256" max="8192" step="256" />
          </div>
        </div>
      </div>

      <!-- 检索配置 -->
      <div class="section glass-card">
        <div class="section-title">
          <Icon icon="ph:funnel-duotone" class="section-icon" />
          检索 & Rerank
        </div>
        <div class="fields">
          <div class="field field-half">
            <label>向量召回数 (RETRIEVE_TOP_K) <span class="field-hint">Qdrant 粗筛</span></label>
            <input v-model.number="form.RETRIEVE_TOP_K" type="number" min="1" max="50" />
          </div>
          <div class="field field-half">
            <label>Rerank 保留数 (RERANK_TOP_K) <span class="field-hint">进入 LLM 的文档数</span></label>
            <input v-model.number="form.RERANK_TOP_K" type="number" min="1" max="20" />
          </div>
          <div class="field field-row">
            <label>启用 Rerank</label>
            <button
              class="toggle-btn"
              :class="{ active: form.RERANK_ENABLED }"
              @click="form.RERANK_ENABLED = !form.RERANK_ENABLED"
            >
              <span class="toggle-knob" />
            </button>
          </div>
          <div class="field field-row">
            <label>
              启用 HyDE
              <span class="field-hint">先让 LLM 生成假答案再检索，提高召回率，但增加一次 LLM 调用</span>
            </label>
            <button
              class="toggle-btn"
              :class="{ active: form.USE_HYDE }"
              @click="form.USE_HYDE = !form.USE_HYDE"
            >
              <span class="toggle-knob" />
            </button>
          </div>
        </div>
      </div>

      <!-- 只读信息 -->
      <div class="section glass-card">
        <div class="section-title">
          <Icon icon="ph:info-duotone" class="section-icon" />
          基础设施 <span class="badge-ro">只读，修改需重启</span>
        </div>
        <div class="readonly-grid">
          <div class="ro-item">
            <span class="ro-label">Embedding</span>
            <code>{{ current.EMBEDDING_PROVIDER }}</code>
          </div>
          <div class="ro-item">
            <span class="ro-label">向量库模式</span>
            <code>{{ current.QDRANT_MODE }}</code>
          </div>
          <div class="ro-item">
            <span class="ro-label">入库模式</span>
            <code>{{ current.INGEST_MODE }}</code>
          </div>
        </div>
      </div>

      <!-- 保存按钮 -->
      <div class="save-row">
        <button class="btn-neon save-btn" :disabled="saving" @click="save">
          <Icon :icon="saving ? 'ph:circle-notch-bold' : 'ph:floppy-disk-duotone'" :class="{ spin: saving }" />
          {{ saving ? '保存中…' : '保存' }}
        </button>
        <button class="test-btn" :disabled="testing" @click="testConnection">
          <Icon :icon="testing ? 'ph:circle-notch-bold' : 'ph:plug-charging-duotone'" :class="{ spin: testing }" />
          {{ testing ? '测试中…' : '测试连接' }}
        </button>
        <span class="save-hint">保存后即时生效并写入 .env（重启不丢）；测试连接用当前已保存的配置发一次最小调用</span>
      </div>
    </template>

    <!-- 修改密码（不依赖 settings 加载） -->
    <div class="section glass-card">
      <div class="section-title">
        <Icon icon="ph:lock-key-duotone" class="section-icon" />
        修改密码
      </div>
      <div class="fields">
        <div class="field">
          <label>当前密码</label>
          <input v-model="pwdForm.oldPassword" type="password" placeholder="输入当前登录密码" autocomplete="current-password" />
        </div>
        <div class="field field-half">
          <label>新密码 <span class="field-hint">至少 6 位</span></label>
          <input v-model="pwdForm.newPassword" type="password" placeholder="输入新密码" autocomplete="new-password" />
        </div>
        <div class="field field-half">
          <label>确认新密码</label>
          <input v-model="pwdForm.confirmPassword" type="password" placeholder="再次输入新密码" autocomplete="new-password" />
        </div>
      </div>
      <div class="save-row" style="margin-top: 4px;">
        <button class="btn-neon save-btn" :disabled="changingPwd" @click="changePassword">
          <Icon :icon="changingPwd ? 'ph:circle-notch-bold' : 'ph:check-bold'" :class="{ spin: changingPwd }" />
          {{ changingPwd ? '修改中…' : '修改密码' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 720px;
}

.page-header { display: flex; flex-direction: column; gap: 4px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin: 0; }
.page-sub { font-size: 13px; color: var(--text-muted); margin: 0; }

.badge-ro {
  display: inline-block;
  padding: 1px 7px;
  border-radius: 10px;
  background: rgba(107, 114, 144, 0.15);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  vertical-align: middle;
}

.center-hint { padding: 40px; text-align: center; color: var(--text-muted); font-size: 14px; }

.section { padding: 22px 24px; display: flex; flex-direction: column; gap: 16px; }

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}
.section-icon { font-size: 20px; color: #5B4FE8; }

.fields { display: flex; flex-wrap: wrap; gap: 14px; }

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1 1 100%;
}
.field-half { flex: 1 1 calc(50% - 7px); min-width: 200px; }

.field label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.field-hint { font-weight: 400; color: var(--text-muted); font-size: 11px; }

.field input {
  padding: 9px 12px;
  border: 1.5px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}
.field input:focus { border-color: #5B4FE8; box-shadow: 0 0 0 3px rgba(91, 79, 232, 0.1); }

.select {
  padding: 9px 12px;
  border: 1.5px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%239498A4' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 34px;
}
.select:focus { border-color: #5B4FE8; box-shadow: 0 0 0 3px rgba(91, 79, 232, 0.1); }

.ollama-row { display: flex; gap: 10px; align-items: center; }
.ollama-row .select,
.ollama-row input { flex: 1; }
.ollama-msg { font-size: 11.5px; color: var(--color-success); margin-top: 2px; }
.ollama-msg.warn { color: var(--color-warning); }

.key-wrap { position: relative; display: flex; align-items: center; }
.key-wrap input {
  width: 100%;
  padding: 9px 40px 9px 12px;
  border: 1.5px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
  font-family: var(--font-mono);
  outline: none;
}
.key-wrap input:focus { border-color: #5B4FE8; box-shadow: 0 0 0 3px rgba(91, 79, 232, 0.1); }
.key-eye {
  position: absolute;
  right: 8px;
  display: grid;
  place-items: center;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 16px;
  padding: 2px;
}
.key-eye:hover { color: var(--accent); }

.field-row {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  flex: 1 1 100%;
}

.readonly-field { opacity: 0.6; }
.readonly-field code {
  font-size: 13px;
  background: rgba(91, 79, 232, 0.08);
  color: #5B4FE8;
  padding: 4px 10px;
  border-radius: 6px;
  font-family: var(--font-mono);
}

.toggle-btn {
  width: 40px; height: 22px;
  border-radius: 11px;
  background: var(--border-subtle);
  border: none; cursor: pointer;
  position: relative; transition: background 0.2s; padding: 0;
  flex-shrink: 0;
}
.toggle-btn.active { background: #5B4FE8; }
.toggle-knob {
  position: absolute; top: 3px; left: 3px;
  width: 16px; height: 16px;
  border-radius: 50%; background: #fff;
  transition: left 0.2s; display: block;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
.toggle-btn.active .toggle-knob { left: 21px; }

.readonly-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.ro-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 8px 14px;
}
.ro-label { font-size: 12px; color: var(--text-muted); }
.ro-item code {
  font-size: 12px;
  background: rgba(91, 79, 232,0.08);
  color: #5B4FE8;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: var(--font-mono);
}

.save-row {
  display: flex;
  align-items: center;
  gap: 14px;
}
.save-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 22px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 10px;
  cursor: pointer;
  border: none;
  flex-shrink: 0;
}
.save-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.test-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 10px;
  cursor: pointer;
  flex-shrink: 0;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid var(--border-neon);
  transition: background 0.15s, border-color 0.15s;
}
.test-btn:hover:not(:disabled) { background: #E5E2FB; }
.test-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.save-hint { font-size: 12px; color: var(--text-muted); flex: 1 1 100%; }

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }
</style>
