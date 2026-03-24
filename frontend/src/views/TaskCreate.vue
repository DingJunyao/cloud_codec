<template>
  <div class="task-create">
    <h1>创建转码任务</h1>

    <el-form @submit.prevent="handleSubmit" class="form" label-width="120px">
      <!-- 文件上传 -->
      <el-form-item label="视频文件" required>
        <input
          ref="fileInput"
          type="file"
          @change="handleFileChange"
          accept="video/*"
          :disabled="uploading"
          style="display: none"
        />
        <el-button
          @click="$refs.fileInput?.click()"
          :disabled="uploading"
          :loading="uploading"
        >
          {{ uploading ? '上传中...' : '选择文件' }}
        </el-button>
        <div v-if="uploading" class="upload-progress">
          <el-progress :percentage="uploadProgress" />
        </div>
        <div v-else-if="form.source_file" class="file-info">
          已上传: {{ fileName }}
        </div>
        <div v-else-if="uploadError" class="error-text">{{ uploadError }}</div>
      </el-form-item>

      <!-- 预设选择 -->
      <el-form-item label="转码预设">
        <el-select
          v-model="form.preset_id"
          placeholder="选择预设或自定义"
          @change="handlePresetChange"
          style="width: 100%"
        >
          <el-option value="" label="自定义参数" />
          <el-option-group label="系统预设">
            <el-option
              v-for="preset in systemPresets"
              :key="preset.id"
              :value="preset.id"
              :label="preset.name + (preset.description ? ' - ' + preset.description : '')"
            />
          </el-option-group>
          <el-option-group v-if="userPresets.length > 0" label="我的预设">
            <el-option
              v-for="preset in userPresets"
              :key="preset.id"
              :value="preset.id"
              :label="preset.name"
            />
          </el-option-group>
        </el-select>
      </el-form-item>

      <!-- 任务名称 -->
      <el-form-item label="任务名称">
        <el-input v-model="form.name" placeholder="默认使用文件名" />
      </el-form-item>

      <!-- 自定义参数折叠面板 -->
      <el-collapse v-model="activeCollapse" class="params-collapse">
        <el-collapse-item title="视频配置" name="video">
          <el-form-item label="编码器">
            <el-select v-model="config.video.codec" @change="markAsCustom" style="width: 100%">
              <el-option value="h264" label="H.264" />
              <el-option value="h265" label="H.265/HEVC" />
              <el-option value="vp9" label="VP9" />
              <el-option value="av1" label="AV1" />
              <el-option value="copy" label="复制" />
            </el-select>
          </el-form-item>

          <el-form-item label="编码预设">
            <el-select v-model="config.video.codec_options.preset" @change="markAsCustom" style="width: 100%">
              <el-option value="ultrafast" label="极快" />
              <el-option value="superfast" label="超快" />
              <el-option value="veryfast" label="很快" />
              <el-option value="faster" label="较快" />
              <el-option value="fast" label="快" />
              <el-option value="medium" label="中等" />
              <el-option value="slow" label="慢" />
              <el-option value="slower" label="较慢" />
              <el-option value="veryslow" label="极慢" />
            </el-select>
          </el-form-item>

          <el-form-item label="质量因子 (CRF)">
            <el-slider
              v-model="config.video.codec_options.crf"
              :min="0"
              :max="51"
              show-input
              @change="markAsCustom"
            />
          </el-form-item>

          <el-form-item label="目标码率">
            <el-input
              v-model="config.video.codec_options.bitrate"
              placeholder="如 5M, 2500K，留空使用 CRF"
              @input="markAsCustom"
            />
          </el-form-item>

          <el-form-item label="分辨率模式">
            <el-radio-group v-model="config.video.resolution.mode" @change="markAsCustom">
              <el-radio-button label="auto">自动</el-radio-button>
              <el-radio-button label="scale">缩放</el-radio-button>
              <el-radio-button label="custom">自定义</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <template v-if="config.video.resolution.mode !== 'auto'">
            <el-form-item label="宽度">
              <el-input-number
                v-model="config.video.resolution.width"
                :min="1"
                :max="7680"
                @change="markAsCustom"
              />
            </el-form-item>

            <el-form-item label="高度">
              <el-input-number
                v-model="config.video.resolution.height"
                :min="1"
                :max="4320"
                @change="markAsCustom"
              />
            </el-form-item>

            <el-form-item label="保持宽高比">
              <el-switch v-model="config.video.resolution.width" @change="markAsCustom" />
            </el-form-item>
          </template>

          <el-form-item label="帧率">
            <el-input-number
              v-model="config.video.fps"
              :min="1"
              :max="120"
              :step="1"
              placeholder="留空保持原始"
              @change="markAsCustom"
            />
          </el-form-item>

          <el-form-item label="硬件加速">
            <el-select
              v-model="config.video.hw_accel"
              @change="markAsCustom"
              style="width: 100%"
            >
              <el-option
                v-for="option in availableHwAccelOptions"
                :key="option.value"
                :value="option.value"
                :label="option.label"
              />
            </el-select>
          </el-form-item>
        </el-collapse-item>

        <el-collapse-item title="音频配置" name="audio">
          <el-form-item label="编码器">
            <el-select v-model="config.audio.codec" @change="markAsCustom" style="width: 100%">
              <el-option value="aac" label="AAC" />
              <el-option value="mp3" label="MP3" />
              <el-option value="opus" label="Opus" />
              <el-option value="ac3" label="AC3" />
              <el-option value="eac3" label="EAC3" />
              <el-option value="flac" label="FLAC" />
              <el-option value="copy" label="复制" />
              <el-option value="none" label="禁用音频" />
            </el-select>
          </el-form-item>

          <el-form-item label="码率">
            <el-input
              v-model="config.audio.bitrate"
              placeholder="如 128k, 192k"
              @input="markAsCustom"
            />
          </el-form-item>

          <el-form-item label="声道数">
            <el-select v-model="config.audio.channels" @change="markAsCustom" style="width: 100%">
              <el-option :value="1" label="单声道" />
              <el-option :value="2" label="立体声" />
              <el-option :value="6" label="5.1" />
              <el-option :value="8" label="7.1" />
            </el-select>
          </el-form-item>

          <el-form-item label="采样率">
            <el-select v-model="config.audio.sample_rate" @change="markAsCustom" style="width: 100%">
              <el-option :value="8000" label="8000 Hz" />
              <el-option :value="16000" label="16000 Hz" />
              <el-option :value="44100" label="44100 Hz" />
              <el-option :value="48000" label="48000 Hz" />
              <el-option :value="96000" label="96000 Hz" />
            </el-select>
          </el-form-item>
        </el-collapse-item>

        <el-collapse-item title="其他配置" name="other">
          <el-form-item label="容器格式">
            <el-select v-model="config.container" @change="markAsCustom" style="width: 100%">
              <el-option value="mp4" label="MP4" />
              <el-option value="mkv" label="MKV" />
              <el-option value="webm" label="WebM" />
              <el-option value="mov" label="MOV" />
              <el-option value="avi" label="AVI" />
            </el-select>
          </el-form-item>

          <el-form-item label="自定义参数">
            <el-input
              v-model="config.custom_params"
              type="textarea"
              :rows="3"
              placeholder="额外的 FFmpeg 参数，如 -movflags +faststart"
              @input="markAsCustom"
            />
          </el-form-item>
        </el-collapse-item>
      </el-collapse>

      <div class="actions">
        <el-button @click="$router.back()">取消</el-button>
        <el-button
          type="primary"
          @click="handleSubmit"
          :disabled="!canSubmit"
          :loading="submitting"
        >
          {{ submitting ? '创建中...' : '创建任务' }}
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'
import { useAuthStore } from '@/stores/auth'
import presetsApi from '@/api/presets'
import systemApi from '@/api/system'
import type { Preset } from '@/api/presets'
import { ElMessage } from 'element-plus'

