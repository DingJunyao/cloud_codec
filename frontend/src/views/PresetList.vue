<template>
  <div class="preset-list">
    <div class="header">
      <h1>{{ isAdminView ? '预设管理' : '转码预设' }}</h1>
      <button @click="showCreateDialog = true" class="btn-primary">
        新建预设
      </button>
    </div>

    <div class="tabs">
      <button :class="{ active: activeTab === 'user' }" @click="activeTab = 'user'">
        {{ isAdminView ? '用户预设' : '我的预设' }}
      </button>
      <button :class="{ active: activeTab === 'system' }" @click="activeTab = 'system'">
        系统预设
      </button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="filteredPresets.length === 0" class="empty">
      <p>{{ activeTab === 'system' ? '暂无系统预设' : (isAdminView ? '暂无用户预设' : '暂无个人预设') }}</p>
    </div>

    <div v-else class="preset-grid">
      <div
        v-for="preset in filteredPresets"
        :key="preset.id"
        class="preset-card"
      >
        <div class="preset-header">
          <div class="preset-title">
            <h3>{{ preset.name }}</h3>
            <el-tag v-if="isAdminView && !preset.is_builtin && preset.created_by" size="small" type="info">
              用户创建
            </el-tag>
          </div>
          <div class="preset-actions">
            <button
              @click="handleClone(preset)"
              class="btn-clone"
            >
              克隆
            </button>
            <button
              v-if="!preset.is_builtin && !isAdminView"
              @click="handleDelete(preset.id)"
              class="btn-delete"
            >
              删除
            </button>
          </div>
        </div>
        <p class="preset-desc">{{ preset.description || '无描述' }}</p>
        <div class="preset-details">
          <el-tag size="small">
            {{ preset.config?.video?.codec?.toUpperCase() || 'H.264' }}
          </el-tag>
          <el-tag size="small" type="info">
            {{ preset.config?.audio?.codec?.toUpperCase() || 'AAC' }}
          </el-tag>
          <el-tag size="small" type="success">
            {{ preset.config?.container?.toUpperCase() || 'MP4' }}
          </el-tag>
        </div>
        <div class="preset-config">
          <span v-if="preset.config?.video?.resolution?.height">
            分辨率: {{ preset.config.video.resolution.height }}p
          </span>
          <span v-if="preset.config?.video?.codec_options?.preset">
            预设: {{ preset.config.video.codec_options.preset }}
          </span>
          <span v-if="preset.config?.video?.codec_options?.crf">
            CRF: {{ preset.config.video.codec_options.crf }}
          </span>
        </div>
      </div>
    </div>

    <!-- 克隆预设对话框 -->
    <div v-if="showCloneDialog" class="dialog-overlay" @click.self="showCloneDialog = false">
      <div class="dialog">
        <h2>克隆预设</h2>
        <form @submit.prevent="confirmClone" class="form">
          <div class="field">
            <label>新预设名称</label>
            <input v-model="cloneForm.name" :placeholder="cloneForm.defaultName" />
          </div>
          <div class="actions">
            <button type="button" @click="showCloneDialog = false">取消</button>
            <button type="submit" :disabled="cloning">
              {{ cloning ? '处理中...' : '确认克隆' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 创建预设对话框 -->
    <div v-if="showCreateDialog" class="dialog-overlay" @click.self="showCreateDialog = false">
      <div class="dialog dialog-large">
        <h2>新建预设</h2>
        <form @submit.prevent="handleCreate" class="form">
          <div class="field">
            <label>名称 *</label>
            <input v-model="newPreset.name" required />
          </div>
          <div class="field">
            <label>描述</label>
            <textarea v-model="newPreset.description" rows="2"></textarea>
          </div>

          <div class="form-section-title">视频设置</div>
          <div class="form-row">
            <div class="field">
              <label>视频编码</label>
              <select v-model="newPreset.config.video.codec">
                <option value="h264">H.264</option>
                <option value="h265">H.265 (HEVC)</option>
                <option value="vp9">VP9</option>
                <option value="av1">AV1</option>
              </select>
            </div>
            <div class="field">
              <label>编码预设</label>
              <select v-model="newPreset.config.video.codec_options.preset">
                <option value="ultrafast">ultrafast</option>
                <option value="superfast">superfast</option>
                <option value="veryfast">veryfast</option>
                <option value="faster">faster</option>
                <option value="fast">fast</option>
                <option value="medium">medium</option>
                <option value="slow">slow</option>
                <option value="slower">slower</option>
                <option value="veryslow">veryslow</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="field">
              <label>CRF 质量 (0-51)</label>
              <input type="number" v-model.number="newPreset.config.video.codec_options.crf" min="0" max="51" />
            </div>
            <div class="field">
              <label>目标码率</label>
              <input v-model="newPreset.config.video.codec_options.bitrate" placeholder="如 5M, 2500K" />
            </div>
          </div>
          <div class="form-row">
            <div class="field">
              <label>分辨率模式</label>
              <select v-model="newPreset.config.video.resolution.mode">
                <option value="auto">自动（保持原始）</option>
                <option value="scale">缩放</option>
                <option value="custom">自定义</option>
              </select>
            </div>
            <div class="field">
              <label>分辨率高度</label>
              <select v-model.number="newPreset.config.video.resolution.height" :disabled="newPreset.config.video.resolution.mode === 'auto'">
                <option :value="null">自动</option>
                <option :value="2160">2160p (4K)</option>
                <option :value="1440">1440p (2K)</option>
                <option :value="1080">1080p</option>
                <option :value="720">720p</option>
                <option :value="480">480p</option>
                <option :value="360">360p</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="field">
              <label>帧率</label>
              <select v-model.number="newPreset.config.video.fps">
                <option :value="null">保持原始</option>
                <option :value="60">60 fps</option>
                <option :value="30">30 fps</option>
                <option :value="24">24 fps</option>
              </select>
            </div>
            <div class="field">
              <label>硬件加速</label>
              <select v-model="newPreset.config.video.hw_accel">
                <option
                  v-for="option in availableHwAccelOptions"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-section-title">音频设置</div>
          <div class="form-row">
            <div class="field">
              <label>音频编码</label>
              <select v-model="newPreset.config.audio.codec">
                <option value="aac">AAC</option>
                <option value="mp3">MP3</option>
                <option value="opus">Opus</option>
                <option value="ac3">AC3</option>
                <option value="copy">保持原始</option>
                <option value="none">移除音频</option>
              </select>
            </div>
            <div class="field">
              <label>音频码率</label>
              <select v-model="newPreset.config.audio.bitrate">
                <option value="64k">64 kbps</option>
                <option value="96k">96 kbps</option>
                <option value="128k">128 kbps</option>
                <option value="192k">192 kbps</option>
                <option value="256k">256 kbps</option>
                <option value="320k">320 kbps</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="field">
              <label>声道</label>
              <select v-model.number="newPreset.config.audio.channels">
                <option :value="1">单声道</option>
                <option :value="2">立体声</option>
                <option :value="6">5.1</option>
              </select>
            </div>
            <div class="field">
              <label>采样率</label>
              <select v-model.number="newPreset.config.audio.sample_rate">
                <option :value="22050">22050 Hz</option>
                <option :value="44100">44100 Hz</option>
                <option :value="48000">48000 Hz</option>
              </select>
            </div>
          </div>

          <div class="form-section-title">输出设置</div>
          <div class="field">
            <label>容器格式</label>
            <select v-model="newPreset.config.container">
              <option value="mp4">MP4</option>
              <option value="mkv">MKV</option>
              <option value="webm">WebM</option>
              <option value="mov">MOV</option>
            </select>
          </div>
          <div class="field">
            <label>自定义 FFmpeg 参数</label>
            <input v-model="newPreset.config.custom_params" placeholder="如 -movflags +faststart" />
          </div>

          <div class="actions">
            <button type="button" @click="showCreateDialog = false">取消</button>
            <button type="submit" :disabled="creating">
              {{ creating ? '创建中...' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute } from 'vue-router'
import presetsApi from '@/api/presets'
import systemApi from '@/api/system'
import type { Preset, EncodeConfig } from '@/api/presets'
import { error, confirm } from '@/utils/message'

const route = useRoute()
const isAdminView = computed(() => route.meta?.adminView === true)

const presets = ref<Preset[]>([])
const activeTab = ref('user')
const loading = ref(false)
const showCreateDialog = ref(false)
const showCloneDialog = ref(false)
const creating = ref(false)
const cloning = ref(false)

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

// 过滤可用的硬件加速选项
const availableHwAccelOptions = computed(() => {
  return allHwAccelOptions.filter(option =>
    supportedHwAccels.value.includes(option.value)
  )
})

const cloneForm = reactive({
  sourceId: '',
  name: '',
  defaultName: ''
})

const defaultConfig: EncodeConfig = {
  video: {
    codec: 'h264',
    codec_options: { preset: 'medium', crf: 23, bitrate: null },
    resolution: { mode: 'auto', width: null, height: null, keep_aspect: true },
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

const newPreset = reactive({
  name: '',
  description: '',
  config: JSON.parse(JSON.stringify(defaultConfig))
})

const filteredPresets = computed(() => {
  if (isAdminView.value) {
    // 管理员视图：根据选项卡显示系统预设或所有用户预设
    return presets.value.filter(p =>
      activeTab.value === 'system' ? p.is_builtin : !p.is_builtin
    )
  } else {
    // 普通用户视图：显示系统预设和自己的预设
    return presets.value.filter(p =>
      activeTab.value === 'system' ? p.is_builtin : !p.is_builtin
    )
  }
})

const fetchPresets = async () => {
  loading.value = true
  try {
    // 管理员视图请求所有预设
    presets.value = await presetsApi.list(isAdminView.value ? { all: true } : undefined)
  } catch (err) {
    console.error('加载预设失败:', err)
  } finally {
    loading.value = false
  }
}

const fetchHwAccelSupport = async () => {
  try {
    const data = await systemApi.getHwAccelSupport()
    supportedHwAccels.value = data.supported
  } catch (err) {
    console.error('获取硬件加速支持失败:', err)
  }
}

const handleCreate = async () => {
  creating.value = true
  try {
    const preset = await presetsApi.create({
      name: newPreset.name,
      description: newPreset.description,
      config: newPreset.config
    })
    presets.value.push(preset)
    showCreateDialog.value = false
    // 重置表单
    newPreset.name = ''
    newPreset.description = ''
    newPreset.config = JSON.parse(JSON.stringify(defaultConfig))
  } catch (err: any) {
    error('创建失败: ' + err.message)
  } finally {
    creating.value = false
  }
}

const handleClone = (preset: Preset) => {
  cloneForm.sourceId = preset.id
  cloneForm.defaultName = `${preset.name} (副本)`
  cloneForm.name = ''
  showCloneDialog.value = true
}

const confirmClone = async () => {
  cloning.value = true
  try {
    const cloned = await presetsApi.clone(cloneForm.sourceId, {
      name: cloneForm.name || undefined
    })
    presets.value.push(cloned)
    showCloneDialog.value = false
  } catch (err: any) {
    error('克隆失败: ' + err.message)
  } finally {
    cloning.value = false
  }
}

const handleDelete = async (id: string) => {
  if (!await confirm('确定要删除此预设吗？')) return
  try {
    await presetsApi.delete(id)
    presets.value = presets.value.filter(p => p.id !== id)
  } catch (err: any) {
    error('删除失败: ' + err.message)
  }
}

onMounted(async () => {
  await Promise.all([fetchPresets(), fetchHwAccelSupport()])
})
</script>

<style scoped>
.preset-list {
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

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.tabs button {
  padding: 10px 20px;
  border: none;
  background: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}

.tabs button.active {
  border-bottom-color: #1890ff;
  color: #1890ff;
}

.loading, .empty {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.preset-card {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 16px;
}

.preset-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.preset-header h3 {
  margin: 0;
  font-size: 16px;
}

.preset-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.creator-tag {
  font-size: 11px;
  color: #999;
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
}

.preset-actions {
  display: flex;
  gap: 8px;
}

.btn-clone {
  padding: 4px 12px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn-delete {
  padding: 4px 12px;
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.preset-desc {
  font-size: 13px;
  color: #666;
  margin-bottom: 12px;
}

.preset-details {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.preset-config {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
}

.btn-primary {
  padding: 10px 20px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  padding: 24px;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.dialog-large {
  max-width: 600px;
}

.dialog h2 {
  margin-bottom: 20px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1890ff;
  margin-top: 8px;
  margin-bottom: 4px;
  padding-bottom: 4px;
  border-bottom: 1px solid #e6f7ff;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 14px;
  font-weight: 500;
}

.field input,
.field select,
.field textarea {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 16px;
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
