<template>
  <div class="preset-list">
    <div class="header">
      <h1>转码预设</h1>
      <button @click="showCreateDialog = true" class="btn-primary">
        新建预设
      </button>
    </div>

    <div class="tabs">
      <button :class="{ active: activeTab === 'user' }" @click="activeTab = 'user'">
        我的预设
      </button>
      <button :class="{ active: activeTab === 'system' }" @click="activeTab = 'system'">
        系统预设
      </button>
    </div>

    <div class="preset-grid">
      <div
        v-for="preset in filteredPresets"
        :key="preset.id"
        class="preset-card"
      >
        <div class="preset-header">
          <h3>{{ preset.name }}</h3>
          <button
            v-if="!preset.is_system"
            @click="handleDelete(preset.id)"
            class="btn-delete"
          >
            删除
          </button>
        </div>
        <div class="preset-details">
          <p><strong>视频:</strong> {{ preset.video_codec || '继承' }} | {{ preset.video_bitrate || '继承' }}</p>
          <p><strong>音频:</strong> {{ preset.audio_codec || '继承' }} | {{ preset.audio_bitrate || '继承' }}</p>
          <p v-if="preset.video_resolution"><strong>分辨率:</strong> {{ preset.video_resolution }}</p>
          <p v-if="preset.fps"><strong>帧率:</strong> {{ preset.fps }} fps</p>
        </div>
      </div>
    </div>

    <!-- 创建预设对话框 -->
    <div v-if="showCreateDialog" class="dialog-overlay" @click.self="showCreateDialog = false">
      <div class="dialog">
        <h2>新建预设</h2>
        <form @submit.prevent="handleCreate" class="form">
          <div class="field">
            <label>名称</label>
            <input v-model="newPreset.name" required />
          </div>
          <div class="field">
            <label>视频编码</label>
            <select v-model="newPreset.video_codec">
              <option value="">继承</option>
              <option value="libx264">H.264</option>
              <option value="libx265">H.265</option>
              <option value="libvpx-vp9">VP9</option>
            </select>
          </div>
          <div class="field">
            <label>视频比特率</label>
            <input v-model="newPreset.video_bitrate" placeholder="如: 2M" />
          </div>
          <div class="field">
            <label>音频编码</label>
            <select v-model="newPreset.audio_codec">
              <option value="">继承</option>
              <option value="aac">AAC</option>
              <option value="libmp3lame">MP3</option>
              <option value="libopus">Opus</option>
            </select>
          </div>
          <div class="field">
            <label>音频比特率</label>
            <input v-model="newPreset.audio_bitrate" placeholder="如: 128k" />
          </div>
          <div class="actions">
            <button type="button" @click="showCreateDialog = false">取消</button>
            <button type="submit">创建</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const presets = ref([])
const activeTab = ref('user')
const showCreateDialog = ref(false)

const newPreset = ref({
  name: '',
  video_codec: '',
  video_bitrate: '',
  audio_codec: '',
  audio_bitrate: ''
})

const filteredPresets = computed(() => {
  return presets.value.filter(p =>
    activeTab.value === 'system' ? p.is_system : !p.is_system
  )
})

const handleCreate = async () => {
  try {
    const response = await fetch('/api/presets/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify(newPreset.value)
    })
    if (response.ok) {
      const preset = await response.json()
      presets.value.push(preset)
      showCreateDialog.value = false
      newPreset.value = { name: '', video_codec: '', video_bitrate: '', audio_codec: '', audio_bitrate: '' }
    }
  } catch (error) {
    alert('创建失败: ' + error.message)
  }
}

const handleDelete = async (id) => {
  if (!confirm('确定要删除此预设吗？')) return
  try {
    await fetch(`/api/presets/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    presets.value = presets.value.filter(p => p.id !== id)
  } catch (error) {
    alert('删除失败: ' + error.message)
  }
}

onMounted(async () => {
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
  align-items: center;
  margin-bottom: 12px;
}

.btn-delete {
  padding: 6px 12px;
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.preset-details p {
  margin: 4px 0;
  font-size: 14px;
  color: #666;
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
}

.form {
  display: flex;
  flex-direction: column;
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
.field select {
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
