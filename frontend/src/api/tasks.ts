/** 任务 API */
import request from './request'

export interface TaskCreate {
  name: string
  video_path: string
  preset_id: number
  output_name?: string
}

export interface Task {
  id: string
  name: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  progress: number
  input_path: string
  output_path: string | null
  preset_id: number
  preset_name: string
  created_at: string
  started_at: string | null
  completed_at: string | null
  error_message: string | null
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
  list(params?: { status?: string }) {
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
   * 连接 WebSocket
   */
  connectWebSocket(taskId: string, onMessage: (data: any) => void) {
    const authStore = useAuthStore()
    const token = authStore.accessToken
    const wsUrl = `${import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'}/api/tasks/ws/${taskId}?token=${token}`
    const ws = new WebSocket(wsUrl)

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
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
