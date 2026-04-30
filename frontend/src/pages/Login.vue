<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const showPwd = ref(false)

async function submit() {
  error.value = ''
  if (!username.value.trim() || !password.value) return
  loading.value = true
  try {
    await authStore.login(username.value.trim(), password.value)
    router.replace('/')
  } catch (e: unknown) {
    error.value = (e as Error).message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-bg">
    <div class="login-card glass-card">
      <!-- Logo -->
      <div class="logo">
        <div class="logo-icon brand-gradient">
          <Icon icon="ph:brain-duotone" />
        </div>
        <div>
          <div class="logo-title text-gradient">知识库</div>
          <div class="logo-sub">私有 AI 问答</div>
        </div>
      </div>

      <h2 class="form-title">登录</h2>

      <form class="form" @submit.prevent="submit">
        <div class="field">
          <label>用户名</label>
          <div class="input-wrap">
            <Icon icon="ph:user-duotone" class="field-icon" />
            <input
              v-model="username"
              type="text"
              placeholder="请输入用户名"
              autocomplete="username"
              :disabled="loading"
            />
          </div>
        </div>

        <div class="field">
          <label>密码</label>
          <div class="input-wrap">
            <Icon icon="ph:lock-duotone" class="field-icon" />
            <input
              v-model="password"
              :type="showPwd ? 'text' : 'password'"
              placeholder="请输入密码"
              autocomplete="current-password"
              :disabled="loading"
            />
            <button
              type="button"
              class="eye-btn"
              @click="showPwd = !showPwd"
              tabindex="-1"
            >
              <Icon :icon="showPwd ? 'ph:eye-slash-duotone' : 'ph:eye-duotone'" />
            </button>
          </div>
        </div>

        <p v-if="error" class="error-msg">
          <Icon icon="ph:warning-circle-duotone" /> {{ error }}
        </p>

        <button
          type="submit"
          class="submit-btn btn-neon"
          :disabled="loading || !username.trim() || !password"
        >
          <Icon v-if="loading" icon="ph:spinner-gap-bold" class="spin" />
          <Icon v-else icon="ph:sign-in-bold" />
          {{ loading ? '登录中…' : '登 录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-bg {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  background-image:
    radial-gradient(ellipse 70% 50% at 20% 20%, rgba(37, 99, 235, 0.10) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 80%, rgba(14, 165, 233, 0.08) 0%, transparent 60%);
}

.login-card {
  width: 380px;
  padding: 40px 36px 36px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 14px;
}
.logo-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 24px;
  color: #fff;
  box-shadow: var(--shadow-neon);
  flex-shrink: 0;
}
.logo-title {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.3px;
}
.logo-sub {
  font-size: 12px;
  color: var(--text-muted);
}

.form-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.field-icon {
  position: absolute;
  left: 12px;
  font-size: 16px;
  color: var(--text-muted);
  pointer-events: none;
}
.input-wrap input {
  width: 100%;
  padding: 10px 40px 10px 36px;
  border: 1.5px solid var(--border-subtle);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.8);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
  box-sizing: border-box;
}
.input-wrap input:focus {
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}
.input-wrap input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.eye-btn {
  position: absolute;
  right: 10px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 16px;
  padding: 2px;
  display: grid;
  place-items: center;
}
.eye-btn:hover { color: var(--text-primary); }

.error-msg {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-error, #EF4444);
  background: rgba(239, 68, 68, 0.07);
  padding: 8px 12px;
  border-radius: 8px;
  margin: 0;
}

.submit-btn {
  width: 100%;
  padding: 11px 0;
  font-size: 15px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 10px;
  cursor: pointer;
  border: none;
  margin-top: 4px;
}
.submit-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
.spin {
  animation: spin 0.8s linear infinite;
}
</style>
