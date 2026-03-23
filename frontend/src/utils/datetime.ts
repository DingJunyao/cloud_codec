/**
 * 时间处理工具函数
 * 后端统一返回 UTC 时间（ISO 8601 格式，带 Z 后缀）
 */

/**
 * 将 UTC 时间字符串转换为本地 Date 对象
 * @param time UTC 时间字符串（如 "2024-01-01T12:00:00Z"）
 * @returns 本地时间的 Date 对象
 */
export function formatDateTimeUTC(time: string | undefined | null): Date {
  if (!time) {
    return new Date()
  }
  // 如果时间字符串已经包含时区信息（Z 或 +HH:MM），直接解析
  // 如果没有时区信息，假设为 UTC 时间，添加 Z 后缀
  const timeStr = time.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(time)
    ? time
    : time + 'Z'
  return new Date(timeStr)
}

/**
 * 格式化 UTC 时间为本地时间字符串
 * @param time UTC 时间字符串
 * @param options Intl.DateTimeFormatOptions
 * @returns 本地时间字符串
 */
export function formatLocalTime(
  time: string | undefined | null,
  options?: Intl.DateTimeFormatOptions
): string {
  if (!time) return '-'
  const date = formatDateTimeUTC(time)
  return date.toLocaleString('zh-CN', options)
}

/**
 * 格式化 UTC 时间为本地日期时间字符串
 */
export function formatDateTime(time: string | undefined | null): string {
  return formatLocalTime(time)
}

/**
 * 格式化 UTC 时间为本地时间字符串（仅时间部分）
 */
export function formatTimeOnly(time: string | undefined | null): string {
  return formatLocalTime(time, { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

/**
 * 格式化秒数为时长字符串（HH:MM:SS 或 MM:SS）
 * @param seconds 秒数
 * @returns 时长字符串
 */
export function formatDuration(seconds: number | undefined | null): string {
  if (seconds === undefined || seconds === null || seconds < 0) return '-'

  const totalSeconds = Math.floor(seconds)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const secs = totalSeconds % 60

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

/**
 * 计算已用时间（从开始时间到现在）
 * @param startedAt 开始时间（UTC 字符串）
 * @returns 已用秒数，如果未开始则返回 0
 */
export function getElapsedTime(startedAt: string | undefined | null): number {
  if (!startedAt) return 0
  const start = formatDateTimeUTC(startedAt)
  const now = new Date()
  return Math.floor((now.getTime() - start.getTime()) / 1000)
}
