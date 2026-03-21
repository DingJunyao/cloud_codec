<template>
  <div class="task-detail">
    <div class="header">
      <button @click="$router.back()" class="back-btn">← 返回</button>
      <h1>{{ store.currentTask?.name }}</h1>
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
          <span v-if="wsMessage">{{ wsMessage }}</span>
        </div>
        <div class="progress-bar">
          <div class="fill" :style="{ width: store.currentTask.progress + '%' }"></div>
        </div>
      </div>

      <div class="info-grid">
        <div class="info-item">
          <label>预设</label>
          <p>{{ store.currentTask.preset_name }}</p>
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
      </div>

      <div v-if="store.currentTask.status === 'processing'" class="actions">
        <button @click="handleCancel" class="btn-cancel">取消任务</button>
      </div>

      <div v-if="store.currentTask.output_path" class="output">
        <h3>输出文件</h3>
        <a :href="downloadUrl" class="download-link">下载</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'
import tasksApi from '@/api/tasks'

const route = useRoute()
const router = useRouter()
const store = useTasksStore()

const ws = ref(null)
const wsMessage = ref('')

const downloadUrl = computed(() => {
  return `/api/download/?path=${store.currentTask?.output_path}`
})

const statusText = (status) => {
  const map = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return map[status] || status
}

const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}

const handleCancel = async () => {
  if (!confirm('确定要取消此任务吗？')) return
  try {
    await store.cancelTask(route.params.id)
  } catch (error) {
    alert('取消失败: ' + error.message)
  }
}

onMounted(async () => {
  await store.fetchTask(route.params.id)

  // 连接 WebSocket
  ws.value = tasksApi.connectWebSocket(route.params.id, (data) => {
    store.updateTaskProgress(route.params.id, data)
    wsMessage.value = data.message
  })
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
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

.output {
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.download-link {
  color: #1890ff;
  text-decoration: none;
}
</style>
