/** 任务 API */
import request from './request'
import type { EncodeConfig } from './presets'
import { buildWebSocketUrl } from '@/utils/origin'

export interface TaskCreate {
  source_file: string
  preset_id?: string
  config?: EncodeConfig
  name?: string
}

export interface TaskProgressData {
  fps?: number
  speed?: string
  eta?: number
  frame?: number
  total_frames?: number
  percent?: number
}

export interface Task {
  id: string
  name: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  progress: number
  progress_data?: TaskProgressData
  source_file: string
  source_size?: number
  output_file?: string
  output_size?: number
  preset_id?: string
  config: EncodeConfig
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
  updated_at?: string
}

export interface TaskListResponse {
  items: Task[]
  total: number
  page: number
  page_size: number
}

export interface TaskProgressUpdate {
  type: 'progress' | 'log' | 'status' | 'error'
  data: {
    percent?: number
    fps?: number
    speed?: string
    eta?: number
    frame?: number
    total_frames?: number
    status?: string
    message?: string
    line?: string
    output_size?: number
    duration?: number
  }
}

export interface TaskLogEntry {
  id: string
  type: 'info' | 'progress' | 'error'
  message: string
  created_at: string
}

export interface TaskLogsResponse {
  total: number
  logs: TaskLogEntry[]
}

export default {
  /**
   * 创建任务
   */
  create(data: TaskCreate) {
    return request.post<any, Task>('/tasks/', data)
  },

  /**
   * 获取任务列表
   */
  list(params?: { status?: string; page?: number; page_size?: number }) {
    return request.get<any, Task[]>('/tasks/', { params })
  },

  /**
   * 获取任务详情
   */
  get(taskId: string) {
    return request.get<any, Task>(`/tasks/${taskId}`)
  },

  /**
   * 取消任务
   */
  cancel(taskId: string) {
    return request.post(`/tasks/${taskId}/cancel`)
  },

  /**
   * 删除任务
   */
  remove(taskId: string) {
    return request.delete(`/tasks/${taskId}`)
  },

  /**
   * 重新转码
   */
  retry(taskId: string) {
    return request.post<any, Task>(`/tasks/${taskId}/retry`)
  },

  /**
   * 获取任务日志
   */
  getLogs(taskId: string, params?: { limit?: number; offset?: number }) {
    return request.get<any, TaskLogsResponse>(`/tasks/${taskId}/logs`, { params })
  },

  /**
   * 获取下载信息（包含文件名）
   */
  async getDownloadInfo(taskId: string) {
    return request.get<any, { url: string; filename: string; size?: number }>(`/tasks/${taskId}/download`)
  },

  /**
   * 连接 WebSocket
   */
  connectWebSocket(taskId: string, onMessage: (data: TaskProgressUpdate) => void) {
    // 从 localStorage 获取 token
    let token = ''
    try {
      const stored = localStorage.getItem('auth_tokens')
      if (stored) {
        const tokens = JSON.parse(stored)
        token = tokens.access || ''
      }
    } catch {
      // ignore
    }

    // 使用动态计算的 WebSocket URL（支持局域网和内网穿透）
    const wsUrl = buildWebSocketUrl(`/api/tasks/ws/${taskId}`, { token })
    const ws = new WebSocket(wsUrl)

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as TaskProgressUpdate
        onMessage(data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    return ws
  },
}
