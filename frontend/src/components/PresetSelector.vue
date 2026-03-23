<template>
  <div class="preset-selector">
    <div class="selector-header">
      <label>转码预设</label>
      <el-button
        v-if="selectedPreset && !selectedPreset.is_builtin"
        type="primary"
        link
        size="small"
        @click="showSaveDialog = true"
      >
        保存修改
      </el-button>
    </div>

    <el-select
      v-model="selectedId"
      placeholder="选择预设"
      class="preset-select"
      @change="handleSelect"
    >
      <el-option-group label="系统预设">
        <el-option
          v-for="preset in systemPresets"
          :key="preset.id"
          :label="preset.name"
          :value="preset.id"
        >
          <div class="preset-option">
            <span class="preset-name">{{ preset.name }}</span>
            <span v-if="preset.description" class="preset-desc">
              {{ preset.description }}
            </span>
          </div>
        </el-option>
      </el-option-group>

      <el-option-group v-if="userPresets.length > 0" label="我的预设">
        <el-option
          v-for="preset in userPresets"
          :key="preset.id"
          :label="preset.name"
          :value="preset.id"
        >
          <div class="preset-option">
            <span class="preset-name">{{ preset.name }}</span>
            <el-tag size="small" type="info">自定义</el-tag>
          </div>
        </el-option>
      </el-option-group>
    </el-select>

    <div v-if="selectedPreset" class="preset-info">
      <p class="preset-description">{{ selectedPreset.description || '无描述' }}</p>
      <div class="preset-details">
        <el-tag size="small">
          {{ selectedPreset.config?.video?.codec?.toUpperCase() || 'H.264' }}
        </el-tag>
        <el-tag size="small" type="info">
          {{ selectedPreset.config?.audio?.codec?.toUpperCase() || 'AAC' }}
        </el-tag>
        <el-tag size="small" type="success">
          {{ selectedPreset.config?.container?.toUpperCase() || 'MP4' }}
        </el-tag>
      </div>
    </div>

    <div class="preset-actions">
      <el-button
        type="primary"
        link
        @click="showCloneDialog = true"
        :disabled="!selectedPreset"
      >
        另存为预设
      </el-button>
    </div>

    <!-- 克隆预设对话框 -->
    <el-dialog
      v-model="showCloneDialog"
      title="保存为预设"
      width="400px"
    >
      <el-form :model="cloneForm" label-width="80px">
        <el-form-item label="预设名称">
          <el-input
            v-model="cloneForm.name"
            :placeholder="defaultCloneName"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCloneDialog = false">取消</el-button>
        <el-button type="primary" @click="handleClone" :loading="cloning">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 保存修改对话框 -->
    <el-dialog
      v-model="showSaveDialog"
      title="保存预设修改"
      width="400px"
    >
      <p>确定要保存对预设 "{{ selectedPreset?.name }}" 的修改吗？</p>
      <template #footer>
        <el-button @click="showSaveDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import presetsApi from '@/api/presets'
import type { Preset, EncodeConfig } from '@/api/presets'
import { ElMessage } from 'element-plus'

interface Props {
  modelValue?: string
  config?: EncodeConfig
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'update:config', value: EncodeConfig): void
  (e: 'preset-change', preset: Preset): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const presets = ref<Preset[]>([])
const selectedId = ref<string>(props.modelValue || '')
const loading = ref(false)

const showCloneDialog = ref(false)
const showSaveDialog = ref(false)
const cloneForm = ref({ name: '' })
const cloning = ref(false)
const saving = ref(false)

const systemPresets = computed(() =>
  presets.value.filter(p => p.is_builtin)
)

const userPresets = computed(() =>
  presets.value.filter(p => !p.is_builtin)
)

const selectedPreset = computed(() =>
  presets.value.find(p => p.id === selectedId.value)
)

const defaultCloneName = computed(() =>
  selectedPreset.value ? `${selectedPreset.value.name} (副本)` : ''
)

const handleSelect = () => {
  emit('update:modelValue', selectedId.value)
  if (selectedPreset.value) {
    emit('update:config', selectedPreset.value.config)
    emit('preset-change', selectedPreset.value)
  }
}

const handleClone = async () => {
  if (!selectedPreset.value) return

  cloning.value = true
  try {
    const newPreset = await presetsApi.clone(selectedPreset.value.id, {
      name: cloneForm.value.name || undefined
    })
    presets.value.push(newPreset)
    selectedId.value = newPreset.id
    emit('update:modelValue', newPreset.id)
    ElMessage.success('预设已保存')
    showCloneDialog.value = false
    cloneForm.value.name = ''
  } catch (error: any) {
    ElMessage.error('保存失败: ' + error.message)
  } finally {
    cloning.value = false
  }
}

const handleSave = async () => {
  if (!selectedPreset.value || !props.config) return

  saving.value = true
  try {
    const updated = await presetsApi.update(selectedPreset.value.id, {
      config: props.config
    })
    const index = presets.value.findIndex(p => p.id === updated.id)
    if (index !== -1) {
      presets.value[index] = updated
    }
    ElMessage.success('预设已更新')
    showSaveDialog.value = false
  } catch (error: any) {
    ElMessage.error('更新失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

const fetchPresets = async () => {
  loading.value = true
  try {
    presets.value = await presetsApi.list()
    // 如果没有选中，默认选择第一个系统预设
    if (!selectedId.value && systemPresets.value.length > 0) {
      selectedId.value = systemPresets.value[0].id
      handleSelect()
    }
  } catch (error) {
    console.error('加载预设失败:', error)
  } finally {
    loading.value = false
  }
}

watch(() => props.modelValue, (val) => {
  if (val !== selectedId.value) {
    selectedId.value = val
  }
})

onMounted(fetchPresets)
</script>

<style scoped>
.preset-selector {
  margin-bottom: 20px;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.selector-header label {
  font-weight: 500;
  font-size: 14px;
}

.preset-select {
  width: 100%;
}

.preset-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preset-name {
  font-weight: 500;
}

.preset-desc {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
}

.preset-info {
  margin-top: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.preset-description {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.preset-details {
  display: flex;
  gap: 8px;
}

.preset-actions {
  margin-top: 8px;
}
</style>
