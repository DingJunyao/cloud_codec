<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-header">
        <h1>注册账号</h1>
        <p>创建您的 CloudCoder 账号</p>
      </div>

      <el-card class="register-card">
        <el-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          label-position="top"
          size="large"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="formData.username" placeholder="3-50 个字符" />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input v-model="formData.email" type="email" placeholder="请输入邮箱" />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input v-model="formData.password" type="password" show-password placeholder="至少 8 个字符" />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input v-model="formData.confirmPassword" type="password" show-password @keyup.enter="handleRegister" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :loading="loading" @click="handleRegister" class="register-btn">
              注册
            </el-button>
          </el-form-item>

          <div class="register-footer">
            <span>已有账号？</span>
            <el-link type="primary" @click="router.push('/login')">立即登录</el-link>
          </div>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)

const formData = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value !== formData.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 100, message: '密码长度在 8 到 100 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

async function handleRegister() {
  try {
    loading.value = true
    await authStore.register(formData.username, formData.email, formData.password)
    ElMessage.success('注册成功')
    router.push('/tasks')
  } catch (error: any) {
    ElMessage.error(error?.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.register-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
  padding: 20px 0;
}

.register-container {
  width: 100%;
  max-width: 400px;
  padding: 20px;
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
  color: #ffffff;

  h1 { font-size: 28px; margin: 0 0 10px 0; }
  p { margin: 0; color: #b0b0b0; }
}

.register-card {
  background-color: #2d2d2d;
  border: 1px solid #404040;

  :deep(.el-card__body) { padding: 30px; }
  :deep(.el-input__wrapper) {
    background-color: #1a1a1a;
    box-shadow: 0 0 0 1px #404040 inset;
  }
}

.register-btn { width: 100%; height: 44px; }
.register-footer { text-align: center; color: #b0b0b0; margin-top: 10px; }
</style>
