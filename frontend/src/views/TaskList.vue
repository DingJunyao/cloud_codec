<template>
  <div class="task-list">
    <div class="header">
      <h1>转码任务</h1>
      <button @click="$router.push('/tasks/create')" class="btn-primary">
        新建任务
      </button>
    </div>

    <div class="filters">
      <button
        v-for="filter in filters"
        :key="filter.value"
        :class="{ active: currentFilter === filter.value }"
        @click="currentFilter = filter.value"
      >
        {{ filter.label }}
      </button>
    </div>

    <div v-if="store.loading" class="loading">加载中...</div>

    <div v-else-if="filteredTasks.length === 0" class="empty">
      <p>暂无任务</p>
      <button @click="$router.push('/tasks/create')">创建第一个任务</button>
    </div>

    <div v-else class="task-grid">
      <div
        v-for="task in filteredTasks"
        :key="task.id"
        class="task-card"
      >
        <div class="card-header" @click="$router.push(`/tasks/${task.id}`)">
          <div class="status" :class="task.status">{{ statusText(task.status) }}</div>
          <h3 class="file-name">{{ task.name || getFileName(task.source_file) }}</h3>
          <div class="progress-bar">
            <div class="fill" :style="{ width: task.progress + '%' }"></div>
          </div>
          <div class="progress-info">
            <span>{{ task.progress }}%</span>
            <span v-if="task.status === 'processing'" class="time-info">
              <span v-if="task.started_at">已用 {{ formatDuration(getElapsedTime(task.started_at)) }}</span>
              <span v-if="task.progress_data?.eta"> | 剩余 {{ formatDuration(task.progress_data.eta) }}</span>
            </span>
          </div>
          <p class="time">{{ formatTime(task.created_at) }}</p>
        </div>
        <div class="card-actions" @click.stop>
          <button
            v-if="task.status === 'processing' || task.status === 'pending'"
            @click="handleStop(task.id)"
            class="btn-stop"
          >停止</button>
          <button
            v-if="task.status === 'completed'"
            @click="handleDownload(task)"
            class="btn-download"
          >下载</button>
          <button
            v-if="['completed', 'failed', 'cancelled'].includes(task.status)"
            @click="handleRetry(task.id, task.status === 'completed')"
            class="btn-retry"
          >重试</button>
          <button
            v-if="['completed', 'failed', 'cancelled'].includes(task.status)"
            @click="handleDelete(task.id)"
            class="btn-delete"
          >删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTasksStore } from '@/stores/tasks'
import tasksApi from '@/api/tasks'
import type { Task } from '@/api/tasks'
import { formatDateTime, formatDuration, getElapsedTime } from '@/utils/datetime'
import { success, error, confirm } from '@/utils/message'

const store = useTasksStore()
const currentFilter = ref('all')
let pollInterval: number | null = null

const filters = [
  { value: 'all', label: '全部' },
  { value: 'pending', label: '等待中' },
  { value: 'processing', label: '处理中' },
  { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失败' },
  { value: 'cancelled', label: '已取消' }
]

const filteredTasks = computed(() => {
  if (currentFilter.value === 'all') return store.tasks
  return store.tasks.filter(t => t.status === currentFilter.value)
})

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

const getFileName = (path: string) => {
  return path.split('/').pop() || path
}

const handleStop = async (taskId: string) => {
  if (!await confirm('确定要停止此任务吗？')) return

  try {
    await tasksApi.cancel(taskId)
    await store.refreshTasks()
  } catch (err) {
    error('停止失败')
  }
}

const handleDownload = async (task: Task) => {
  if (!task.output_file) return

  try {
    // 获取下载信息（包含正确的文件名）
    const downloadInfo = await tasksApi.getDownloadInfo(task.id)

    // 获取 token
    let token = ''
    const stored = localStorage.getItem('auth_tokens')
    if (stored) {
      const tokens = JSON.parse(stored)
      token = tokens.access || ''
    }

    if (!token) {
      error('请先登录')
      return
    }

    // 使用返回的 URL 下载文件
    const response = await fetch(downloadInfo.url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      if (response.status === 401) {
        error('登录已过期，请重新登录')
      } else {
        error('下载失败: ' + response.statusText)
      }
      return
    }

    // 创建 Blob 并触发下载
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = downloadInfo.filename || 'output.mp4'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (err: any) {
    error('下载失败: ' + err.message)
  }
}

const handleDelete = async (taskId: string) => {
  if (!await confirm('确定要删除此任务吗？')) return

  try {
    await tasksApi.remove(taskId)
    await store.refreshTasks()
  } catch (err) {
    error('删除失败')
  }
}

const handleRetry = async (taskId: string, isCompleted: boolean) => {
  const message = isCompleted
    ? '此任务已完成，确定要重新转码吗？这将覆盖现有输出文件。'
    : '确定要重新转码吗？'

  if (!await confirm(message)) return

  try {
    await tasksApi.retry(taskId)
    await store.refreshTasks()
  } catch (err: any) {
    error('重试失败: ' + (err.response?.data?.detail || err.message))
  }
}

onMounted(() => {
  // 首次加载显示 loading
  store.fetchTasks()
  // 轮询使用静默刷新，不触发 loading 状态
  pollInterval = window.setInterval(() => {
    store.refreshTasks()
  }, 3000)
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
})
</script>

<style scoped>
.task-list {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.filters button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
}

.filters button.active {
  background: #1890ff;
  color: white;
  border-color: #1890ff;
}

.loading, .empty {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.empty button {
  margin-top: 16px;
  padding: 10px 20px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.task-card {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.task-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.status {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-bottom: 8px;
}

.status.pending { background: #f0f0f0; }
.status.processing { background: #e6f7ff; color: #1890ff; }
.status.completed { background: #f6ffed; color: #52c41a; }
.status.failed { background: #fff1f0; color: #ff4d4f; }
.status.cancelled { background: #f5f5f5; color: #999; }

.file-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 12px;
  word-break: break-all;
}

.progress-bar {
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  margin: 8px 0;
  overflow: hidden;
}

.progress-bar .fill {
  height: 100%;
  background: #1890ff;
  transition: width 0.3s;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
}

.time {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.btn-primary {
  padding: 10px 20px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-primary:hover {
  background: #40a9ff;
}
</style>
