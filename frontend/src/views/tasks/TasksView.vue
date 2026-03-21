<template>
  <div class="tasks-view">
    <h2>转码任务</h2>
    <p>任务列表功能开发中...</p>
    <el-button type="primary" @click="ElMessage.info('功能开发中')">
      创建新任务
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
</script>

<style scoped lang="scss">
.tasks-view {
  color: #ffffff;
  h2 { margin-top: 0; }
  p { color: #b0b0b0; }
}
</style>
