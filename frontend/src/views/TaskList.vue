<template>
  <div class="task-list">
    <div class="header">
      <h1>转码任务</h1>
      <el-button type="primary" @click="$router.push('/tasks/create')">
        <el-icon><Plus /></el-icon>
        新建任务
      </el-button>
    </div>

    <div class="filters">
      <el-radio-group v-model="currentFilter" size="default">
        <el-radio-button
          v-for="filter in filters"
          :key="filter.value"
          :value="filter.value"
        >
          {{ filter.label }}
        </el-radio-button>
      </el-radio-group>
    </div>

    <div v-if="store.loading" class="loading">加载中...</div>

    <div v-else-if="filteredTasks.length === 0" class="empty">
      <p>暂无任务</p>
      <el-button type="primary" @click="$router.push('/tasks/create')">创建第一个任务</el-button>
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
          <el-button-group>
            <el-button
              v-if="task.status === 'processing' || task.status === 'pending'"
              @click="handleStop(task.id)"
              type="warning"
              size="small"
            >
              <el-icon><VideoPause /></el-icon>
              停止
            </el-button>
            <el-button
              v-if="task.status === 'completed'"
              @click="handleDownload(task)"
              type="primary"
              size="small"
            >
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button
              v-if="['completed', 'failed', 'cancelled'].includes(task.status)"
              @click="handleRetry(task.id, task.status === 'completed')"
              type="warning"
              size="small"
            >
              <el-icon><RefreshRight /></el-icon>
              重试
            </el-button>
            <el-button
              v-if="['completed', 'failed', 'cancelled'].includes(task.status)"
              @click="handleDelete(task.id)"
              type="danger"
              size="small"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </el-button-group>
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
import { Plus, VideoPause, Download, RefreshRight, Delete } from '@element-plus/icons-vue'

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
  max-width: var(--page-max-width);
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  margin: 0;
  color: var(--color-text-primary);
}

.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.loading, .empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--color-text-secondary);
}

.empty p {
  color: var(--color-text-secondary);
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.task-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.task-card:hover {
  box-shadow: 0 4px 12px var(--color-shadow);
  border-color: var(--color-border);
}

.card-header {
  color: var(--color-text-primary);
}

.status {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-bottom: 8px;
}

.status.pending {
  background: var(--el-fill-color-light);
  color: var(--color-text-secondary);
}

.status.processing {
  background: #e6f7ff;
  color: #1890ff;
}

html.dark .status.processing {
  background: rgba(24, 144, 255, 0.15);
}

.status.completed {
  background: #f6ffed;
  color: #52c41a;
}

html.dark .status.completed {
  background: rgba(82, 196, 26, 0.15);
}

.status.failed {
  background: #fff1f0;
  color: #ff4d4f;
}

html.dark .status.failed {
  background: rgba(255, 77, 79, 0.15);
}

.status.cancelled {
  background: var(--el-fill-color);
  color: var(--color-text-secondary);
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 12px;
  word-break: break-all;
  color: var(--color-text-primary);
}

.progress-bar {
  height: 6px;
  background: var(--el-fill-color);
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
  color: var(--color-text-secondary);
}

.time {
  font-size: 12px;
  color: var(--color-text-placeholder);
  margin-top: 8px;
}

.card-actions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border-lighter);
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .task-list {
    padding: 0;
  }

  .task-grid {
    grid-template-columns: 1fr;
  }

  .filters :deep(.el-radio-group) {
    flex-wrap: wrap;
  }

  .filters :deep(.el-radio-button__inner) {
    padding: 8px 12px;
    font-size: 13px;
  }
}
</style>
