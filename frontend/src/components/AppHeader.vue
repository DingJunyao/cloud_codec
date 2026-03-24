<template>
  <header class="app-header">
    <div class="header-content">
      <div class="logo" @click="$router.push('/tasks')">
        <h1>{{ appName }}</h1>
      </div>

      <nav class="main-nav">
        <router-link to="/tasks" class="nav-link">
          <el-icon><List /></el-icon>
          <span>任务</span>
        </router-link>
        <router-link to="/settings" class="nav-link">
          <el-icon><User /></el-icon>
          <span>个人中心</span>
        </router-link>
        <router-link v-if="user?.is_admin" to="/admin/dashboard" class="nav-link admin-link">
          <el-icon><Tools /></el-icon>
          <span>管理</span>
        </router-link>
      </nav>

      <div class="user-menu">
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-icon><UserFilled /></el-icon>
            <span>{{ user?.username || '用户' }}</span>
            <el-icon v-if="user?.is_admin" class="admin-badge"><Star /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled>
                <el-icon><User /></el-icon>
                {{ user?.username || '用户' }}
                <el-tag v-if="user?.is_admin" type="danger" size="small" style="margin-left: 8px">管理员</el-tag>
              </el-dropdown-item>
              <el-dropdown-item divided command="settings">
                <el-icon><Setting /></el-icon>
                设置
              </el-dropdown-item>
              <el-dropdown-item v-if="user?.is_admin" command="admin">
                <el-icon><Tools /></el-icon>
                管理面板
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import {
  List,
  Setting,
  User,
  UserFilled,
  Tools,
  SwitchButton,
  Star
} from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const appName = '码上转'
const user = computed(() => authStore.user)

const handleCommand = (command: string) => {
  switch (command) {
    case 'settings':
      router.push('/settings')
      break
    case 'admin':
      router.push('/admin/dashboard')
      break
    case 'logout':
      authStore.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
      break
  }
}
</script>

<style scoped>
.app-header {
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  cursor: pointer;
  display: flex;
  align-items: center;
}

.logo h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1890ff;
}

.main-nav {
  display: flex;
  gap: 8px;
  flex: 1;
  margin-left: 40px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 6px;
  color: #666;
  text-decoration: none;
  transition: all 0.2s;
  font-size: 14px;
}

.nav-link:hover {
  background: #f5f5f5;
  color: #1890ff;
}

.nav-link.router-link-active {
  background: #e6f7ff;
  color: #1890ff;
  font-weight: 500;
}

.nav-link.admin-link {
  color: #ff4d4f;
}

.nav-link.admin-link:hover {
  background: #fff1f0;
}

.nav-link.admin-link.router-link-active {
  background: #fff1f0;
  color: #ff4d4f;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  color: #333;
  font-size: 14px;
}

.user-info:hover {
  background: #f5f5f5;
}

.admin-badge {
  color: #ff4d4f;
  font-size: 12px;
}

@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
  }

  .logo h1 {
    font-size: 18px;
  }

  .main-nav {
    margin-left: 20px;
    gap: 4px;
  }

  .nav-link {
    padding: 8px 12px;
    font-size: 13px;
  }

  .nav-link span {
    display: none;
  }

  .user-info span {
    max-width: 80px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}
</style>
