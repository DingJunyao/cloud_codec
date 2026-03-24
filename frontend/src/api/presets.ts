/** 预设 API */
import request from './request'

// 转码配置类型定义
export interface VideoCodecOptions {
  preset?: string
  crf?: number
  profile?: string
  level?: string
  bitrate?: string
}

export interface ResolutionConfig {
  mode: 'auto' | 'custom' | 'scale'
  width?: number
  height?: number
  keep_aspect: boolean
}

export interface VideoConfig {
  codec: string
  codec_options: VideoCodecOptions
  resolution: ResolutionConfig
  fps?: number
  hw_accel: 'auto' | 'none' | 'nvenc' | 'qsv' | 'vaapi' | 'videotoolbox' | 'amf'
}

export interface AudioConfig {
  codec: string
  bitrate: string
  channels?: number
  sample_rate?: number
}

export interface FilterItem {
  type: string
  params: Record<string, unknown>
}

export interface EncodeConfig {
  video: VideoConfig
  audio: AudioConfig
  container: 'mp4' | 'mkv' | 'webm' | 'mov' | 'avi'
  filters: FilterItem[]
  custom_params?: string
}

// 预设类型定义
export interface PresetCreate {
  name: string
  description?: string
  config: EncodeConfig
}

export interface PresetUpdate {
  name?: string
  description?: string
  config?: EncodeConfig
}

export interface PresetClone {
  name?: string
}

export interface Preset {
  id: string
  name: string
  description?: string
  is_builtin: boolean
  is_default: boolean
  created_by?: string
  config: EncodeConfig
  created_at: string
  updated_at?: string
}

export default {
  /**
   * 获取预设列表
   * @param params.is_builtin - 猉是否为系统内置筛选
   * @param params.all - 管理员查看所有预设
   */
  list(params?: { is_builtin?: boolean; all?: boolean }) {
    return request.get<any, Preset[]>('/presets/', { params })
  },

  /**
   * 获取预设详情
   */
  get(presetId: string) {
    return request.get<any, Preset>(`/presets/${presetId}`)
  },

  /**
   * 创建预设
   */
  create(data: PresetCreate) {
    return request.post<any, Preset>('/presets/', data)
  },

  /**
   * 更新预设
   */
  update(presetId: string, data: PresetUpdate) {
    return request.put<any, Preset>(`/presets/${presetId}`, data)
  },

  /**
   * 删除预设
   */
  delete(presetId: string) {
    return request.delete(`/presets/${presetId}`)
  },

  /**
   * 克隆预设
   */
  clone(presetId: string, data?: PresetClone) {
    return request.post<any, Preset>(`/presets/${presetId}/clone`, data || {})
  },
}
