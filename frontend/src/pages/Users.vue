<script setup lang="ts">
import { h, onMounted, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useMessage } from 'naive-ui'
import { adminApi, type AdminUser } from '@/api/admin'

const message = useMessage()

const users = ref<AdminUser[]>([])
const loading = ref(false)

// 创建用户弹窗
const showCreate = ref(false)
const creating = ref(false)
const createForm = ref({ username: '', password: '', is_admin: false })

// 密码展示弹窗
const showPwdDialog = ref(false)
const pwdDialogTitle = ref('')
const generatedPwd = ref('')

async function load() {
  loading.value = true
  try {
    users.value = await adminApi.listUsers()
  } catch (e: unknown) {
    message.error((e as Error).message)
  } finally {
    loading.value = false
  }
}

async function submitCreate() {
  if (!createForm.value.username.trim()) return
  creating.value = true
  try {
    const result = await adminApi.createUser({
      username: createForm.value.username.trim(),
      password: createForm.value.password || undefined,
      is_admin: createForm.value.is_admin,
    })
    users.value.push(result.user)
    showCreate.value = false
    createForm.value = { username: '', password: '', is_admin: false }
    if (result.generated_password) {
      pwdDialogTitle.value = `用户 "${result.user.username}" 创建成功`
      generatedPwd.value = result.generated_password
      showPwdDialog.value = true
    } else {
      message.success('用户创建成功')
    }
  } catch (e: unknown) {
    message.error((e as Error).message)
  } finally {
    creating.value = false
  }
}

async function toggleActive(user: AdminUser) {
  try {
    const updated = await adminApi.updateUser(user.id, { is_active: !user.is_active })
    const idx = users.value.findIndex((u) => u.id === user.id)
    if (idx !== -1) users.value[idx] = updated
  } catch (e: unknown) {
    message.error((e as Error).message)
  }
}

async function toggleAdmin(user: AdminUser) {
  try {
    const updated = await adminApi.updateUser(user.id, { is_admin: !user.is_admin })
    const idx = users.value.findIndex((u) => u.id === user.id)
    if (idx !== -1) users.value[idx] = updated
  } catch (e: unknown) {
    message.error((e as Error).message)
  }
}

async function resetPwd(user: AdminUser) {
  try {
    const result = await adminApi.resetPassword(user.id)
    pwdDialogTitle.value = `已重置 "${user.username}" 的密码`
    generatedPwd.value = result.generated_password ?? ''
    showPwdDialog.value = true
  } catch (e: unknown) {
    message.error((e as Error).message)
  }
}

async function deleteUser(user: AdminUser) {
  if (!confirm(`确定删除用户 "${user.username}"？此操作不可恢复。`)) return
  try {
    await adminApi.deleteUser(user.id)
    users.value = users.value.filter((u) => u.id !== user.id)
    message.success('已删除')
  } catch (e: unknown) {
    message.error((e as Error).message)
  }
}

function copyPwd() {
  navigator.clipboard.writeText(generatedPwd.value).then(() => message.success('已复制'))
}

