# CloudCodec (码上转)

一个现代化的视频转码服务平台，支持自定义转码预设、实时进度跟踪和 WebSocket 通信。

## 功能特性

- **用户认证** - JWT Token 认证，支持自动刷新
- **视频转码** - 基于 FFmpeg，支持多种格式和硬件加速
- **实时进度** - WebSocket 推送转码进度和状态
- **预设管理** - 系统预设 + 用户自定义预设
- **任务管理** - 创建、查看、取消任务，状态实时更新
- **管理后台** - 用户管理、任务监控、系统仪表盘

## 技术栈

### 后端

| 技术 | 版本 | 说明 |
|------|------|------|
| FastAPI | 0.109+ | Web 框架 |
| SQLAlchemy | 2.0 | ORM (async) |
| RQ | 1.15+ | 任务队列 (Redis) |
| FFmpeg | - | 视频转码 |
| WebSocket | - | 实时通信 |

### 前端

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.4+ | 前端框架 |
| TypeScript | 5.3+ | 类型支持 |
| Vite | 5.0+ | 构建工具 |
| Element Plus | 2.5+ | UI 组件库 |
| Pinia | 2.1+ | 状态管理 |
| Axios | 1.6+ | HTTP 客户端 |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Redis 服务器
- FFmpeg (支持硬件加速可选)

### 后端安装

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置必要参数

# 初始化数据库
python scripts/init_db.py

# 启动服务
uvicorn app.main:app --reload
```

### 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动开发服务器
npm run dev
```

### 启动 Worker

```bash
cd backend
source .venv/bin/activate

# 启动 RQ Worker
python -m app.worker
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |

## 配置说明

### 后端环境变量

```bash
# 应用配置
APP_NAME=码上转
APP_ENV=development
APP_SECRET=your-secret-key-min-32-chars
APP_URL=http://localhost:8000

# 数据库 (支持 SQLite / PostgreSQL / MySQL)
DATABASE_URL=sqlite+aiosqlite:///./data/cloudcodec.db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET=your-jwt-secret-min-32-chars
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 存储
STORAGE_TYPE=local
STORAGE_PATH=./data

# FFmpeg (硬件加速)
HW_ACCEL_PRIORITY=nvenc,qsv,vaapi,videotoolbox,amf
```

### 前端环境变量

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=CloudCodec - 视频转码服务
```

## 项目结构

```
cloud_coder/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic 模型
│   │   ├── services/       # 业务逻辑
│   │   ├── tasks/          # RQ 任务
│   │   └── main.py         # 应用入口
│   ├── alembic/            # 数据库迁移
│   └── requirements.txt
│
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── api/           # API 调用
│   │   ├── components/    # 组件
│   │   ├── router/        # 路由配置
│   │   ├── stores/        # Pinia 状态
│   │   ├── styles/        # 样式文件
│   │   ├── utils/         # 工具函数
│   │   └── views/         # 页面组件
│   └── package.json
│
└── docs/                   # 文档
    └── plans/              # 开发计划
```

## 开发命令

### 后端

```bash
# 启动开发服务器
uvicorn app.main:app --reload

# 数据库迁移
alembic revision --autogenerate -m "description"
alembic upgrade head

# 启动 Worker
python -m app.worker
```

### 前端

```bash
# 开发
npm run dev

# 构建
npm run build

# 预览构建结果
npm run preview
```

## 硬件加速支持

支持以下硬件加速方式（按优先级自动检测）：

1. **NVIDIA NVENC** - NVIDIA GPU 编码
2. **Intel QSV** - Intel Quick Sync Video
3. **VAAPI** - Linux VA-API
4. **VideoToolbox** - macOS
5. **AMD AMF** - AMD GPU

## 支持的视频格式

- MP4 (H.264/H.265)
- MKV
- WebM
- MOV
- AVI

## 许可证

MIT License
