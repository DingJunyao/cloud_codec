# 码上转 (CloudCoder) - 系统设计文档

> 创建日期：2026-03-21

## 一、项目概述

### 1.1 项目简介

码上转（CloudCoder）是一个基于 Web 的视频转码服务平台，提供视频上传、转码配置、实时进度监控和结果下载等功能。系统支持多用户管理、批量转码、硬件加速编解码，并提供了完整的权限管理体系。

### 1.2 核心功能

- 用户上传视频，选择预设或自定义转码配置
- 实时查看转码进度和日志
- 批量转码支持
- 多用户管理和权限控制
- 本地文件访问（管理员授权）
- 自动化 API 支持
- 多数据库支持（SQLite/MySQL/PostgreSQL）
- 硬件加速编解码（NVENC/QSV/VAAPI/VideoToolbox/AMF）

### 1.3 系统兼容性

| 平台 | 支持级别 | 备注 |
|------|----------|------|
| Linux | 主要支持 | 包括群晖 DSM |
| Windows | 支持 | 需单独安装 FFmpeg |
| macOS | 支持 | 开发测试环境 |
| Docker | 支持 | 便捷部署方案 |

架构支持：amd64、arm64

---

## 二、技术架构

### 2.1 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端框架 | Vue 3 + TypeScript | 组合式 API，类型安全 |
| UI 组件库 | Element Plus | 成熟的后台管理组件库 |
| 状态管理 | Pinia | Vue 3 官方状态管理 |
| 后端框架 | FastAPI | 高性能异步框架 |
| ORM | SQLAlchemy 2.0 + Alembic | 异步支持，多数据库兼容 |
| 任务队列 | RQ + Redis | 轻量级，功能够用 |
| 实时通信 | WebSocket | 进度推送，日志流 |
| 认证方式 | JWT + Refresh Token | 无状态，API 友好 |
| 转码引擎 | FFmpeg (命令行) | 功能最全，硬件加速支持好 |
| 存储 | 本地 / S3 兼容 | 灵活切换 |
| 数据库 | SQLite / MySQL / PostgreSQL | 默认 SQLite |

### 2.2 项目结构

```
cloud_coder/
├── backend/                    # Python 后端
│   ├── app/
│   │   ├── api/                # API 路由
│   │   │   ├── v1/
│   │   │   │   ├── auth.py     # 认证相关
│   │   │   │   ├── users.py    # 用户管理
│   │   │   │   ├── tasks.py    # 转码任务
│   │   │   │   ├── presets.py  # 预设管理
│   │   │   │   ├── admin.py     # 管理员接口
│   │   │   │   └── external.py  # 自动化 API
│   │   │   └── deps.py         # 依赖注入
│   │   ├── core/               # 核心配置
│   │   │   ├── config.py       # 配置管理
│   │   │   ├── security.py     # 安全相关
│   │   │   └── logging.py      # 日志配置
│   │   ├── models/             # 数据库模型
│   │   │   ├── user.py
│   │   │   ├── task.py
│   │   │   ├── preset.py
│   │   │   └── permission.py
│   │   ├── schemas/            # Pydantic 模型
│   │   ├── services/           # 业务逻辑
│   │   │   ├── storage.py      # 存储抽象
│   │   │   ├── encoder.py      # FFmpeg 封装
│   │   │   ├── hw_accel.py     # 硬件加速检测
│   │   │   └── notification.py # 通知服务
│   │   ├── tasks/              # RQ 任务
│   │   │   └── encode.py       # 转码任务
│   │   └── main.py             # 应用入口
│   ├── alembic/                # 数据库迁移
│   ├── tests/                  # 测试
│   └── requirements.txt
│
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   │   ├── auth/           # 登录注册
│   │   │   ├── tasks/          # 任务管理
│   │   │   ├── presets/        # 预设管理
│   │   │   ├── settings/       # 用户设置
│   │   │   └── admin/          # 管理页面
│   │   ├── components/         # 通用组件
│   │   │   ├── TaskUploader.vue
│   │   │   ├── PresetSelector.vue
│   │   │   ├── EncodeConfigForm.vue
│   │   │   ├── TaskProgressPanel.vue
│   │   │   ├── LogViewer.vue
│   │   │   └── FileManager.vue
│   │   ├── stores/             # Pinia 状态
│   │   │   ├── auth.ts
│   │   │   ├── task.ts
│   │   │   ├── preset.ts
│   │   │   └── settings.ts
│   │   ├── api/                # API 请求封装
│   │   ├── router/             # 路由配置
│   │   ├── utils/              # 工具函数
│   │   └── main.ts
│   └── package.json
│
├── docs/                       # 文档
├── docker-compose.yml          # Docker 部署
├── Dockerfile
└── README.md
```

