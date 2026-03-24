<template>
  <div class="task-monitor">
    <h1>任务监控</h1>

    <div class="toolbar">
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 150px">
        <el-option value="" label="全部状态" />
        <el-option value="pending" label="等待中" />
        <el-option value="processing" label="处理中" />
        <el-option value="completed" label="已完成" />
        <el-option value="failed" label="失败" />
        <el-option value="cancelled" label="已取消" />
      </el-select>
      <el-select v-model="userFilter" placeholder="全部用户" clearable style="width: 150px">
        <el-option value="" label="全部用户" />
        <el-option v-for="user in users" :key="user.id" :value="user.id" :label="user.username" />
      </el-select>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="task-table">
      <table>
        <thead>
          <tr>
            <th>任务ID</th>
            <th>用户</th>
            <th>源文件</th>
            <th>状态</th>
            <th>进度</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in tasks" :key="task.id">
            <td class="task-id">{{ task.id.slice(0, 8) }}</td>
            <td>{{ task.username || '-' }}</td>
            <td class="file-cell">{{ task.source_file }}</td>
            <td>
              <span :class="['status', task.status]">{{ statusText(task.status) }}</span>
            </td>
            <td>
              <div class="progress-bar">
                <div class="progress" :style="{ width: task.progress + '%' }"></div>
                <span class="progress-text">{{ task.progress }}%</span>
              </div>
            </td>
            <td>{{ formatTime(task.created_at) }}</td>
            <td>
              <el-button size="small" @click="viewTask(task.id)">查看</el-button>
              <el-button
                v-if="task.status === 'processing' || task.status === 'pending'"
                size="small"
                type="warning"
                @click="cancelTask(task.id)"
              >取消</el-button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="pagination">
        <el-button size="small" @click="prevPage" :disabled="page === 1">上一页</el-button>
        <span class="page-info">第 {{ page }} 页，共 {{ total }} 条</span>
        <el-button size="small" @click="nextPage">下一页</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import request from '@/api/request'
import { formatDateTime } from '@/utils/datetime'
import { success, error, confirm, info } from '@/utils/message'
import type { User } from '@/api/auth'

interface TaskItem {
  id: string
  username?: string
  source_file: string
  status: string
  progress: number
  created_at: string
}

const tasks = ref<TaskItem[]>([])
const users = ref<User[]>([])
const loading = ref(true)
const statusFilter = ref('')
const userFilter = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)
let pollInterval: number | null = null

const statusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return map[status] || status
}

const formatTime = (time: string) => formatDateTime(time)

const fetchTasks = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (statusFilter.value) {
      params.append('status', statusFilter.value)
    }
    if (userFilter.value) {
      params.append('user_id', userFilter.value)
    }
    params.append('skip', String((page.value - 1) * pageSize))
    params.append('limit', String(pageSize))

    const response = await request.get('/admin/tasks', { params })
    tasks.value = response.items
    total.value = response.total
  } catch (err) {
    console.error('获取任务失败:', err)
  } finally {
    loading.value = false
  }
}

const fetchUsers = async () => {
  try {
    const response = await request.get('/admin/users')
    users.value = response.items || response
  } catch (err) {
    console.error('获取用户失败:', err)
  }
}

const viewTask = (taskId: string) => {
  info('功能待实现')
}

const cancelTask = async (taskId: string) => {
  if (!await confirm('确定要取消此任务吗？')) return
  try {
    await request.post(`/admin/tasks/${taskId}/cancel`)
    success('任务已取消')
    fetchTasks()
  } catch (err) {
    error('取消失败')
  }
}

const prevPage = () => {
  if (page.value > 1) {
    page.value--
    fetchTasks()
  }
}

const nextPage = () => {
  page.value++
  fetchTasks()
}

onMounted(() => {
  fetchTasks()
  fetchUsers()
  // 每10秒轮询一次
  pollInterval = setInterval(fetchTasks, 10000)
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
})
</script>

<style scoped>
.task-monitor {
  padding: 20px;
}

.task-monitor h1 {
  margin-bottom: 20px;
  color: var(--color-text-primary);
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.task-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--color-bg-card);
  border-radius: 8px;
  overflow: hidden;
}

.task-table th {
  background: var(--el-fill-color-light);
  text-align: left;
  padding: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.task-table td {
  padding: 12px;
  border-bottom: 1px solid var(--color-border-lighter);
  color: var(--color-text-regular);
}

.task-id {
  font-family: monospace;
  font-size: 12px;
}

.file-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status.pending { background: var(--el-fill-color-light); color: var(--color-text-secondary); }
.status.processing { background: rgba(24, 144, 255, 0.15); color: #1890ff; }
.status.completed { background: rgba(82, 196, 26, 0.15); color: #52c41a; }
.status.failed { background: rgba(255, 77, 79, 0.15); color: #ff4d4f; }
.status.cancelled { background: var(--el-fill-color); color: var(--color-text-secondary); }

.progress-bar {
  width: 100px;
  height: 16px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  position: relative;
}

.progress {
  height: 100%;
  background: #1890ff;
  border-radius: 4px;
  transition: width 0.3s;
}

.progress-text {
  position: absolute;
  right: 8px;
  top: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.loading {
  text-align: center;
  padding: 60px;
  color: var(--color-text-secondary);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  border-top: 1px solid var(--color-border-lighter);
  padding: 10px;
}

.page-info {
  color: var(--color-text-secondary);
  font-size: 14px;
}

html.dark .task-table th {
  background: var(--el-fill-color);
}

html.dark .task-table td {
  border-bottom-color: var(--color-border);
}

html.dark .progress-bar {
  background: var(--el-fill-color);
}
</style>