function formatDate(s: string) {
  return new Date(s).toLocaleDateString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

onMounted(load)
</script>

<template>
  <div class="users-page">
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <button class="btn-neon create-btn" @click="showCreate = true">
        <Icon icon="ph:plus-bold" />
        创建用户
      </button>
    </div>

    <!-- 用户列表 -->
    <div class="glass-card table-card">
      <div v-if="loading" class="center-hint">加载中…</div>
      <div v-else-if="users.length === 0" class="center-hint">暂无用户</div>
      <table v-else class="user-table">
        <thead>
          <tr>
            <th>用户名</th>
            <th>角色</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td class="col-name">
              <Icon icon="ph:user-circle-duotone" class="user-icon" />
              {{ u.username }}
            </td>
            <td>
              <span class="tag" :class="u.is_admin ? 'tag-admin' : 'tag-user'">
                {{ u.is_admin ? 'Admin' : '普通用户' }}
              </span>
            </td>
            <td>
              <span class="tag" :class="u.is_active ? 'tag-active' : 'tag-inactive'">
                {{ u.is_active ? '启用' : '禁用' }}
              </span>
            </td>
            <td class="col-date">{{ formatDate(u.created_at) }}</td>
            <td class="col-actions">
              <button class="action-btn" @click="toggleActive(u)" :title="u.is_active ? '禁用' : '启用'">
                <Icon :icon="u.is_active ? 'ph:toggle-right-duotone' : 'ph:toggle-left-duotone'" />
              </button>
              <button class="action-btn" @click="toggleAdmin(u)" title="切换管理员">
                <Icon icon="ph:shield-chevron-duotone" />
              </button>
              <button class="action-btn" @click="resetPwd(u)" title="重置密码">
                <Icon icon="ph:key-duotone" />
              </button>
              <button class="action-btn danger" @click="deleteUser(u)" title="删除">
                <Icon icon="ph:trash-duotone" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 创建用户弹窗 -->
    <div v-if="showCreate" class="modal-mask" @click.self="showCreate = false">
      <div class="modal glass-card">
        <h3 class="modal-title">创建用户</h3>

        <div class="field">
          <label>用户名 <span class="required">*</span></label>
          <input v-model="createForm.username" type="text" placeholder="请输入用户名" />
        </div>
        <div class="field">
          <label>密码 <span class="hint-text">（留空则自动生成）</span></label>
          <input v-model="createForm.password" type="text" placeholder="留空自动生成随机密码" />
        </div>
        <div class="field field-row">
          <label>设为管理员</label>
          <button
            class="toggle-btn"
            :class="{ active: createForm.is_admin }"
            @click="createForm.is_admin = !createForm.is_admin"
          >
            <span class="toggle-knob" />
          </button>
        </div>

        <div class="modal-actions">
          <button class="btn-ghost" @click="showCreate = false">取消</button>
          <button
            class="btn-neon"
            :disabled="creating || !createForm.username.trim()"
            @click="submitCreate"
          >
            {{ creating ? '创建中…' : '确认创建' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 密码展示弹窗 -->
    <div v-if="showPwdDialog" class="modal-mask" @click.self="showPwdDialog = false">
      <div class="modal glass-card">
        <h3 class="modal-title">{{ pwdDialogTitle }}</h3>
        <p class="pwd-tip">请妥善保存该密码，关闭后将无法再次查看。</p>
        <div class="pwd-box">
          <code>{{ generatedPwd }}</code>
          <button class="copy-btn" @click="copyPwd">
            <Icon icon="ph:copy-duotone" />
            复制
          </button>
        </div>
        <div class="modal-actions">
          <button class="btn-neon" @click="showPwdDialog = false">我已记录，关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.users-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}
.create-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 10px;
  cursor: pointer;
  border: none;
}

.table-card {
  padding: 0;
  overflow: hidden;
}
.center-hint {
  padding: 40px;
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
}
.user-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.user-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-subtle);
  background: rgba(37, 99, 235, 0.03);
}
.user-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-subtle);
  color: var(--text-primary);
}
.user-table tr:last-child td { border-bottom: none; }
.user-table tr:hover td { background: rgba(37, 99, 235, 0.03); }

.col-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}
.user-icon { font-size: 18px; color: #2563EB; }
.col-date { color: var(--text-muted); font-size: 12px; }
.col-actions { display: flex; gap: 4px; }

.tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
}
.tag-admin   { background: rgba(37,99,235,0.12); color: #2563EB; }
.tag-user    { background: rgba(0,0,0,0.06); color: var(--text-secondary); }
.tag-active  { background: rgba(34,197,94,0.12); color: #16a34a; }
.tag-inactive{ background: rgba(239,68,68,0.10); color: #dc2626; }

.action-btn {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: grid;
  place-items: center;
  font-size: 15px;
  transition: background 0.15s, color 0.15s;
}
.action-btn:hover { background: rgba(37,99,235,0.08); color: #2563EB; }
.action-btn.danger:hover { background: rgba(239,68,68,0.08); color: #dc2626; }

/* ===== Modal ===== */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(2px);
}
.modal {
  width: 400px;
  padding: 28px 28px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.modal-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}
.field input {
  padding: 9px 12px;
  border: 1.5px solid var(--border-subtle);
  border-radius: 8px;
  background: rgba(255,255,255,0.8);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
}
.field input:focus { border-color: #2563EB; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
.required { color: #EF4444; }
.hint-text { font-weight: 400; color: var(--text-muted); font-size: 12px; }

.field-row {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}
.toggle-btn {
  width: 40px;
  height: 22px;
  border-radius: 11px;
  background: var(--border-subtle);
  border: none;
  cursor: pointer;
  position: relative;
  transition: background 0.2s;
  padding: 0;
}
.toggle-btn.active { background: #2563EB; }
.toggle-knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  transition: left 0.2s;
  display: block;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
.toggle-btn.active .toggle-knob { left: 21px; }

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}
.btn-ghost {
  padding: 8px 18px;
  border-radius: 8px;
  border: 1.5px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.btn-ghost:hover { background: rgba(0,0,0,0.04); }
.btn-neon {
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}
.btn-neon:disabled { opacity: 0.4; cursor: not-allowed; }

.pwd-tip { font-size: 13px; color: var(--text-secondary); margin: 0; }
.pwd-box {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(37,99,235,0.06);
  border: 1px solid rgba(37,99,235,0.2);
  border-radius: 8px;
  padding: 12px 14px;
}
.pwd-box code {
  flex: 1;
  font-size: 15px;
  font-weight: 700;
  color: #2563EB;
  letter-spacing: 0.5px;
  word-break: break-all;
}
.copy-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 6px;
  border: none;
  background: #2563EB;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}
.copy-btn:hover { opacity: 0.85; }
</style>