const router = useRouter()
const store = useTasksStore()
const authStore = useAuthStore()

// 所有硬件加速选项
const allHwAccelOptions = [
  { value: 'auto', label: '自动' },
  { value: 'none', label: '禁用' },
  { value: 'nvenc', label: 'NVIDIA NVENC' },
  { value: 'qsv', label: 'Intel QSV' },
  { value: 'vaapi', label: 'VAAPI' },
  { value: 'videotoolbox', label: 'VideoToolbox' },
  { value: 'amf', label: 'AMD AMF' }
]

// 系统支持的硬件加速列表
const supportedHwAccels = ref<string[]>(['auto', 'none'])

// 默认配置
const defaultConfig = {
  video: {
    codec: 'h264',
    codec_options: {
      preset: 'medium',
      crf: 23,
      profile: null,
      level: null,
      bitrate: null
    },
    resolution: {
      mode: 'auto',
      width: null,
      height: null,
      keep_aspect: true
    },
    fps: null,
    hw_accel: 'auto'
  },
  audio: {
    codec: 'aac',
    bitrate: '128k',
    channels: 2,
    sample_rate: 48000
  },
  container: 'mp4',
  filters: [],
  custom_params: ''
}

const form = ref({
  source_file: '',
  preset_id: '',
  name: '',
  original_name: ''
})

