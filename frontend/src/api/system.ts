import request from './request'

export interface HwAccelSupport {
  supported: string[]
  available: Array<{ value: string; label: string }>
}

export default {
  /**
   * 获取系统支持的硬件加速列表
   */
  async getHwAccelSupport(): Promise<HwAccelSupport> {
    return request.get('/system/hw-accel')
  }
}
