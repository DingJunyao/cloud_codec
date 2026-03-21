/** 预设 API */
import request from './request'

export interface PresetCreate {
  name: string
  video_codec?: string
  video_bitrate?: string
  video_resolution?: string
  fps?: number
  audio_codec?: string
  audio_bitrate?: string
  audio_channels?: number
  output_format?: string
  extra_options?: string
}

export interface Preset extends PresetCreate {
  id: number
  user_id: number
  is_system: boolean
}

export default {
  /**
   * 获取预设列表
   */
  list(params?: { is_system?: boolean }) {
    return request.get<any, Preset[]>('/presets/', { params })
  },

  /**
   * 创建预设
   */
  create(data: PresetCreate) {
    return request.post<any, Preset>('/presets/', data)
  },

  /**
   * 获取预设详情
   */
  get(presetId: number) {
    return request.get<any, Preset>(`/presets/${presetId}`)
  },

  /**
   * 删除预设
   */
  delete(presetId: number) {
    return request.delete(`/presets/${presetId}`)
  },
}