---

## 三、数据模型设计

### 3.1 实体关系

```
User (用户)
├── 1:N → Task (转码任务)
├── N:1 → UserGroup (用户组)
└── 1:1 → UserSettings (用户设置)

UserGroup (用户组)
├── N:N → Permission (权限)
└── 1:N → User

Task (转码任务)
├── N:1 → User
├── N:1 → Preset (预设配置)
└── 1:1 → TaskResult (转码结果)

Preset (预设)
├── is_builtin: bool (系统预设/用户自定义)
└── config: JSON (编码参数)
```

### 3.2 主要数据表

#### users - 用户表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| username | VARCHAR(50) | 用户名，唯一 |
| email | VARCHAR(255) | 邮箱，唯一 |
| password_hash | VARCHAR(255) | bcrypt 哈希密码 |
| is_active | BOOLEAN | 是否激活 |
| is_admin | BOOLEAN | 是否管理员 |
| group_id | UUID | 用户组 ID |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### user_groups - 用户组表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | VARCHAR(50) | 组名 |
| description | TEXT | 描述 |
| max_file_size | BIGINT | 最大文件大小（字节） |
| result_retention_days | INT | 结果保留天数 |
| local_paths | JSON | 允许的本地路径 |
| created_at | DATETIME | 创建时间 |

#### permissions - 权限表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| code | VARCHAR(50) | 权限代码，唯一 |
| name | VARCHAR(100) | 权限名称 |
| description | TEXT | 描述 |

#### tasks - 任务表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 用户 ID |
| preset_id | UUID | 预设 ID（可为空，自定义配置） |
| status | ENUM | pending/processing/completed/failed/cancelled |
| progress | INT | 进度百分比 |
| source_file | VARCHAR(500) | 源文件路径 |
| source_size | BIGINT | 源文件大小 |
| output_file | VARCHAR(500) | 输出文件路径 |
| output_size | BIGINT | 输出文件大小 |
| config | JSON | 转码配置 |
| error_message | TEXT | 错误信息 |
| created_at | DATETIME | 创建时间 |
| started_at | DATETIME | 开始时间 |
| completed_at | DATETIME | 完成时间 |

#### presets - 预设表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | VARCHAR(100) | 预设名称 |
| is_builtin | BOOLEAN | 是否系统预设 |
| is_default | BOOLEAN | 是否默认预设 |
| created_by | UUID | 创建者 ID（系统预设为空） |
| config | JSON | 编码配置 |
| created_at | DATETIME | 创建时间 |

#### task_logs - 任务日志表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| task_id | UUID | 任务 ID |
| level | VARCHAR(10) | 日志级别 |
| message | TEXT | 日志内容 |
| created_at | DATETIME | 创建时间 |

#### api_keys - API 密钥表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 用户 ID |
| name | VARCHAR(100) | 密钥名称 |
| key_hash | VARCHAR(255) | 密钥哈希 |
| permissions | JSON | 权限范围 |
| ip_whitelist | JSON | IP 白名单 |
| expires_at | DATETIME | 过期时间 |
| last_used_at | DATETIME | 最后使用时间 |
| created_at | DATETIME | 创建时间 |

