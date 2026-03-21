<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1>码上转</h1>
        <p>CloudCoder - 视频转码服务</p>
      </div>

      <el-card class="login-card">
        <el-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          label-position="top"
          size="large"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="formData.username" placeholder="请输入用户名" />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input v-model="formData.password" type="password" show-password @keyup.enter="handleLogin" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :loading="loading" @click="handleLogin" class="login-btn">
              登录
            </el-button>
          </el-form-item>

          <div class="login-footer">
            <span>还没有账号？</span>
            <el-link type="primary" @click="router.push('/register')">立即注册</el-link>
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
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  try {
    loading.value = true
    await authStore.login(formData.username, formData.password)
    ElMessage.success('登录成功')
    router.push('/tasks')
  } catch (error: any) {
    ElMessage.error(error?.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
}

.login-container {
  width: 100%;
  max-width: 400px;
  padding: 20px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
  color: #ffffff;

  h1 {
    font-size: 36px;
    margin: 0 0 10px 0;
    background: linear-gradient(45deg, #409eff, #67c23a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  p { margin: 0; color: #b0b0b0; }
}

.login-card {
  background-color: #2d2d2d;
  border: 1px solid #404040;

  :deep(.el-card__body) { padding: 30px; }
  :deep(.el-input__wrapper) {
    background-color: #1a1a1a;
    box-shadow: 0 0 0 1px #404040 inset;
  }
}

.login-btn { width: 100%; height: 44px; }
.login-footer { text-align: center; color: #b0b0b0; margin-top: 10px; }
</style>
