<template>
  <div class="task-create">
    <h1>创建转码任务</h1>

    <form @submit.prevent="handleSubmit" class="form">
      <div class="field">
        <label>视频文件</label>
        <input type="file" @change="handleFileChange" accept="video/*" required :disabled="uploading" />
        <div v-if="uploading" class="upload-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
          </div>
          <span class="progress-text">上传中... {{ uploadProgress }}%</span>
        </div>
        <span v-else-if="form.source_file" class="file-info">已上传: {{ fileName }}</span>
        <span v-else-if="uploadError" class="error-text">{{ uploadError }}</span>
      </div>

      <div class="field">
        <label>转码预设</label>
        <select v-model="form.preset_id" required>
          <option value="">选择预设</option>
          <optgroup label="系统预设">
            <option
              v-for="preset in systemPresets"
              :key="preset.id"
              :value="preset.id"
            >
              {{ preset.name }}
              <template v-if="preset.description"> - {{ preset.description }}</template>
            </option>
          </optgroup>
          <optgroup v-if="userPresets.length > 0" label="我的预设">
            <option
              v-for="preset in userPresets"
              :key="preset.id"
              :value="preset.id"
            >
              {{ preset.name }}
            </option>
          </optgroup>
        </select>
      </div>

      <div class="field">
        <label>任务名称</label>
        <input v-model="form.name" placeholder="默认使用文件名" />
      </div>

      <div class="actions">
        <button type="button" @click="$router.back()">取消</button>
        <button type="submit" :disabled="!canSubmit">
          {{ submitting ? '创建中...' : '创建任务' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'
import { useAuthStore } from '@/stores/auth'
import presetsApi from '@/api/presets'
import type { Preset } from '@/api/presets'
import { error as showError } from '@/utils/message'

const router = useRouter()
const store = useTasksStore()
const authStore = useAuthStore()

const form = ref({
  source_file: '',
  preset_id: '',
  name: '',
  original_name: ''  // 上传返回的原始文件名
})

const presets = ref<Preset[]>([])
const submitting = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadError = ref('')

const fileName = computed(() => {
  // 显示原始文件名，如果没有则显示存储文件名
  return form.value.original_name || form.value.source_file.split('/').pop() || ''
})

const systemPresets = computed(() =>
  presets.value.filter(p => p.is_builtin)
)

const userPresets = computed(() =>
  presets.value.filter(p => !p.is_builtin)
)

const canSubmit = computed(() =>
  !submitting.value &&
  !uploading.value &&
  !!form.value.source_file &&
  !!form.value.preset_id
)

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  uploadError.value = ''
  uploading.value = true
  uploadProgress.value = 0
  form.value.source_file = ''

  const formData = new FormData()
  formData.append('file', file)

  try {
    const xhr = new XMLHttpRequest()

    // 监听上传进度
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        uploadProgress.value = Math.round((e.loaded / e.total) * 100)
      }
    })

    // 创建 Promise 处理响应
    const response = await new Promise<{ file_path: string; filename: string; original_name: string }>((resolve, reject) => {
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText))
          } catch {
            reject(new Error('解析响应失败'))
          }
        } else {
          const errorData = JSON.parse(xhr.responseText)
          reject(new Error(errorData.detail || `上传失败: ${xhr.status}`))
        }
      })

      xhr.addEventListener('error', () => reject(new Error('网络错误')))
      xhr.addEventListener('abort', () => reject(new Error('上传已取消')))

      // 直接请求后端，绕过 Vite 代理的缓冲
      // 开发环境（端口 5173）→ 使用当前主机名 + 后端端口 8000
      // 内网穿透 → 使用后端穿透地址（VITE_UPLOAD_API_URL 已包含 /api）
      // 生产环境 → 使用当前页面域名
      const isViteDev = window.location.port === '5173'
      let uploadUrl: string
      if (isViteDev) {
        // 使用当前访问的主机名，兼容 localhost 和内网 IP
        uploadUrl = `http://${window.location.hostname}:8000/api/upload/`
      } else if (import.meta.env.VITE_UPLOAD_API_URL) {
        // VITE_UPLOAD_API_URL 已包含 /api 前缀
        uploadUrl = `${import.meta.env.VITE_UPLOAD_API_URL}/upload/`
      } else {
        uploadUrl = `${window.location.origin}/api/upload/`
      }
      xhr.open('POST', uploadUrl)
      xhr.setRequestHeader('Authorization', `Bearer ${authStore.accessToken}`)
      xhr.send(formData)
    })

    form.value.source_file = response.file_path
    form.value.original_name = response.original_name  // 保存原始文件名
    // 自动填充任务名称（使用原始文件名，不含扩展名）
    if (!form.value.name) {
      form.value.name = response.original_name.replace(/\.[^/.]+$/, '')
    }
  } catch (err: any) {
    uploadError.value = err.message || '上传失败'
    form.value.source_file = ''
  } finally {
    uploading.value = false
  }
}

const handleSubmit = async () => {
  if (!form.value.source_file || !form.value.preset_id) {
    showError('请选择视频文件和预设')
    return
  }

  submitting.value = true
  try {
    await store.createTask(form.value)
    router.push('/tasks')
  } catch (err: any) {
    // 提取错误信息
    let message = '创建失败'
    if (err.response?.status === 503) {
      message = err.response?.data?.detail || '任务队列服务不可用，请联系管理员'
    } else if (err.response?.data?.detail) {
      message = err.response.data.detail
    } else if (err.message) {
      message = err.message
    }
    showError(message)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    presets.value = await presetsApi.list()
  } catch (err) {
    console.error('加载预设失败:', err)
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

.file-info {
  font-size: 12px;
  color: #666;
}

.upload-progress {
  margin-top: 8px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #1890ff;
  transition: width 0.2s ease;
}

.progress-text {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
  display: block;
}

.error-text {
  font-size: 12px;
  color: #ff4d4f;
}

.field input[type="file"]:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
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

.actions button[type="submit"]:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.actions button[type="button"] {
  background: #f0f0f0;
}
</style>
