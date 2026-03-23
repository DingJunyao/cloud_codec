<template>
  <div class="login-page">
    <div class="login-container">
      <h1>CloudCoder</h1>
      <p class="subtitle">视频转码服务平台</p>

      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="field">
          <label>用户名</label>
          <input v-model="form.username" required autofocus />
        </div>
        <div class="field">
          <label>密码</label>
          <input v-model="form.password" type="password" required />
        </div>
        <button type="submit" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
        <p v-if="error" class="error">{{ error }}</p>
      </form>

      <div class="register-link">
        还没有账号？<a @click="showRegister = true">立即注册</a>
      </div>
    </div>

    <!-- 注册对话框 -->
    <div v-if="showRegister" class="dialog-overlay" @click.self="showRegister = false">
      <div class="dialog">
        <h2>注册账号</h2>
        <form @submit.prevent="handleRegister" class="form">
          <div class="field">
            <label>用户名</label>
            <input v-model="registerForm.username" required />
          </div>
          <div class="field">
            <label>邮箱</label>
            <input v-model="registerForm.email" type="email" required />
          </div>
          <div class="field">
            <label>密码</label>
            <input v-model="registerForm.password" type="password" required />
          </div>
          <div class="field">
            <label>确认密码</label>
            <input v-model="registerForm.confirm" type="password" required />
          </div>
          <div class="actions">
            <button type="button" @click="showRegister = false">取消</button>
            <button type="submit" :disabled="registering">
              {{ registering ? '注册中...' : '注册' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { hashPassword } from '@/utils/crypto'
import { success, error as showError } from '@/utils/message'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({ username: '', password: '' })
const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirm: ''
})
const loading = ref(false)
const registering = ref(false)
const error = ref('')
const showRegister = ref(false)

const handleSubmit = async () => {
  loading.value = true
  error.value = ''
  try {
    await authStore.login(form.value.username, form.value.password)
    router.push('/tasks')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (registerForm.value.password !== registerForm.value.confirm) {
    showError('两次输入的密码不一致')
    return
  }
  registering.value = true
  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: registerForm.value.username,
        email: registerForm.value.email,
        password: hashPassword(registerForm.value.password)
      })
    })
    if (response.ok) {
      success('注册成功，请登录')
      showRegister.value = false
      form.value.username = registerForm.value.username
      registerForm.value = { username: '', email: '', password: '', confirm: '' }
    } else {
      const data = await response.json()
      showError('注册失败: ' + (data.detail || '未知错误'))
    }
  } catch (err) {
    showError('注册失败: ' + err.message)
  } finally {
    registering.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-container {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
  width: 90%;
  max-width: 400px;
}

.login-container h1 {
  text-align: center;
  margin: 0 0 8px 0;
  color: #333;
}

.subtitle {
  text-align: center;
  color: #999;
  margin-bottom: 32px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 14px;
  font-weight: 500;
  color: #666;
}

.field input {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.login-form button {
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  margin-top: 8px;
}

.login-form button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error {
  color: #ff4d4f;
  text-align: center;
  font-size: 14px;
  margin: 0;
}

.register-link {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: #666;
}

.register-link a {
  color: #667eea;
  cursor: pointer;
  text-decoration: underline;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  padding: 32px;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
}

.dialog h2 {
  margin-top: 0;
  margin-bottom: 24px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}

.actions button {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.actions button[type="submit"] {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.actions button[type="button"] {
  background: #f0f0f0;
  color: #666;
}
</style>
