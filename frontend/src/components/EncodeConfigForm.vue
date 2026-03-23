<template>
  <div class="encode-config-form">
    <!-- 预设选择 -->
    <div class="form-section">
      <PresetSelector
        v-model="presetId"
        :config="config"
        @update:config="handlePresetConfigChange"
      />
    </div>

    <!-- 视频配置 -->
    <div class="form-section">
      <h3>视频设置</h3>
      <div class="form-row">
        <div class="form-item">
          <label>编码器</label>
          <select v-model="config.video.codec">
            <option value="h264">H.264</option>
            <option value="h265">H.265 (HEVC)</option>
            <option value="vp9">VP9</option>
            <option value="av1">AV1</option>
          </select>
        </div>
        <div class="form-item">
          <label>编码预设</label>
          <select v-model="config.video.codec_options.preset">
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
        <div class="form-item">
          <label>质量 (CRF)</label>
          <input
            type="range"
            v-model.number="config.video.codec_options.crf"
            min="0"
            max="51"
          />
          <span class="range-value">{{ config.video.codec_options.crf }}</span>
        </div>
      </div>

      <div class="form-row">
        <div class="form-item">
          <label>分辨率模式</label>
          <select v-model="config.video.resolution.mode">
            <option value="auto">保持原始</option>
            <option value="scale">缩放到</option>
            <option value="custom">自定义</option>
          </select>
        </div>
        <div class="form-item" v-if="config.video.resolution.mode !== 'auto'">
          <label>高度</label>
          <select v-model.number="config.video.resolution.height">
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
        <div class="form-item">
          <label>帧率</label>
          <select v-model.number="config.video.fps">
            <option :value="null">保持原始</option>
            <option :value="60">60 fps</option>
            <option :value="30">30 fps</option>
            <option :value="24">24 fps</option>
          </select>
        </div>
        <div class="form-item">
          <label>硬件加速</label>
          <select v-model="config.video.hw_accel">
            <option value="auto">自动</option>
            <option value="none">禁用</option>
            <option value="nvenc">NVIDIA NVENC</option>
            <option value="qsv">Intel QSV</option>
            <option value="vaapi">VAAPI</option>
            <option value="videotoolbox">VideoToolbox</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 音频配置 -->
    <div class="form-section">
      <h3>音频设置</h3>
      <div class="form-row">
        <div class="form-item">
          <label>编码器</label>
          <select v-model="config.audio.codec">
            <option value="aac">AAC</option>
            <option value="mp3">MP3</option>
            <option value="opus">Opus</option>
            <option value="ac3">AC3</option>
            <option value="copy">保持原始</option>
            <option value="none">移除音频</option>
          </select>
        </div>
        <div class="form-item" v-if="config.audio.codec !== 'copy' && config.audio.codec !== 'none'">
          <label>码率</label>
          <select v-model="config.audio.bitrate">
            <option value="64k">64 kbps</option>
            <option value="96k">96 kbps</option>
            <option value="128k">128 kbps</option>
            <option value="192k">192 kbps</option>
            <option value="256k">256 kbps</option>
            <option value="320k">320 kbps</option>
          </select>
        </div>
      </div>

      <div class="form-row" v-if="config.audio.codec !== 'copy' && config.audio.codec !== 'none'">
        <div class="form-item">
          <label>声道</label>
          <select v-model.number="config.audio.channels">
            <option :value="1">单声道</option>
            <option :value="2">立体声</option>
            <option :value="6">5.1</option>
          </select>
        </div>
        <div class="form-item">
          <label>采样率</label>
          <select v-model.number="config.audio.sample_rate">
            <option :value="22050">22050 Hz</option>
            <option :value="44100">44100 Hz</option>
            <option :value="48000">48000 Hz</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 容器配置 -->
    <div class="form-section">
      <h3>输出设置</h3>
      <div class="form-row">
        <div class="form-item">
          <label>容器格式</label>
          <select v-model="config.container">
            <option value="mp4">MP4</option>
            <option value="mkv">MKV</option>
            <option value="webm">WebM</option>
            <option value="mov">MOV</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 高级选项 -->
    <div class="form-section advanced">
      <h3 @click="showAdvanced = !showAdvanced" class="collapsible">
        高级选项
        <span class="toggle">{{ showAdvanced ? '−' : '+' }}</span>
      </h3>
      <div v-show="showAdvanced">
        <div class="form-item">
          <label>自定义 FFmpeg 参数</label>
          <input
            type="text"
            v-model="config.custom_params"
            placeholder="例如: -tune film -x264opts bframes=3"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import type { EncodeConfig } from '@/api/presets'
import PresetSelector from './PresetSelector.vue'

interface Props {
  modelValue: EncodeConfig
  presetId?: string
}

interface Emits {
  (e: 'update:modelValue', value: EncodeConfig): void
  (e: 'update:presetId', value: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const showAdvanced = ref(false)
const presetId = ref(props.presetId || '')

const defaultConfig: EncodeConfig = {
  video: {
    codec: 'h264',
    codec_options: { preset: 'medium', crf: 23 },
    resolution: { mode: 'auto', keep_aspect: true },
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

const config = reactive<EncodeConfig>(
  props.modelValue ? JSON.parse(JSON.stringify(props.modelValue)) : defaultConfig
)

const handlePresetConfigChange = (newConfig: EncodeConfig) => {
  Object.assign(config, JSON.parse(JSON.stringify(newConfig)))
}

watch(() => config, () => {
  emit('update:modelValue', JSON.parse(JSON.stringify(config)))
}, { deep: true })

watch(presetId, (val) => {
  emit('update:presetId', val)
})
</script>

<style scoped>
.encode-config-form {
  padding: 16px;
}

.form-section {
  margin-bottom: 24px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.form-section h3 {
  margin: 0 0 16px 0;
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 12px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-item label {
  font-size: 13px;
  font-weight: 500;
  color: #666;
}

.form-item select,
.form-item input[type="text"] {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-item input[type="range"] {
  flex: 1;
}

.range-value {
  min-width: 30px;
  text-align: center;
  font-size: 13px;
  color: #666;
}

.form-item:has(input[type="range"]) {
  flex-direction: row;
  align-items: center;
}

.advanced h3 {
  cursor: pointer;
  user-select: none;
}

.collapsible {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toggle {
  font-size: 18px;
  font-weight: bold;
  color: #999;
}

@media (max-width: 600px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
