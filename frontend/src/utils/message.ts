/**
 * 统一消息提示工具
 * 使用 Element Plus 的 ElMessage 和 ElMessageBox 替代原生 alert/confirm
 */
import { ElMessage, ElMessageBox } from 'element-plus'

type MessageType = 'success' | 'warning' | 'info' | 'error'

interface MessageOptions {
  message: string
  type?: MessageType
  duration?: number
}

/**
 * 显示顶部消息提示
 */
export function toast(message: string, type: MessageType = 'info', duration = 3000) {
  ElMessage({
    message,
    type,
    duration,
    offset: 60, // 顶部偏移，避免被导航栏遮挡
  })
}

/**
 * 成功消息
 */
export function success(message: string) {
  toast(message, 'success')
}

/**
 * 错误消息
 */
export function error(message: string) {
  toast(message, 'error', 4000)
}

/**
 * 警告消息
 */
export function warning(message: string) {
  toast(message, 'warning')
}

/**
 * 信息消息
 */
export function info(message: string) {
  toast(message, 'info')
}

/**
 * 显示确认对话框
 * @param message 提示信息
 * @param title 标题
 * @returns Promise<boolean> 用户是否确认
 */
export async function confirm(message: string, title = '确认'): Promise<boolean> {
  try {
    await ElMessageBox.confirm(message, title, {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
      // 移动端优化
      customClass: 'mobile-confirm-dialog',
      closeOnClickModal: false,
    })
    return true
  } catch {
    return false
  }
}

/**
 * 显示删除确认对话框
 */
export async function confirmDelete(itemName = '此项目'): Promise<boolean> {
  return confirm(`确定要删除${itemName}吗？此操作不可撤销。`, '删除确认')
}

/**
 * 显示输入对话框
 */
export async function prompt(
  message: string,
  title = '请输入',
  defaultValue = ''
): Promise<string | null> {
  try {
    const { value } = await ElMessageBox.prompt(message, title, {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: defaultValue,
      // 移动端优化
      customClass: 'mobile-prompt-dialog',
      inputPlaceholder: '请输入...',
    })
    return value
  } catch {
    return null
  }
}

// 默认导出
export default {
  toast,
  success,
  error,
  warning,
  info,
  confirm,
  confirmDelete,
  prompt,
}