const config = ref(JSON.parse(JSON.stringify(defaultConfig)))
const presets = ref<Preset[]>([])
const submitting = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadError = ref('')
const activeCollapse = ref<string[]>([])
const fileInput = ref<HTMLInputElement>()

const fileName = computed(() => {
  return form.value.original_name || form.value.source_file.split('/').pop() || ''
})

const systemPresets = computed(() =>
  presets.value.filter(p => p.is_builtin)
)

const userPresets = computed(() =>
  presets.value.filter(p => !p.is_builtin)
)

// 过滤可用的硬件加速选项
const availableHwAccelOptions = computed(() => {
  return allHwAccelOptions.filter(option =>
    supportedHwAccels.value.includes(option.value)
  )
})

const canSubmit = computed(() =>
  !submitting.value &&
  !uploading.value &&
  !!form.value.source_file
)

// 标记为自定义，清除预设选择
const markAsCustom = () => {
  if (form.value.preset_id && form.value.preset_id !== '') {
    form.value.preset_id = ''
  }
}

// 预设选择变化
const handlePresetChange = async (presetId: string) => {
  if (!presetId) return

  const preset = presets.value.find(p => p.id === presetId)
  if (preset?.config) {
    // 深拷贝配置
    config.value = JSON.parse(JSON.stringify(preset.config))
    // 确保所有必需字段都存在
    if (!config.value.video.codec_options) {
      config.value.video.codec_options = { preset: 'medium', crf: 23 }
    }
    if (!config.value.video.resolution) {
      config.value.video.resolution = { mode: 'auto', keep_aspect: true }
    }
    if (!config.value.audio.channels) {
      config.value.audio.channels = 2
    }
    if (!config.value.audio.sample_rate) {
      config.value.audio.sample_rate = 48000
    }
  }
}

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

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        uploadProgress.value = Math.round((e.loaded / e.total) * 100)
      }
    })

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

      const isViteDev = window.location.port === '5173'
      let uploadUrl: string
      if (isViteDev) {
        uploadUrl = `http://${window.location.hostname}:8000/api/upload/`
      } else if (import.meta.env.VITE_UPLOAD_API_URL) {
        uploadUrl = `${import.meta.env.VITE_UPLOAD_API_URL}/upload/`
      } else {
        uploadUrl = `${window.location.origin}/api/upload/`
      }
      xhr.open('POST', uploadUrl)
      xhr.setRequestHeader('Authorization', `Bearer ${authStore.accessToken}`)
      xhr.send(formData)
    })

    form.value.source_file = response.file_path
    form.value.original_name = response.original_name
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
  if (!form.value.source_file) {
    ElMessage.error('请选择视频文件')
    return
  }

  submitting.value = true
  try {
    // 根据是否有预设ID决定提交格式
    const taskData: any = {
      source_file: form.value.source_file,
      name: form.value.name || undefined
    }

    if (form.value.preset_id) {
      taskData.preset_id = form.value.preset_id
    } else {
      taskData.config = config.value
    }

    await store.createTask(taskData)
    ElMessage.success('任务创建成功')
    router.push('/tasks')
  } catch (err: any) {
    let message = '创建失败'
    if (err.response?.status === 503) {
      message = err.response?.data?.detail || '任务队列服务不可用，请联系管理员'
    } else if (err.response?.data?.detail) {
      message = err.response.data.detail
    } else if (err.message) {
      message = err.message
    }
    ElMessage.error(message)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    // 并行加载预设和硬件加速支持信息
    const [presetsData, hwAccelData] = await Promise.all([
      presetsApi.list().catch(err => {
        console.error('加载预设失败:', err)
        return []
      }),
      systemApi.getHwAccelSupport().catch(err => {
        console.error('获取硬件加速支持失败:', err)
        return { supported: ['auto', 'none'] }
      })
    ])

    presets.value = presetsData
    supportedHwAccels.value = hwAccelData.supported
  } catch (err) {
    console.error('初始化失败:', err)
  }
})
</script>

