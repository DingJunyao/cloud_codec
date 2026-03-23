<template>
  <div class="task-detail">
    <div class="header">
      <button @click="$router.back()" class="back-btn">← 返回</button>
      <h1>任务详情</h1>
    </div>

    <div v-if="!store.currentTask" class="loading">加载中...</div>

    <div v-else class="detail-content">
      <div class="status-section">
        <div class="status-badge" :class="store.currentTask.status">
          {{ statusText(store.currentTask.status) }}
        </div>
        <p v-if="store.currentTask.error_message" class="error">
          错误: {{ store.currentTask.error_message }}
        </p>
      </div>

      <div class="progress-section">
        <div class="progress-info">
          <span>进度: {{ store.currentTask.progress }}%</span>
          <span v-if="store.currentTask.status === 'processing'" class="progress-details">
            <span v-if="store.currentTask.started_at">已用 {{ formatDuration(getElapsedTime(store.currentTask.started_at)) }}</span>
            <span v-if="store.currentTask.progress_data?.eta"> | 剩余 {{ formatDuration(store.currentTask.progress_data.eta) }}</span>
          </span>
        </div>
        <div class="progress-bar">
          <div class="fill" :style="{ width: store.currentTask.progress + '%' }"></div>
        </div>
      </div>

      <!-- 实时日志区域 -->
      <div class="log-section">
        <div class="log-header">
          <h3>实时日志</h3>
          <div class="log-status">
            <span :class="wsConnected ? 'connected' : 'disconnected'">
              {{ wsConnected ? '已连接' : '未连接' }}
            </span>
            <button @click="clearLogs" class="btn-clear">清空</button>
          </div>
        </div>
        <div class="log-container" ref="logContainer">
          <div v-if="logs.length === 0" class="log-empty">暂无日志</div>
          <div v-for="(log, index) in logs" :key="index" class="log-line" :class="log.type">
            <span class="log-time">{{ log.time }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>

      <div class="info-grid">
        <div class="info-item">
          <label>源文件</label>
          <p class="file-path">{{ store.currentTask.source_file }}</p>
        </div>
        <div class="info-item">
          <label>创建时间</label>
          <p>{{ formatTime(store.currentTask.created_at) }}</p>
        </div>
        <div v-if="store.currentTask.started_at" class="info-item">
          <label>开始时间</label>
          <p>{{ formatTime(store.currentTask.started_at) }}</p>
        </div>
        <div v-if="store.currentTask.completed_at" class="info-item">
          <label>完成时间</label>
          <p>{{ formatTime(store.currentTask.completed_at) }}</p>
        </div>
        <div v-if="store.currentTask.source_size" class="info-item">
          <label>源文件大小</label>
          <p>{{ formatSize(store.currentTask.source_size) }}</p>
        </div>
        <div v-if="store.currentTask.output_size" class="info-item">
          <label>输出大小</label>
          <p>{{ formatSize(store.currentTask.output_size) }}</p>
        </div>
      </div>

      <div v-if="store.currentTask.status === 'processing'" class="actions">
        <button @click="handleCancel" class="btn-cancel">取消任务</button>
      </div>

      <div v-if="store.currentTask.output_file" class="output">
        <h3>输出文件</h3>
        <p class="file-path">{{ store.currentTask.output_file }}</p>
        <button @click="handleDownload" class="download-link" :disabled="downloading">
          {{ downloading ? '下载中...' : '下载结果' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'
import tasksApi from '@/api/tasks'
import type { TaskProgressUpdate } from '@/api/tasks'
import { formatDateTime, formatTimeOnly, formatDuration, getElapsedTime } from '@/utils/datetime'
import { error, confirm } from '@/utils/message'

const route = useRoute()
const store = useTasksStore()

const ws = ref<WebSocket | null>(null)
const wsConnected = ref(false)
const logContainer = ref<HTMLElement | null>(null)

interface LogEntry {
  time: string
  message: string
  type: 'info' | 'progress' | 'error'
}

const logs = ref<LogEntry[]>([])
const MAX_LOGS = 500
const downloading = ref(false)

const downloadUrl = computed(() => {
  if (!store.currentTask?.output_file) return ''
  return `/api/download/?path=${encodeURIComponent(store.currentTask.output_file)}`
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

const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(2) + ' MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

const addLog = (message: string, type: 'info' | 'progress' | 'error' = 'info') => {
  logs.value.push({
    time: formatTimeOnly(new Date().toISOString()),
    message,
    type
  })
  // 限制日志数量
  if (logs.value.length > MAX_LOGS) {
    logs.value = logs.value.slice(-MAX_LOGS)
  }
  // 自动滚动到底部
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

const clearLogs = () => {
  logs.value = []
}

const handleCancel = async () => {
  if (!await confirm('确定要取消此任务吗？')) return
  try {
    await store.cancelTask(route.params.id as string)
    addLog('任务已取消', 'error')
  } catch (err: any) {
    error('取消失败: ' + err.message)
  }
}

const handleDownload = async () => {
  if (!store.currentTask?.output_file || downloading.value) return

  downloading.value = true
  try {
    // 获取下载信息（包含正确的文件名）
    const downloadInfo = await tasksApi.getDownloadInfo(route.params.id as string)

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
  } finally {
    downloading.value = false
  }
}

onMounted(async () => {
  await store.fetchTask(route.params.id as string)
  addLog('开始监控任务...', 'info')

  // 加载历史日志（注意：只用于显示，不影响当前状态）
  try {
    const response = await tasksApi.getLogs(route.params.id as string, { limit: 200 })
    if (response.logs && response.logs.length > 0) {
      // 清空日志列表，只加载历史日志
      logs.value = []
      // 将历史日志添加到日志列表（仅显示，不触发状态更新）
      response.logs.forEach(log => {
        logs.value.push({
          time: formatTimeOnly(log.created_at),
          message: log.message,
          type: log.type as 'info' | 'progress' | 'error'
        })
      })
      // 添加提示信息
      logs.value.push({
        time: formatTimeOnly(new Date().toISOString()),
        message: `--- 已加载 ${response.logs.length} 条历史日志 ---`,
        type: 'info'
      })
    }
  } catch (err) {
    console.warn('加载历史日志失败:', err)
  }

  // 重新获取最新任务状态（确保历史日志不会影响当前状态）
  await store.fetchTask(route.params.id as string)

  // 连接 WebSocket
  ws.value = tasksApi.connectWebSocket(route.params.id as string, (data: TaskProgressUpdate) => {
    if (data.type === 'progress') {
      store.updateTaskProgress(route.params.id as string, {
        progress: data.data.percent,
        progress_data: data.data,
        status: data.data.status
      })
      // 添加进度日志
      if (data.data.percent !== undefined) {
        const progressInfo = `进度: ${data.data.percent.toFixed(1)}%` +
          (data.data.fps ? ` | FPS: ${data.data.fps.toFixed(1)}` : '') +
          (data.data.speed ? ` | 速度: ${data.data.speed}` : '')
        addLog(progressInfo, 'progress')
      }
    } else if (data.type === 'log') {
      // FFmpeg 日志
      if (data.data.line) {
        const line = data.data.line
        const type = line.toLowerCase().includes('error') ? 'error' : 'info'
        addLog(line, type)
      }
    } else if (data.type === 'status') {
      if (data.data.status) {
        // 更新 store 中的任务状态
        store.updateTaskProgress(route.params.id as string, {
          status: data.data.status,
          progress: data.data.progress,
          output_file: data.data.output_file,
          output_size: data.data.output_size
        })
        addLog(`状态变更: ${statusText(data.data.status)}`, 'info')
      }
    } else if (data.type === 'error') {
      addLog(`错误: ${data.data.message || '未知错误'}`, 'error')
    }
  })

  // 监听 WebSocket 连接状态
  if (ws.value) {
    ws.value.onopen = () => {
      wsConnected.value = true
      addLog('WebSocket 已连接', 'info')
    }
    ws.value.onclose = () => {
      wsConnected.value = false
      addLog('WebSocket 已断开', 'error')
    }
  }
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
  store.clearCurrentTask()
})
</script>

<style scoped>
.task-detail {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.back-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #666;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.status-section {
  margin-bottom: 24px;
}

.status-badge {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 4px;
  font-weight: 500;
}

.status-badge.pending { background: #f0f0f0; }
.status-badge.processing { background: #e6f7ff; color: #1890ff; }
.status-badge.completed { background: #f6ffed; color: #52c41a; }
.status-badge.failed { background: #fff1f0; color: #ff4d4f; }
.status-badge.cancelled { background: #f5f5f5; color: #999; }

.error {
  color: #ff4d4f;
  margin-top: 8px;
}

.progress-section {
  margin-bottom: 24px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
}

.progress-details {
  color: #999;
}

.progress-bar {
  height: 12px;
  background: #f0f0f0;
  border-radius: 6px;
  overflow: hidden;
}

.progress-bar .fill {
  height: 100%;
  background: #1890ff;
  transition: width 0.3s;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.info-item label {
  font-size: 12px;
  color: #999;
  text-transform: uppercase;
}

.info-item p {
  font-size: 16px;
  margin-top: 4px;
}

.file-path {
  font-family: monospace;
  font-size: 14px !important;
  word-break: break-all;
}

.actions {
  margin-bottom: 24px;
}

.btn-cancel {
  padding: 10px 20px;
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-cancel:hover {
  background: #ff7875;
}

.output {
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.output h3 {
  margin-bottom: 8px;
}

.download-link {
  display: inline-block;
  margin-top: 12px;
  padding: 8px 16px;
  background: #1890ff;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 14px;
}

.download-link:hover:not(:disabled) {
  background: #40a9ff;
}

.download-link:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}

/* 日志区域样式 */
.log-section {
  margin-bottom: 24px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
}

.log-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}

.log-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

.log-status .connected {
  color: #52c41a;
  font-size: 12px;
}

.log-status .disconnected {
  color: #ff4d4f;
  font-size: 12px;
}

.btn-clear {
  padding: 4px 12px;
  font-size: 12px;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
}

.btn-clear:hover {
  color: #1890ff;
  border-color: #1890ff;
}

.log-container {
  height: 300px;
  overflow-y: auto;
  background: #1e1e1e;
  padding: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  line-height: 1.6;
}

.log-empty {
  color: #666;
  text-align: center;
  padding: 40px;
}

.log-line {
  display: flex;
  gap: 12px;
  color: #d4d4d4;
}

.log-line .log-time {
  color: #6a9955;
  flex-shrink: 0;
}

.log-line .log-message {
  word-break: break-all;
}

.log-line.progress .log-message {
  color: #4ec9b0;
}

.log-line.error .log-message {
  color: #f14c4c;
}

.log-line.info .log-message {
  color: #d4d4d4;
}
</style>
