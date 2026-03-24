<template>
  <div class="admin-dashboard">
    <h1>系统概览</h1>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats.users?.total || 0 }}</div>
        <div class="stat-label">注册用户</div>
      </div>

      <div class="stat-card">
        <div class="stat-value">{{ stats.tasks?.total || 0 }}</div>
        <div class="stat-label">总任务数</div>
      </div>

      <div class="stat-card highlight">
        <div class="stat-value">{{ stats.tasks?.today || 0 }}</div>
        <div class="stat-label">今日任务</div>
      </div>

      <div class="stat-card">
        <div class="stat-value">{{ stats.presets?.total || 0 }}</div>
        <div class="stat-label">预设数量</div>
      </div>
    </div>

    <div class="section">
      <h2>任务状态分布</h2>
      <div class="status-bars">
        <div
          v-for="(count, status) in stats.tasks?.by_status"
          :key="status"
          class="status-bar"
        >
          <span class="status-label">{{ statusText(status) }}</span>
          <div class="bar">
            <div
              class="bar-fill"
              :class="status"
              :style="{ width: barWidth(count) }"
            ></div>
          </div>
          <span class="status-count">{{ count }}</span>
        </div>
      </div>
    </div>

    <div class="section">
      <h2>硬件加速</h2>
      <div class="hw-status">
        <div class="hw-item">
          <span class="hw-label">系统</span>
          <span class="hw-value">{{ stats.hardware?.system || '-' }}</span>
        </div>
        <div class="hw-item">
          <span class="hw-label">最佳方案</span>
          <span class="hw-value">{{ stats.hardware?.best || '无' }}</span>
        </div>
        <div class="hw-item">
          <span class="hw-label">可用方案</span>
          <span class="hw-value">
            {{ stats.hardware?.available?.join(', ') || '无' }}
          </span>
        </div>
      </div>
    </div>

    <div class="section">
      <h2>管理功能</h2>
      <div class="management-cards">
        <router-link to="/admin/users" class="management-card">
          <el-icon size="32"><User /></el-icon>
          <div class="card-title">用户管理</div>
          <div class="card-desc">管理系统用户和权限</div>
        </router-link>
        <router-link to="/admin/groups" class="management-card">
          <el-icon size="32"><UserFilled /></el-icon>
          <div class="card-title">用户组管理</div>
          <div class="card-desc">配置用户组和权限</div>
        </router-link>
        <router-link to="/admin/tasks" class="management-card">
          <el-icon size="32"><List /></el-icon>
          <div class="card-title">任务监控</div>
          <div class="card-desc">查看所有转码任务</div>
        </router-link>
        <router-link to="/admin/presets" class="management-card">
          <el-icon size="32"><Setting /></el-icon>
          <div class="card-title">预设管理</div>
          <div class="card-desc">管理转码预设</div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { User, UserFilled, List, Setting } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const loading = ref(true)
const stats = ref<Record<string, any>>({})

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

const barWidth = (count: number) => {
  const total = stats.value.tasks?.total || 1
  return `${(count / total) * 100}%`
}

const fetchStats = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/admin/stats', {
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    stats.value = await response.json()
  } catch (error) {
    console.error('获取统计失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(fetchStats)
</script>

<style scoped>
.admin-dashboard {
  padding: 20px;
}

.admin-dashboard h1 {
  margin-bottom: 24px;
  color: var(--color-text-primary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--color-border-light);
  border-radius: 8px;
  padding: 24px;
  text-align: center;
}

.stat-card.highlight {
  background: rgba(24, 144, 255, 0.1);
  border-color: rgba(24, 144, 255, 0.2);
}

html.dark .stat-card {
  background: var(--color-bg-card);
}

html.dark .stat-card.highlight {
  background: rgba(24, 144, 255, 0.15);
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #1890ff;
}

.stat-card.highlight .stat-value {
  color: #52c41a;
}

.stat-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-top: 8px;
}

.section {
  margin-bottom: 32px;
}

.section h2 {
  font-size: 18px;
  margin-bottom: 16px;
  color: var(--color-text-primary);
}

.status-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-label {
  width: 80px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.bar {
  flex: 1;
  height: 24px;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
  overflow: hidden;
}

html.dark .bar {
  background: var(--el-fill-color);
}

.bar-fill {
  height: 100%;
  transition: width 0.3s;
}

.bar-fill.pending { background: #d9d9d9; }
.bar-fill.processing { background: #1890ff; }
.bar-fill.completed { background: #52c41a; }
.bar-fill.failed { background: #ff4d4f; }
.bar-fill.cancelled { background: #faad14; }

.status-count {
  width: 40px;
  text-align: right;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.hw-status {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.hw-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hw-label {
  font-size: 12px;
  color: var(--color-text-placeholder);
  text-transform: uppercase;
}

.hw-value {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.loading {
  text-align: center;
  padding: 60px;
  color: var(--color-text-secondary);
}

.management-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.management-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  text-decoration: none;
  color: inherit;
  transition: all 0.3s;
  cursor: pointer;
}

.management-card .el-icon {
  color: var(--el-color-primary);
}

html.dark .management-card .el-icon {
  color: var(--el-color-primary);
}

.management-card:hover {
  background: rgba(24, 144, 255, 0.05);
  border-color: #1890ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px var(--color-shadow);
}

html.dark .management-card:hover {
  background: rgba(24, 144, 255, 0.1);
}

.card-title {
  font-size: 16px;
  font-weight: 500;
  margin-top: 12px;
  color: var(--color-text-primary);
}

.card-desc {
  font-size: 12px;
  color: var(--color-text-placeholder);
  margin-top: 4px;
}
</style>