---

## 四、API 设计

### 4.1 RESTful API 结构

```
/api/v1
├── /auth                        # 认证相关
│   ├── POST /register           # 注册
│   ├── POST /login             # 登录
│   ├── POST /refresh            # 刷新 Token
│   └── POST /logout             # 登出
│
├── /users                       # 用户管理
│   ├── GET  /me                 # 当前用户信息
│   ├── PUT  /me                 # 更新个人信息
│   └── PUT  /me/password        # 修改密码
│
├── /tasks                       # 转码任务
│   ├── GET    /                 # 任务列表
│   ├── POST   /                 # 创建任务
│   ├── GET    /{id}             # 任务详情
│   ├── DELETE /{id}             # 取消/删除任务
│   ├── GET    /{id}/download    # 下载结果
│   └── GET    /{id}/logs        # 获取日志
│
├── /presets                     # 预设管理
│   ├── GET  /                   # 预设列表
│   ├── POST /                   # 创建自定义预设
│   ├── PUT  /{id}               # 更新预设
│   └── DELETE /{id}             # 删除预设
│
├── /files                       # 文件操作（需权限）
│   ├── GET  /browse             # 浏览本地文件
│   └── GET  /preview            # 预览文件信息
│
├── /settings                    # 用户设置
│   ├── GET  /                   # 获取设置
│   └── PUT  /                   # 更新设置
│
├── /admin                       # 管理员接口
│   ├── /users                   # 用户管理
│   ├── /groups                  # 用户组管理
│   ├── /presets                 # 系统预设管理
│   ├── /settings                # 系统设置
│   └── /stats                   # 系统统计
│
└── /external                    # 自动化 API
    ├── POST /tasks              # 创建任务
    ├── GET  /tasks              # 任务列表
    ├── GET  /tasks/{id}         # 任务详情
    ├── GET  /tasks/{id}/download # 下载结果
    ├── DELETE /tasks/{id}       # 取消任务
    └── POST /tasks/batch        # 批量任务
```

### 4.2 WebSocket 接口

```
/ws/{task_id}                    # 任务实时推送

连接参数：
- token: JWT Token

消息格式：
{
  "type": "progress",     // progress | log | status | error
  "data": {
    "percent": 45,
    "fps": 120,
    "speed": "2.5x",
    "eta": 60,
    "frame": 5400,
    "total_frames": 12000
  }
}

{
  "type": "log",
  "data": {
    "line": "frame= 5400 fps=120 q=28.0 size=  123456kB time=00:03:45..."
  }
}

{
  "type": "status",
  "data": {
    "status": "completed",
    "output_size": 123456789,
    "duration": 180
  }
}
```

### 4.3 认证方式

**Web 用户认证：**
```
Header: Authorization: Bearer {access_token}
```

**API Key 认证（自动化 API）：**
```
Header: X-API-Key: {api_key}
或
Header: Authorization: Bearer {api_key}
```

---

## 五、转码系统设计

### 5.1 硬件加速检测

系统启动时自动检测可用的硬件加速方案：

```python
# 检测优先级（可由管理员配置）
HW_ACCEL_PRIORITY = [
    'nvenc',      # NVIDIA GPU
    'qsv',        # Intel Quick Sync
    'vaapi',      # Linux VAAPI
    'videotoolbox', # macOS
    'amf',        # AMD
]

# 支持的编解码器映射
ENCODER_MAP = {
    'h264': {
        'nvenc': 'h264_nvenc',
        'qsv': 'h264_qsv',
        'vaapi': 'h264_vaapi',
        'videotoolbox': 'h264_videotoolbox',
        'amf': 'h264_amf',
        'software': 'libx264',
    },
    'h265': {
        'nvenc': 'hevc_nvenc',
        'qsv': 'hevc_qsv',
        'vaapi': 'hevc_vaapi',
        'videotoolbox': 'hevc_videotoolbox',
        'amf': 'hevc_amf',
        'software': 'libx265',
    },
    # ... 更多编解码器
}
```

