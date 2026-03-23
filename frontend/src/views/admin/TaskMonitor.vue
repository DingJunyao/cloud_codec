<template>
  <div class="task-monitor">
    <h1>任务监控</h1>

    <div class="toolbar">
      <select v-model="statusFilter">
        <option value="">全部状态</option>
        <option value="pending">等待中</option>
        <option value="processing">处理中</option>
        <option value="completed">已完成</option>
        <option value="failed">失败</option>
        <option value="cancelled">已取消</option>
      </select>
      <select v-model="userFilter">
        <option value="">全部用户</option>
        <option v-for="user in users" :key="user.id" :value="user.id">
          {{ user.username }}
        </option>
      </select>
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
              <button @click="viewTask(task.id)" class="btn">查看</button>
              <button
                v-if="task.status === 'processing'"
                @click="cancelTask(task.id)"
                class="btn btn-danger"
              >
                取消
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination">
      <button @click="prevPage" :disabled="page === 1">上一页</button>
      <span>第 {{ page }} 页， 共 {{ total }} 条</span>
      <button @click="nextPage" :disabled="tasks.length < pageSize">下一页</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'
import type { User } from '@/api/presets'
import { formatDateTime } from '@/utils/datetime'
import { success, error, confirm, info } from '@/utils/message'

const statusFilter = ref('')
const userFilter = ref('')
const page = ref(1)
const pageSize = 10
const loading = ref(false)
const tasks = ref<any[]>([])
const users = ref<User[]>([])
const total = ref(0)

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
    const params: any = { page: page.value, page_size: pageSize }
    if (statusFilter.value) params.status = statusFilter.value
    if (userFilter.value) params.user_id = userFilter.value

    const response = await request.get('/admin/tasks', { params })
    tasks.value = response.data.items
    total.value = response.data.total
  } catch (err) {
    console.error('获取任务失败:', err)
  } finally {
    loading.value = false
  }
}

const fetchUsers = async () => {
  try {
    const response = await request.get('/admin/users')
    users.value = response.data.items || response.data
  } catch (err) {
    console.error('获取用户失败:', err)
  }
}

const viewTask = (taskId: string) => {
  // 跳转到任务详情页面或显示所有任务， view 详情
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
})
</script>

<style scoped>
.task-monitor {
  padding: 20px;
}

.task-monitor h1 {
  margin-bottom: 20px;
}

.toolbar {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.toolbar select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.task-table {
  background: white;
  border-radius: 8px;
  overflow-x: auto;
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
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status.pending { background: #f0f0f0; }
.status.processing { background: #e6f7ff; color: #1890ff; }
.status.completed { background: #f6ffed; color: #52c41a; }
.status.failed { background: #fff1f0; color: #ff4d4f; }
.status.cancelled { background: #f5f5f5; color: #999; }

.progress-bar {
  width: 100px;
  height: 16px;
  background: #f0f0f0;
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

.loading {
  text-align: center;
  padding: 60px;
  color: #666;
}

.pagination {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 20px;
  border-top: 1px solid #eee;
  padding: 10px;
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
