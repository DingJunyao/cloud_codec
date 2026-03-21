<template>
  <div class="settings">
    <h1>设置</h1>

    <div class="settings-section">
      <h2>个人信息</h2>
      <form @submit.prevent="handleProfileUpdate" class="form">
        <div class="field">
          <label>用户名</label>
          <input v-model="profile.username" disabled />
        </div>
        <div class="field">
          <label>邮箱</label>
          <input v-model="profile.email" type="email" />
        </div>
        <button type="submit" :disabled="updating">
          {{ updating ? '保存中...' : '保存' }}
        </button>
      </form>
    </div>

    <div class="settings-section">
      <h2>修改密码</h2>
      <form @submit.prevent="handlePasswordChange" class="form">
        <div class="field">
          <label>当前密码</label>
          <input v-model="passwordForm.old_password" type="password" required />
        </div>
        <div class="field">
          <label>新密码</label>
          <input v-model="passwordForm.new_password" type="password" required />
        </div>
        <div class="field">
          <label>确认新密码</label>
          <input v-model="passwordForm.confirm_password" type="password" required />
        </div>
        <button type="submit" :disabled="changing">
          {{ changing ? '修改中...' : '修改密码' }}
        </button>
      </form>
    </div>

    <div v-if="user?.is_admin" class="settings-section">
      <h2>系统设置</h2>
      <div class="admin-links">
        <button @click="$router.push('/admin/users')">用户管理</button>
        <button @click="$router.push('/admin/settings')">系统配置</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const profile = ref({ username: '', email: '' })
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})
const user = ref(null)
const updating = ref(false)
const changing = ref(false)

const handleProfileUpdate = async () => {
  updating.value = true
  try {
    const response = await fetch('/api/users/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify(profile.value)
    })
    if (response.ok) {
      alert('保存成功')
    } else {
      alert('保存失败')
    }
  } catch (error) {
    alert('保存失败: ' + error.message)
  } finally {
    updating.value = false
  }
}

const handlePasswordChange = async () => {
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    alert('两次输入的密码不一致')
    return
  }
  changing.value = true
  try {
    const response = await fetch('/api/users/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({
        old_password: passwordForm.value.old_password,
        new_password: passwordForm.value.new_password
      })
    })
    if (response.ok) {
      alert('密码修改成功')
      passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
    } else {
      const data = await response.json()
      alert('修改失败: ' + (data.detail || '未知错误'))
    }
  } catch (error) {
    alert('修改失败: ' + error.message)
  } finally {
    changing.value = false
  }
}

onMounted(async () => {
  try {
    const response = await fetch('/api/users/me', {
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    user.value = await response.json()
    profile.value = { username: user.value.username, email: user.value.email || '' }
  } catch (error) {
    console.error('加载用户信息失败:', error)
  }
})
</script>

<style scoped>
.settings {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.settings-section {
  margin-bottom: 40px;
  padding: 24px;
  border: 1px solid #eee;
  border-radius: 8px;
}

.settings-section h2 {
  margin-top: 0;
  margin-bottom: 20px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 400px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 14px;
  font-weight: 500;
}

.field input {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.field input:disabled {
  background: #f5f5f5;
  color: #999;
}

.form button {
  padding: 10px 20px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  align-self: flex-start;
}

.form button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.admin-links {
  display: flex;
  gap: 10px;
}

.admin-links button {
  padding: 10px 20px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