### 5.2 任务流程

```
1. 用户上传视频
   └─→ 后端验证文件（类型、大小）
   └─→ 创建 Task 记录（status: pending）
   └─→ 存储到 /uploads/{user_id}/{task_id}/source.{ext}

2. 入队处理
   └─→ 根据预设 + 硬件加速配置构建 FFmpeg 命令
   └─→ RQ.enqueue(encode_task, task_id)
   └─→ 返回 task_id，前端建立 WebSocket 连接

3. Worker 执行
   └─→ 更新 status 为 processing
   └─→ 调用 FFmpeg，使用 -progress 参数获取进度
   └─→ 解析进度输出，通过 WebSocket 推送
   └─→ 完成后：
       ├─→ 成功：存储结果，status: completed
       └─→ 失败：记录错误，status: failed
   └─→ 发送通知（如已配置）

4. 用户下载
   └─→ WebSocket 收到完成通知
   └─→ 调用 GET /tasks/{id}/download 获取文件
```

### 5.3 FFmpeg 命令构建

```python
def build_ffmpeg_command(task: Task, hw_accel: str) -> list:
    """构建 FFmpeg 命令"""
    config = task.config
    encoder = get_encoder(config.video.codec, hw_accel)

    cmd = [
        'ffmpeg',
        '-i', task.source_file,
        '-c:v', encoder,
        '-preset', config.video.preset,
        # ... 根据编码器类型添加参数
        '-c:a', config.audio.codec,
        '-b:a', config.audio.bitrate,
        # ... 滤镜
        '-y', task.output_file,
        '-progress', 'pipe:1',  # 进度输出
    ]

    return cmd
```

---

## 六、存储系统设计

### 6.1 存储抽象接口

```python
from abc import ABC, abstractmethod

class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    async def save(self, path: str, data: bytes) -> str:
        """保存文件，返回路径"""
        pass

    @abstractmethod
    async def read(self, path: str) -> bytes:
        """读取文件"""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """检查文件是否存在"""
        pass

    @abstractmethod
    async def get_url(self, path: str, expires: int = 3600) -> str:
        """获取下载链接"""
        pass

    @abstractmethod
    async def list_files(self, prefix: str) -> list:
        """列出文件"""
        pass

    @abstractmethod
    async def get_size(self, path: str) -> int:
        """获取文件大小"""
        pass
```

### 6.2 文件存储路径规范

```
本地存储结构：
/data/
├── uploads/                    # 用户上传
│   └── {user_id}/
│       └── {task_id}/
│           └── source.{ext}
├── results/                    # 转码结果
│   └── {user_id}/
│       └── {task_id}/
│           └── output.{ext}
├── logs/                       # 任务日志
│   └── {task_id}.log
└── temp/                       # 临时文件
    └── {task_id}/

对象存储结构（S3 兼容）：
bucket: cloud-coder
├── uploads/{user_id}/{task_id}/
├── results/{user_id}/{task_id}/
└── logs/{task_id}.log
```

### 6.3 文件清理策略

```python
# 定时任务清理过期文件
@cron('0 3 * * *')  # 每天凌晨 3 点
async def cleanup_expired_files():
    """清理过期文件"""
    retention_config = get_retention_config()

    for group in get_user_groups():
        # 根据用户组配置清理
        days = retention_config.get(group.id, 7)
        cutoff = datetime.now() - timedelta(days=days)

        expired_tasks = get_tasks_completed_before(cutoff)
        for task in expired_tasks:
            await delete_task_files(task)
```

---

## 七、权限系统设计

### 7.1 权限定义

