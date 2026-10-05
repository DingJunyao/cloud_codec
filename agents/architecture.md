# 架构详解

## 后端结构

### 入口点
**`backend/app/main.py`**
- 应用生命周期管理 (`@asynccontextmanager` lifespan)
- CORS 中间件配置
- 自定义中间件：`RequestLoggingMiddleware`, `TimingMiddleware`
- 路由聚合：`app.api.v1.api_router` 挂载到 `/api/v1`

### 数据库层
**`backend/app/database.py`**
- Async SQLAlchemy 2.0 + `aiosqlite` (可切换 PostgreSQL/MySQL)
- 会话管理：`get_db()` 异步生成器
- 所有模型继承自：`Base`, `TimestampMixin`, `UUIDMixin`

**模型** (`backend/app/models/`):
- `User` - 用户模型，包含 `UserRole` 枚举
- `UserGroup` - 用户组，权限和配额管理
- `Permission` - 权限模型
- `Task` - 转码任务，包含 `TaskStatus` 枚举
- `Preset` - 转码预设

### 配置
**`backend/app/core/config.py`**
- Pydantic Settings，从 `.env` 文件加载
- 关键配置：`DATABASE_URL`, `JWT_SECRET`, `STORAGE_PATH`, `FFMPEG_PATH`
- 使用 `@field_validator` 进行验证
- 属性方法：`CORS_ORIGINS_LIST`, `ALLOWED_VIDEO_TYPES_LIST`, `HW_ACCEL_LIST`

### API 路由
**`backend/app/api/v1/`**
- `auth.py` - 登录/注册端点
- `users.py` - 用户资料管理
- 其他路由（tasks, presets, upload, download）存在但当前在 `__init__.py` 中被注释

**注意**: 新增路由需要在 `app/api/v1/__init__.py` 中注册

### 服务层
**`backend/app/services/`**
- `storage/` - 抽象存储后端（本地/S3 工厂模式）
  - `base.py` - `StorageBackend` 接口
  - `local.py` - 本地文件系统实现
  - `factory.py` - `get_storage()` 单例
- `ffmpeg/` - FFmpeg 命令构建器
  - `command.py` - 链式 API 构建命令
  - `base.py` - 编码器和硬件加速检测
- `user_service.py` - 用户 CRUD 操作
- `task_service.py` - 任务 CRUD 操作

### 后台任务
**`backend/app/tasks/`**
- `encode.py` - RQ worker 函数 `encode_task()`
- `websocket.py` - WebSocket 连接管理和广播

## 前端结构

### 入口点
**`frontend/src/main.ts`**
- Vue 3 + Pinia + Element Plus 初始化
- 路由集成和认证守卫

### 路由
**`frontend/src/router/index.ts`**
- 路由级认证：`meta.requiresAuth`
- 懒加载组件：`import()`
- 认证守卫：未认证重定向到 `/login`

### 状态管理
**`frontend/src/stores/`**
- `auth.ts` - 用户认证状态，token 管理
- `tasks.ts` - 任务状态和操作
- `presets.ts` - 预设状态和操作

### API 层
**`frontend/src/api/`**
- `request.ts` - Axios 实例
  - 自动注入 `Authorization: Bearer <token>`
  - 全局错误处理（Element Plus 通知）
  - 401 自动登出重定向
- `tasks.ts`, `presets.ts`, `upload.ts` - 类型化 API 客户端

### 路径别名
- `@` → `src/` (在 `vite.config.ts` 中配置)
- 使用 ESM 导入语法：`import { foo } from '@/bar'`

**重要**: 只使用 `.ts` 文件。删除重复的 `.js` 文件以避免冲突（Vite 可能优先加载 `.js`）
