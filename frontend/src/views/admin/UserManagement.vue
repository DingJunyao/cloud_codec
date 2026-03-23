<template>
  <div class="user-management">
    <h1>用户管理</h1>

    <div class="toolbar">
      <input
        v-model="search"
        type="text"
        placeholder="搜索用户名或邮箱"
        @input="handleSearch"
      />
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="user-table">
      <table>
        <thead>
          <tr>
            <th>用户名</th>
            <th>邮箱</th>
            <th>状态</th>
            <th>角色</th>
            <th>任务数</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span :class="['status', user.is_active ? 'active' : 'inactive']">
                {{ user.is_active ? '正常' : '已禁用' }}
              </span>
            </td>
            <td>
              <span :class="['role', user.is_admin ? 'admin' : 'user']">
                {{ user.is_admin ? '管理员' : '用户' }}
              </span>
            </td>
            <td>{{ user.task_count || 0 }}</td>
            <td>{{ formatTime(user.created_at) }}</td>
            <td>
              <button
                v-if="!user.is_admin"
                @click="handleToggleActive(user)"
                :class="['btn', user.is_active ? 'btn-danger' : 'btn-success']"
              >
                {{ user.is_active ? '禁用' : '启用' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="users.length === 0" class="empty">
        <p>暂无用户数据</p>
      </div>

      <div class="pagination">
        <button @click="prevPage" :disabled="page === 0">上一页</button>
        <span>第 {{ page + 1 }} 页</span>
        <button @click="nextPage" :disabled="users.length < pageSize">下一页</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/datetime'
import { confirm } from '@/utils/message'

interface User {
  id: string
  username: string
  email: string
  is_active: boolean
  is_admin: boolean
  task_count: number
  created_at: string
}

const authStore = useAuthStore()
const users = ref<User[]>([])
const loading = ref(true)
const search = ref('')
const page = ref(0)
const pageSize = 20

const formatTime = (time: string) => formatDateTime(time)

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      skip: String(page.value * pageSize),
      limit: String(pageSize)
    })
    if (search.value) {
      params.append('search', search.value)
    }

    const response = await fetch(`/api/admin/users?${params}`, {
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    users.value = await response.json()
  } catch (err) {
    console.error('获取用户列表失败:', err)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 0
  fetchUsers()
}

const handleToggleActive = async (user: User) => {
  if (!await confirm(`确定要${user.is_active ? '禁用' : '启用'}用户 ${user.username} 吗？`)) {
    return
  }

  try {
    const response = await fetch(`/api/admin/users/${user.id}/toggle-active`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    const data = await response.json()
    user.is_active = data.user.is_active
  } catch (err) {
    console.error('操作失败:', err)
  }
}

const prevPage = () => {
  if (page.value > 0) {
    page.value--
    fetchUsers()
  }
}

const nextPage = () => {
  page.value++
  fetchUsers()
}

onMounted(fetchUsers)
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.user-management h1 {
  margin-bottom: 20px;
}

.toolbar {
  margin-bottom: 20px;
}

.toolbar input {
  width: 300px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.user-table {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background: #f5f5f5;
  font-weight: 600;
  font-size: 14px;
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status.active {
  background: #f6ffed;
  color: #52c41a;
}

.status.inactive {
  background: #fff1f0;
  color: #ff4d4f;
}

.role {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.role.admin {
  background: #fff7e6;
  color: #fa8c16;
}

.role.user {
  background: #f0f0f0;
  color: #666;
}

.btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn-danger {
  background: #ff4d4f;
  color: white;
}

.btn-success {
  background: #52c41a;
  color: white;
}

.loading, .empty {
  text-align: center;
  padding: 60px;
  color: #666;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-top: 1px solid #eee;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
}

.pagination button:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}
</style>