```python
from enum import Enum

class Permission(Enum):
    # 任务相关
    TASK_CREATE = "task:create"           # 创建转码任务
    TASK_BATCH = "task:batch"             # 批量转码
    TASK_API = "task:api"                # 自动化 API 访问
    TASK_VIEW_ALL = "task:view_all"      # 查看所有用户任务

    # 文件相关
    FILE_UPLOAD = "file:upload"          # 上传文件
    FILE_LOCAL = "file:local"            # 本地文件访问
    FILE_LOCAL_WRITE = "file:local_write"  # 本地文件写入

    # 预设相关
    PRESET_CUSTOM = "preset:custom"      # 创建自定义预设

    # 管理相关
    ADMIN_USERS = "admin:users"          # 用户管理
    ADMIN_GROUPS = "admin:groups"        # 用户组管理
    ADMIN_PRESETS = "admin:presets"      # 系统预设管理
    ADMIN_SYSTEM = "admin:system"        # 系统设置
```

### 7.2 用户组示例

```json
{
  "name": "普通用户",
  "permissions": [
    "task:create",
    "file:upload",
    "preset:custom"
  ],
  "settings": {
    "max_file_size": 1073741824,
    "result_retention_days": 7,
    "available_presets": ["default", "web", "mobile"]
  }
}

{
  "name": "高级用户",
  "permissions": [
    "task:create",
    "task:batch",
    "task:api",
    "file:upload",
    "file:local",
    "file:local_write",
    "preset:custom"
  ],
  "settings": {
    "max_file_size": 10737418240,
    "result_retention_days": 30,
    "local_paths": ["/home/user/videos", "/mnt/nas"]
  }
}

{
  "name": "管理员",
  "permissions": [
    "task:create",
    "task:batch",
    "task:api",
    "task:view_all",
    "file:upload",
    "file:local",
    "file:local_write",
    "preset:custom",
    "admin:users",
    "admin:groups",
    "admin:presets",
    "admin:system"
  ],
  "settings": {
    "max_file_size": null,
    "result_retention_days": null,
    "local_paths": null
  }
}
```

### 7.3 本地文件访问控制

```python
def check_path_permission(user: User, path: str, operation: str) -> bool:
    """检查用户是否有权限访问指定路径"""
    if not user.has_permission(f'file:local'):
        return False

    if operation == 'write' and not user.has_permission('file:local_write'):
        return False

    # 检查路径是否在允许列表内
    allowed_paths = user.group.settings.get('local_paths', [])
    normalized_path = os.path.normpath(path)

    for allowed in allowed_paths:
        normalized_allowed = os.path.normpath(allowed)
        if normalized_path.startswith(normalized_allowed):
            return True

    return False
```

---

## 八、预设系统设计

### 8.1 预设数据结构

```json
{
  "id": "preset_uuid",
  "name": "H.264 1080p 高质量",
  "description": "适用于大多数场景的高质量预设",
  "is_builtin": true,
  "is_default": false,
  "created_by": null,
  "config": {
    "video": {
      "codec": "h264",
      "codec_options": {
        "preset": "medium",
        "crf": 23,
        "profile": "high",
        "level": "4.1"
      },
      "width": 1920,
      "height": 1080,
      "fps": null,
      "hw_accel": "auto"
    },
    "audio": {
      "codec": "aac",
      "bitrate": "128k",
      "channels": 2,
      "sample_rate": 48000
    },
    "container": "mp4",
    "filters": [
      {"type": "scale", "width": -2, "height": 1080}
    ],
    "metadata": {
      "remove_original": false,
      "add_tags": {}
    }
  }
}
```

### 8.2 系统内置预设

| 预设名称 | 视频编码 | 音频编码 | 分辨率 | 用途 |
|---------|----------|----------|--------|------|
| 通用兼容 | H.264 | AAC | 原始 | 最大兼容性 |
| Web 优化 | H.264 | AAC | 1080p | 网页播放 |
| 移动设备 | H.264 | AAC | 720p | 手机平板 |
| 压缩存储 | H.265 | AAC | 原始 | 节省空间 |
| 快速转码 | H.264 | AAC | 原始 | 速度优先 |
| 4K 优化 | H.265 | AAC | 2160p | 4K 视频 |

### 8.3 预设管理逻辑