<style scoped>
.task-create {
  max-width: var(--page-max-width);
  margin: 0 auto;
  padding: 20px;
}

.task-create h1 {
  color: var(--color-text-primary);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: var(--color-bg-card);
  padding: 24px;
  border-radius: 8px;
  border: 1px solid var(--color-border-light);
}

.params-collapse {
  margin-top: 10px;
}

.file-info {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 8px;
}

.upload-progress {
  margin-top: 12px;
}

.error-text {
  font-size: 12px;
  color: #ff4d4f;
  margin-top: 8px;
}

.actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

:deep(.el-form-item) {
  margin-bottom: 16px;
}

:deep(.el-form-item__label) {
  color: var(--color-text-regular);
}

:deep(.el-collapse-item__header) {
  font-weight: 500;
  color: var(--color-text-primary);
  background: transparent;
}

:deep(.el-collapse-item__content) {
  background: transparent;
}

/* Element Plus Select 下拉框夜间模式适配 */
:deep(.el-select) {
  width: 100%;
}
:deep(.el-select .el-input__wrapper) {
  background-color: var(--color-bg-card);
  box-shadow: 0 0 0 1px var(--color-border) inset;
}
:deep(.el-select .el-input__inner) {
  color: var(--color-text-primary);
}

/* Element Plus Input 输入框夜间模式适配 */
:deep(.el-input__wrapper) {
  background-color: var(--color-bg-card);
  box-shadow: 0 0 0 1px var(--color-border) inset;
}
:deep(.el-input__inner) {
  color: var(--color-text-primary);
}

/* Element Plus Upload 按钮夜间模式适配 */
:deep(.el-upload) {
  width: 100%;
}
:deep(.el-upload-list__item .el-upload-dragger) {
  background-color: var(--color-bg-card);
  border-color: var(--color-border);
}
:deep(.el-upload-dragger:hover) {
  border-color: var(--el-color-primary);
}
:deep(.el-upload-list__item .el-upload__text) {
  color: var(--color-text-regular);
}
:deep(.el-upload-list__item .el-icon--upload) {
  color: var(--color-text-secondary);
}
:deep(.el-upload-list__item .el-upload-list__item-status) {
  color: var(--color-text-secondary);
}

/* Element Plus 按钮夜间模式适配 */
:deep(.el-button--default) {
  background-color: var(--color-bg-card);
  border-color: var(--color-border);
  color: var(--color-text-regular);
}
:deep(.el-button--default:hover) {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary);
}
:deep(.el-progress) {
  line-height: 1;
}
:deep(.el-progress-bar__outer) {
  background-color: var(--el-fill-color-light);
}
:deep(.el-progress-bar__innerText) {
  color: var(--color-text-primary);
}
@media (max-width: 768px) {
  .task-create {
    padding: 0;
  }

    .form {
        padding: 16px;
        border-radius: 0;
        border-left: none;
        border-right: none;
    }
}
</style>
