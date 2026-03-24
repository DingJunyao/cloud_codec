<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <nav>
        <router-link to="/admin/users">用户管理</router-link>
        <router-link to="/admin/tasks">任务监控</router-link>
        <router-link to="/admin/presets">预设管理</router-link>
      </nav>
    </aside>

    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: calc(100vh - 48px);
}

.sidebar {
  width: 200px;
  background: var(--color-bg-card);
  border-right: 1px solid var(--color-border-light);
  padding: 20px;
}

.sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sidebar a {
  color: var(--color-text-regular);
  text-decoration: none;
  padding: 10px;
  border-radius: 4px;
}

.sidebar a:hover {
  background: var(--el-fill-color-light);
}

.sidebar a.router-link-active {
  background: #e6f7ff;
  color: #1890ff;
}

html.dark .sidebar a.router-link-active {
  background: rgba(24, 144, 255, 0.15);
}

.content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: var(--color-bg-base);
}
</style>