```
预设权限：
├── 系统预设 (is_builtin=true)
│   ├── 所有用户可见
│   ├── 管理员可启用/禁用
│   ├── 管理员可设置默认预设
│   └── 用户不可修改
│
└── 用户预设 (is_builtin=false)
    ├── 仅创建者可见
    ├── 可基于系统预设克隆
    ├── 可自定义所有参数
    └── 可删除自己的预设

预设验证：
├── 编解码器兼容性（容器支持）
├── 参数合法性（范围检查）
└── 硬件加速可用性提示
```

---

## 九、安全设计

### 9.1 认证安全

```
密码处理：
├── 前端：SHA256(password) 传输
├── 后端：bcrypt hash 存储
├── HTTPS 强制（生产环境）
└── 登录失败限制：5 次/15分钟

JWT 配置：
├── Access Token：30 分钟有效期
├── Refresh Token：7 天有效期（可配置）
├── Refresh Token 数据库存储（可撤销）
└── 敏感操作：重新验证密码
```

### 9.2 文件安全

```python
ALLOWED_MIME_TYPES = [
    'video/mp4', 'video/x-matroska', 'video/webm',
    'video/quicktime', 'video/x-msvideo', 'video/x-mpegts',
    # ... 更多视频格式
]

MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 默认 10GB

async def validate_upload_file(file: UploadFile, user: User) -> bool:
    """验证上传文件"""
    # 1. 检查文件大小
    if file.size > user.group.max_file_size:
        raise FileTooLargeError()

    # 2. 检查 MIME 类型
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise InvalidFileTypeError()

    # 3. 检查文件头（防止伪造）
    header = await file.read(1024)
    await file.seek(0)
    if not validate_file_header(header):
        raise InvalidFileTypeError()

    # 4. 安全文件名处理
    safe_filename = secure_filename(file.filename)

    return True
```

### 9.3 API 安全

```python
# API Key 验证
@router.post("/external/tasks")
async def create_task_external(
    request: Request,
    api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    key = validate_api_key(api_key, db)

    # 检查 IP 白名单
    if key.ip_whitelist:
        client_ip = request.client.host
        if client_ip not in key.ip_whitelist:
            raise ForbiddenError()

    # 检查权限
    if 'task:create' not in key.permissions:
        raise ForbiddenError()

    # 更新最后使用时间
    key.last_used_at = datetime.now()
    db.commit()

    return await create_task(...)

# 请求频率限制
@limiter.limit("100/minute")
async def api_endpoint():
    pass
```

---

## 十、通知系统设计

### 10.1 通知架构

```
通知渠道：
├── Email（MVP 实现）
├── Webhook（后续）
├── Telegram（后续）
└── 企业微信/钉钉（后续）

触发事件：
├── task.completed    # 转码完成
├── task.failed       # 转码失败
├── storage.warning   # 存储空间告警
└── system.error      # 系统错误（管理员）
```

### 10.2 邮件配置

```python
class EmailConfig(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    use_tls: bool = True
    from_address: str

class EmailService:
    async def send_task_completed(self, user: User, task: Task):
        """发送任务完成通知"""
        subject = f"转码完成 - {task.source_file}"
        body = f"""
        您的转码任务已完成：

        源文件：{task.source_file}
        输出文件：{task.output_file}
        耗时：{task.duration}秒

        请登录系统下载结果。
        """
        await self.send(user.email, subject, body)

    async def send_task_failed(self, user: User, task: Task):
        """发送任务失败通知"""
        subject = f"转码失败 - {task.source_file}"
        body = f"""
        您的转码任务失败：

        源文件：{task.source_file}
        错误信息：{task.error_message}

        请检查文件格式或联系管理员。
        """
        await self.send(user.email, subject, body)
```

### 10.3 用户通知设置

```json
{
  "notifications": {
    "email_enabled": true,
    "email_address": "user@example.com",
    "events": {
      "task_completed": true,
      "task_failed": true
    }
  }
}
```

