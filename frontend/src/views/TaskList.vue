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

    <div v-else class="task-grid">
      <div
        v-for="task in filteredTasks"
        :key="task.id"
        class="task-card"
        @click="$router.push(`/tasks/${task.id}`)"
      >
        <div class="status" :class="task.status">{{ statusText(task.status) }}</div>
        <h3>{{ task.name }}</h3>
        <p class="preset">{{ task.preset_name }}</p>
        <div class="progress-bar">
          <div class="fill" :style="{ width: task.progress + '%' }"></div>
        </div>
        <p class="time">{{ formatTime(task.created_at) }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTasksStore } from '@/stores/tasks'

const store = useTasksStore()
const currentFilter = ref('all')

const filters = [
  { value: 'all', label: '全部' },
  { value: 'processing', label: '处理中' },
  { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失败' }
]

const filteredTasks = computed(() => {
  if (currentFilter.value === 'all') return store.tasks
  return store.tasks.filter(t => t.status === currentFilter.value)
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

onMounted(() => {
  store.fetchTasks()
  // 轮询更新
  setInterval(() => store.fetchTasks(), 5000)
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

.progress-bar {
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  margin: 12px 0;
  overflow: hidden;
}

.progress-bar .fill {
  height: 100%;
  background: #1890ff;
  transition: width 0.3s;
}

.btn-primary {
  padding: 10px 20px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
