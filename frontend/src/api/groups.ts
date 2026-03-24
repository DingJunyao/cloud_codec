import request from './request'

export interface UserGroup {
  id: string
  name: string
  description?: string
  max_file_size?: number
  max_storage?: number
  result_retention_days?: number
  local_paths?: string[]
  allowed_preset_ids?: string[]
  default_preset_id?: string
  api_access_enabled: boolean
  email_enabled: boolean
  created_at: string
  updated_at: string
  user_count: number
}

export interface UserGroupCreate {
  name: string
  description?: string
  max_file_size?: number
  max_storage?: number
  result_retention_days?: number
  local_paths?: string[]
  allowed_preset_ids?: string[]
  default_preset_id?: string
  api_access_enabled?: boolean
  email_enabled?: boolean
}

export interface Permission {
  id: string
  code: string
  name: string
  description?: string
}

export default {
  async list(): Promise<UserGroup[]> {
    return request.get('/admin/groups/')
  },

  async get(id: string): Promise<UserGroup> {
    return request.get(`/admin/groups/${id}`)
  },

  async create(data: UserGroupCreate): Promise<UserGroup> {
    return request.post('/admin/groups/', data)
  },

  async update(id: string, data: Partial<UserGroupCreate>): Promise<UserGroup> {
    return request.put(`/admin/groups/${id}`, data)
  },

  async delete(id: string): Promise<void> {
    return request.delete(`/admin/groups/${id}`)
  },

  async listPermissions(): Promise<Permission[]> {
    return request.get('/admin/groups/permissions/list')
  },

  async assignUser(userId: string, groupId: string): Promise<{ message: string; user: any }> {
    return request.put(`/admin/users/${userId}/group`, { group_id: groupId })
  },

  async removeUserGroup(userId: string): Promise<{ message: string; user: any }> {
    return request.delete(`/admin/users/${userId}/group`)
  }
}