---

## 十一、部署方案

### 11.1 源码安装

**环境要求：**
- Python 3.10+
- Node.js 18+
- FFmpeg 5.0+（需编译硬件加速支持）
- Redis 6.0+
- 数据库：SQLite（默认）/ MySQL 8.0+ / PostgreSQL 14+

**安装步骤：**

```bash
# 1. 克隆仓库
git clone https://github.com/xxx/cloud-coder.git
cd cloud-coder

# 2. 后端安装
cd backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 3. 前端安装
cd ../frontend
npm install
npm run build

# 4. 配置
cp .env.example .env
# 编辑 .env 填写配置

# 5. 数据库初始化
cd ../backend
alembic upgrade head

# 6. 启动服务
# 启动 Worker
python -m app.worker

# 另一个终端启动 Web 服务
python -m app.main
```

### 11.2 Docker 部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/cloudcoder
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - db

  worker:
    build: .
    command: python -m app.worker
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/cloudcoder
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - db
    # GPU 支持（可选）
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=cloudcoder

volumes:
  redis_data:
  postgres_data:
```

### 11.3 配置文件示例

```bash
# .env
# 应用配置
APP_NAME=码上转
APP_ENV=production
APP_SECRET=your-secret-key
APP_URL=https://your-domain.com

# 数据库配置
DATABASE_URL=sqlite:///./data/cloudcoder.db
# DATABASE_URL=postgresql://user:pass@localhost:5432/cloudcoder
# DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/cloudcoder

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# 存储配置
STORAGE_TYPE=local  # local 或 s3
STORAGE_PATH=/data

# S3 配置（如使用）
# S3_ENDPOINT=https://s3.example.com
# S3_BUCKET=cloudcoder
# S3_ACCESS_KEY=xxx
# S3_SECRET_KEY=xxx

# 邮件配置
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=xxx
SMTP_FROM=码上转 <noreply@example.com>

# JWT 配置
JWT_SECRET=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# FFmpeg 配置
FFMPEG_PATH=ffmpeg
FFPROBE_PATH=ffprobe
HW_ACCEL_PRIORITY=nvenc,qsv,vaapi
```

---

## 十二、MVP 实现范围

### 第一阶段：核心功能

1. **用户系统**
   - 用户注册、登录
   - JWT 认证
   - 基础用户组权限

2. **转码功能**
   - 视频上传
   - 预设选择（系统预设）
   - FFmpeg 转码
   - 硬件加速检测
   - 实时进度和日志（WebSocket）
   - 结果下载

3. **基础管理**
   - 简单的管理员界面
   - 用户组配置

### 第二阶段：完善功能

1. **预设管理**
   - 用户自定义预设
   - 预设克隆

2. **批量转码**
   - 批量上传
   - 统一预设/单独配置

3. **本地文件访问**
   - 文件浏览器
   - 本地路径权限控制

### 第三阶段：高级功能

1. **自动化 API**
   - API Key 管理
   - Webhook 回调

2. **通知系统**
   - 邮件通知
   - 用户通知设置

3. **高级管理**
   - 完整的权限管理
   - 系统监控
   - 存储空间管理

---

## 附录：技术决策记录

| 决策 | 选择 | 原因 |
|------|------|------|
| 后端框架 | FastAPI | 异步支持好，WebSocket 原生，自动 API 文档 |
| 前端框架 | Vue 3 | 中文社区活跃，Element Plus 成熟 |
| 任务队列 | RQ | 轻量够用，Redis 依赖简单 |
| ORM | SQLAlchemy | 成熟稳定，多数据库支持 |
| 认证方式 | JWT + Refresh Token | 无状态，API 友好，安全性好 |
| 存储方案 | 混合（本地 + S3） | 灵活适应不同部署场景 |
| FFmpeg 集成 | 命令行调用 | 功能最全，硬件加速支持好 |
| 实时推送 | WebSocket | 双向通信，适合进度和日志流 |