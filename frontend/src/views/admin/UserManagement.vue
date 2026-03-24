<template>
  <div class="user-management">
    <div class="header">
      <h2>用户管理</h2>
    </div>

    <div class="toolbar">
      <el-input
        v-model="search"
        placeholder="搜索用户名或邮箱"
        style="width: 300px"
        clearable
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <el-table :data="users" stripe v-loading="loading" row-key="id">
      <el-table-column prop="username" label="用户名" width="150" />
      <el-table-column prop="email" label="邮箱" width="200" />
      <el-table-column label="用户组" width="150">
        <template #default="{ row }">
          <el-button
            v-if="row.group_id"
            link
            type="primary"
            size="small"
            @click="openAssignGroupDialog(row)"
          >
            {{ getGroupName(row.group_id) }}
          </el-button>
          <el-button v-else link type="primary" size="small" @click="openAssignGroupDialog(row)">
            分配
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '正常' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_admin ? 'warning' : 'info'" size="small">
            {{ row.is_admin ? '管理员' : '用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="task_count" label="任务数" width="80" align="center" />
      <el-table-column label="注册时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openAssignGroupDialog(row)">
            用户组
          </el-button>
          <el-button
            v-if="!row.is_admin"
            link
            :type="row.is_active ? 'danger' : 'success'"
            size="small"
            @click="handleToggleActive(row)"
          >
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchUsers"
      />
    </div>

    <!-- 分配用户组对话框 -->
    <el-dialog v-model="assignDialogVisible" title="分配用户组" width="400px">
      <el-select
        v-model="selectedGroupId"
        placeholder="选择用户组"
        style="width: 100%"
        clearable
      >
        <el-option label="无（移除分组）" :value="null" />
        <el-option
          v-for="group in allGroups"
          :key="group.id"
          :label="group.name"
          :value="group.id"
        />
      </el-select>
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAssignGroup" :loading="assigning">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/datetime'
import groupsApi from '@/api/groups'
import type { UserGroup } from '@/api/groups'

interface User {
  id: string
  username: string
  email: string
  is_active: boolean
  is_admin: boolean
  group_id?: string
  task_count: number
  created_at: string
}

const authStore = useAuthStore()
const users = ref<User[]>([])
const loading = ref(true)
const search = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)

const allGroups = ref<UserGroup[]>([])
const assignDialogVisible = ref(false)
const assigning = ref(false)
const selectedGroupId = ref<string | null>(null)
const currentUser = ref<User | null>(null)

const formatTime = (time: string) => formatDateTime(time)

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      skip: String((page.value - 1) * pageSize),
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
    const data = await response.json()
    users.value = data
    // 实际应该从 API 返回 total，这里简化处理
    total.value = data.length < pageSize ? (page.value - 1) * pageSize + data.length : page.value * pageSize + 1
  } catch (err) {
    console.error('获取用户列表失败:', err)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const fetchGroups = async () => {
  try {
    allGroups.value = await groupsApi.list()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '获取用户组失败')
  }
}

const getGroupName = (groupId: string) => {
  const group = allGroups.value.find(g => g.id === groupId)
  return group?.name || '未知'
}

const handleSearch = () => {
  page.value = 1
  fetchUsers()
}

const handleToggleActive = async (user: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要${user.is_active ? '禁用' : '启用'}用户 ${user.username} 吗？`,
      '确认',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )

    const response = await fetch(`/api/admin/users/${user.id}/toggle-active`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })

    if (!response.ok) {
      throw new Error('操作失败')
    }

    const data = await response.json()
    user.is_active = data.user.is_active
    ElMessage.success(data.message)
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '操作失败')
    }
  }
}

const openAssignGroupDialog = (user: User) => {
  currentUser.value = user
  selectedGroupId.value = user.group_id || null
  assignDialogVisible.value = true
}

const handleAssignGroup = async () => {
  if (!currentUser.value) return

  assigning.value = true
  try {
    if (selectedGroupId.value) {
      // 分配用户组
      await groupsApi.assignUser(currentUser.value.id, selectedGroupId.value)
      ElMessage.success('分配成功')
    } else {
      // 移除用户组
      await groupsApi.removeUserGroup(currentUser.value.id)
      ElMessage.success('已移除用户组')
    }

    assignDialogVisible.value = false
    await fetchUsers()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    assigning.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchUsers(), fetchGroups()])
})
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.toolbar {
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}
</style>
