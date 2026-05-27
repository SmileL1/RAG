<script setup lang="ts">
import { onMounted, ref } from 'vue'
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

// 可编辑字段的本地副本
const form = ref<SettingsPatch>({})

async function load() {
  loading.value = true
  try {
    const data = await settingsApi.get()
    current.value = data
    form.value = {
      LLM_API_BASE: data.LLM_API_BASE,
      LLM_MODEL: data.LLM_MODEL,
      LLM_TEMPERATURE: data.LLM_TEMPERATURE,
      LLM_MAX_TOKENS: data.LLM_MAX_TOKENS,
      RETRIEVE_TOP_K: data.RETRIEVE_TOP_K,
      RERANK_ENABLED: data.RERANK_ENABLED,
      RERANK_TOP_K: data.RERANK_TOP_K,
      USE_HYDE: data.USE_HYDE,
    }
  } catch (e: unknown) {
    message.error((e as Error).message)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const updated = await settingsApi.patch(form.value)
    current.value = updated
    message.success('已保存（当前进程生效，重启后恢复 .env 值）')
  } catch (e: unknown) {
    message.error((e as Error).message)
  } finally {
    saving.value = false
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
            <label>API 地址</label>
            <input v-model="form.LLM_API_BASE" type="text" placeholder="https://api.deepseek.com/v1" />
          </div>
          <div class="field">
            <label>模型名称</label>
            <input v-model="form.LLM_MODEL" type="text" placeholder="deepseek-chat" />
          </div>
          <div class="field field-half">
            <label>Temperature <span class="field-hint">0~2，越高越随机</span></label>
            <input v-model.number="form.LLM_TEMPERATURE" type="number" min="0" max="2" step="0.1" />
          </div>
          <div class="field field-half">
            <label>Max Tokens <span class="field-hint">最大输出长度</span></label>
            <input v-model.number="form.LLM_MAX_TOKENS" type="number" min="256" max="8192" step="256" />
          </div>
          <div class="field readonly-field">
            <label>LLM 供应商 <span class="badge-ro">只读</span></label>
            <code>{{ current.LLM_PROVIDER }}</code>
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
        <span class="save-hint">修改在当前进程内立即生效，重启后恢复 .env 的值</span>
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
.section-icon { font-size: 20px; color: #2563EB; }

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
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}
.field input:focus { border-color: #2563EB; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1); }

.field-row {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  flex: 1 1 100%;
}

.readonly-field { opacity: 0.6; }
.readonly-field code {
  font-size: 13px;
  background: rgba(37, 99, 235, 0.08);
  color: #2563EB;
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
.toggle-btn.active { background: #2563EB; }
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
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 8px 14px;
}
.ro-label { font-size: 12px; color: var(--text-muted); }
.ro-item code {
  font-size: 12px;
  background: rgba(37,99,235,0.08);
  color: #2563EB;
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
.save-hint { font-size: 12px; color: var(--text-muted); }

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }
</style>
