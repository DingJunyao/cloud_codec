<template>
  <div class="task-create">
    <h1>创建转码任务</h1>

    <form @submit.prevent="handleSubmit" class="form">
      <div class="field">
        <label>任务名称</label>
        <input v-model="form.name" required placeholder="输入任务名称" />
      </div>

      <div class="field">
        <label>视频文件</label>
        <input type="file" @change="handleFileChange" accept="video/*" required />
      </div>

      <div class="field">
        <label>转码预设</label>
        <select v-model="form.preset_id" required>
          <option value="">选择预设</option>
          <option v-for="preset in presets" :key="preset.id" :value="preset.id">
            {{ preset.name }}
          </option>
        </select>
      </div>

      <div class="field">
        <label>输出文件名（可选）</label>
        <input v-model="form.output_name" placeholder="留空自动生成" />
      </div>

      <div class="actions">
        <button type="button" @click="$router.back()">取消</button>
        <button type="submit" :disabled="submitting">
          {{ submitting ? '创建中...' : '创建任务' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const store = useTasksStore()
const authStore = useAuthStore()

const form = ref({
  name: '',
  video_path: '',
  preset_id: '',
  output_name: ''
})

const presets = ref([])
const submitting = ref(false)

const handleFileChange = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await fetch('/api/upload/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      },
      body: formData
    })
    const data = await response.json()
    form.value.video_path = data.file_path
    form.value.name = form.value.name || file.name
  } catch (error) {
    alert('上传失败: ' + error.message)
  }
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    await store.createTask(form.value)
    router.push('/tasks')
  } catch (error) {
    alert('创建失败: ' + error.message)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  // 加载预设列表
  try {
    const response = await fetch('/api/presets/', {
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    presets.value = await response.json()
  } catch (error) {
    console.error('加载预设失败:', error)
  }
})
</script>

<style scoped>
.task-create {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field label {
  font-weight: 500;
}

.field input,
.field select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.actions button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.actions button[type="submit"] {
  background: #1890ff;
  color: white;
}

.actions button[type="button"] {
  background: #f0f0f0;
}
</style>
