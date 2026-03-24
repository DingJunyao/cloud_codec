<template>
  <div class="group-management">
    <div class="header">
      <h2>用户组管理</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新建用户组
      </el-button>
    </div>

    <el-table :data="groups" stripe v-loading="loading">
      <el-table-column prop="name" label="用户组名称" width="200" />
      <el-table-column prop="description" label="描述" />
      <el-table-column prop="user_count" label="用户数量" width="100" align="center" />
      <el-table-column label="文件大小限制" width="140">
        <template #default="{ row }">
          {{ row.max_file_size ? formatSize(row.max_file_size) : '无限制' }}
        </template>
      </el-table-column>
      <el-table-column label="存储限制" width="140">
        <template #default="{ row }">
          {{ row.max_storage ? formatSize(row.max_storage) : '无限制' }}
        </template>
      </el-table-column>
      <el-table-column label="保留天数" width="100">
        <template #default="{ row }">
          {{ row.result_retention_days ? `${row.result_retention_days} 天` : '永久' }}
        </template>
      </el-table-column>
      <el-table-column label="API 访问" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.api_access_enabled ? 'success' : 'info'" size="small">
            {{ row.api_access_enabled ? '允许' : '禁止' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新建用户组' : '编辑用户组'"
      width="700px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="140px">
        <el-form-item label="用户组名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入用户组名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="请输入用户组描述"
          />
        </el-form-item>
        <el-form-item label="最大文件大小">
          <el-input-number
            v-model="form.max_file_size"
            :min="0"
            :step="1024 * 1024 * 1024"
            :precision="0"
            placeholder="0 表示无限制"
            style="width: 100%"
          />
          <div class="form-tip">字节 (0 表示无限制，建议单位：GB = 1073741824 字节)</div>
        </el-form-item>
        <el-form-item label="最大存储空间">
          <el-input-number
            v-model="form.max_storage"
            :min="0"
            :step="1024 * 1024 * 1024"
            :precision="0"
            placeholder="0 表示无限制"
            style="width: 100%"
          />
          <div class="form-tip">字节 (0 表示无限制，建议单位：GB = 1073741824 字节)</div>
        </el-form-item>
        <el-form-item label="结果保留天数">
          <el-input-number
            v-model="form.result_retention_days"
            :min="0"
            :precision="0"
            placeholder="0 表示永久保留"
            style="width: 100%"
          />
          <div class="form-tip">天 (0 表示永久保留)</div>
        </el-form-item>
        <el-form-item label="本地路径限制">
          <el-input
            v-model="localPathsText"
            type="textarea"
            :rows="3"
            placeholder="每行一个路径，如 /mnt/media"
          />
          <div class="form-tip">每行一个路径，留空表示不限制</div>
        </el-form-item>
        <el-form-item label="允许 API 访问">
          <el-switch v-model="form.api_access_enabled" />
          <div class="form-tip">开启后用户组内的用户可以通过 API 访问</div>
        </el-form-item>
        <el-form-item label="启用邮件通知">
          <el-switch v-model="form.email_enabled" />
          <div class="form-tip">开启后用户组内的用户会收到邮件通知</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import groupsApi from '@/api/groups'
import type { UserGroup, UserGroupCreate } from '@/api/groups'

const groups = ref<UserGroup[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const submitting = ref(false)
const currentGroup = ref<UserGroup | null>(null)
const formRef = ref<FormInstance>()

const form = ref<UserGroupCreate>({
  name: '',
  description: '',
  max_file_size: null,
  max_storage: null,
  result_retention_days: null,
  local_paths: [],
  api_access_enabled: false,
  email_enabled: false
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入用户组名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ]
}

const localPathsText = computed({
  get: () => form.value.local_paths?.join('\n') || '',
  set: (val: string) => {
    form.value.local_paths = val.split('\n').filter(p => p.trim())
  }
})

const fetchGroups = async () => {
  loading.value = true
  try {
    groups.value = await groupsApi.list()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  dialogMode.value = 'create'
  currentGroup.value = null
  resetForm()
  dialogVisible.value = true
}

const openEditDialog = (group: UserGroup) => {
  dialogMode.value = 'edit'
  currentGroup.value = group
  form.value = {
    name: group.name,
    description: group.description || '',
    max_file_size: group.max_file_size || null,
    max_storage: group.max_storage || null,
    result_retention_days: group.result_retention_days || null,
    local_paths: group.local_paths || [],
    api_access_enabled: group.api_access_enabled,
    email_enabled: group.email_enabled
  }
  dialogVisible.value = true
}

const resetForm = () => {
  form.value = {
    name: '',
    description: '',
    max_file_size: null,
    max_storage: null,
    result_retention_days: null,
    local_paths: [],
    api_access_enabled: false,
    email_enabled: false
  }
  formRef.value?.clearValidate()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    if (dialogMode.value === 'create') {
      await groupsApi.create(form.value)
      ElMessage.success('创建成功')
    } else {
      await groupsApi.update(currentGroup.value!.id, form.value)
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    await fetchGroups()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (group: UserGroup) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户组 "${group.name}" 吗？${group.user_count > 0 ? `该组内有 ${group.user_count} 个用户，删除后这些用户将不再属于任何组。` : ''}`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )
    await groupsApi.delete(group.id)
    ElMessage.success('删除成功')
    await fetchGroups()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.response?.data?.detail || '删除失败')
    }
  }
}

const formatSize = (bytes: number) => {
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

onMounted(fetchGroups)
</script>

<style scoped>
.group-management {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
  line-height: 1.5;
}
</style>
