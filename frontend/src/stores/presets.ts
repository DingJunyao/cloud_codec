/** 预设 Store */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import presetsApi from '@/api/presets'
import type { Preset, PresetCreate } from '@/api/presets'

export const usePresetsStore = defineStore('presets', () => {
  // State
  const presets = ref<Preset[]>([])
  const userPresets = ref<Preset[]>([])
  const systemPresets = ref<Preset[]>([])
  const loading = ref(false)

  // Actions
  async function fetchPresets() {
    loading.value = true
    try {
      presets.value = await presetsApi.list()
      userPresets.value = presets.value.filter(p => !p.is_system)
      systemPresets.value = presets.value.filter(p => p.is_system)
    } finally {
      loading.value = false
    }
  }

  async function createPreset(data: PresetCreate) {
    const preset = await presetsApi.create(data)
    presets.value.push(preset)
    userPresets.value.push(preset)
    return preset
  }

  async function deletePreset(presetId: number) {
    await presetsApi.delete(presetId)
    presets.value = presets.value.filter(p => p.id !== presetId)
    userPresets.value = userPresets.value.filter(p => p.id !== presetId)
  }

  return {
    // State
    presets,
    userPresets,
    systemPresets,
    loading,
    // Actions
    fetchPresets,
    createPreset,
    deletePreset,
  }
})
