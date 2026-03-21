/** 密码加密工具 */
import { sha256 } from 'js-sha256'

/**
 * 对密码进行 SHA256 加密
 * @param password 原始密码
 * @returns 加密后的密码（十六进制字符串）
 */
export function hashPassword(password: string): string {
  return sha256(password)
}
