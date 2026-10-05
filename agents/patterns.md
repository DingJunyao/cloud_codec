# 关键模式和最佳实践

## 后端模式

### Async/Await

所有数据库操作使用异步函数：

```python
async def get_user(db: AsyncSession, user_id: str):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

### 依赖注入

使用 `Depends()` 注入依赖：

```python
from fastapi import Depends
from app.database import get_db
from app.api.deps import get_current_user

@router.get("/users/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return current_user
```

**常用依赖**:
- `Depends(get_db)` - 数据库会话
- `Depends(get_current_user)` - 当前认证用户
- `Depends(get_current_admin)` - 当前管理员用户

### Pydantic 模型

所有请求/响应使用 Pydantic 模型：

```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str | None

    class Config:
        from_attributes = True  # 支持 ORM 模型
```

### 服务层分离

业务逻辑放在 `app/services/` 中，不在路由中：

```python
# app/services/user_service.py
class UserService:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: str):
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

# app/api/v1/users.py
@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await UserService.get_by_id(db, user_id)
```

## 前端模式

### Composition API

使用 `<script setup>` 语法：

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(false)

const isAdmin = computed(() => authStore.user?.is_admin ?? false)

onMounted(() => {
  authStore.restoreSession()
})
</script>
```

### Pinia Stores

使用 setup 语法定义 stores：

```typescript
export const useTasksStore = defineStore('tasks', () => {
  // State
  const tasks = ref<Task[]>([])

  // Actions
  async function fetchTasks() {
    const data = await tasksApi.list()
    tasks.value = data
  }

  return {
    tasks,
    fetchTasks,
  }
})
```

### 类型化 API 客户端

在 `src/api/` 中定义类型化的 API 客户端：

```typescript
import request from './request'

export interface Task {
  id: string
  name: string
  status: 'pending' | 'processing' | 'completed'
}

export default {
  async list(): Promise<Task[]> {
    return request.get('/tasks/')
  },

  async create(data: TaskCreate): Promise<Task> {
    return request.post('/tasks/', data)
  },
}
```

## FFmpeg 命令构建

使用链式 API 构建 FFmpeg 命令：

```python
from app.services.ffmpeg.command import FFmpegCommandBuilder

cmd = (FFmpegCommandBuilder()
    .input("input.mp4")
    .overwrite()
    .video_codec("libx264", hw_accel="auto")
    .video_preset("medium")
    .video_crf(23)
    .video_scale(1920, 1080)
    .audio_codec("aac")
    .audio_bitrate("128k")
    .build())
# ['ffmpeg', '-i', 'input.mp4', '-y', '-c:v', 'libx264', ...]
```

硬件加速自动检测（优先级：nvenc > qsv > vaapi > videotoolbox > amf）。

## 错误处理

### 后端

```python
from fastapi import HTTPException

@router.post("/tasks")
async def create_task(data: TaskCreate):
    preset = await get_preset(data.preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="预设不存在")
    return await create_task(data)
```

### 前端

Axios 拦截器统一处理错误（`src/api/request.ts`）：
- 401: 自动登出并跳转登录
- 403: 显示"没有权限"通知
- 404: 显示"资源不存在"通知
- 500: 显示"服务器错误"通知
