# 环境配置

## 后端配置 (.env)

在 `backend/` 目录创建 `.env` 文件：

```bash
# 必需配置
APP_SECRET=your-secret-key-min-32-chars-change-in-production
JWT_SECRET=your-jwt-secret-key-min-32-chars-change-in-production

# 数据库
DATABASE_URL=sqlite+aiosqlite:///./data/cloudcodec.db
# 生产环境可使用 PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/cloudcodec

# Redis（任务队列）
REDIS_URL=redis://localhost:6379/0

# 存储
STORAGE_TYPE=local
STORAGE_PATH=./data

# JWT
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# 文件上传
MAX_UPLOAD_SIZE=10737418240
ALLOWED_VIDEO_TYPES=video/mp4,video/x-matroska,video/webm,video/quicktime,video/x-msvideo

# FFmpeg
FFMPEG_PATH=ffmpeg
FFPROBE_PATH=ffprobe
HW_ACCEL_PRIORITY=nvenc,qsv,vaapi,videotoolbox,amf
```

### 配置验证

`app/core/config.py` 使用 Pydantic 验证：
- `APP_SECRET` 和 `JWT_SECRET`: 最小长度 32 字符
- `APP_ENV`: 必须是 `development|production|testing`
- `DATABASE_URL`: 必须以 `sqlite+`, `postgresql+`, 或 `mysql+` 开头
- `APP_URL`: 必须是有效的 URL

## 前端配置

Vite 自动加载以下环境变量：
- `.env` - 所有环境
- `.env.development` - 开发环境
- `.env.production` - 生产环境

### 变量访问

只有以 `VITE_` 开头的变量才能在客户端代码中访问：

```typescript
const apiBase = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const wsBase = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'
```

### 开发代理

`vite.config.ts` 中配置了 API 代理：
```typescript
proxy: {
  '/api': 'http://localhost:8000/api',
  '/ws': {
    target: 'ws://localhost:8000',
    ws: true,
  },
}
```

开发时，前端请求 `/api/*` 会自动代理到后端。

### 默认值

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `VITE_API_BASE_URL` | `/api/v1` | API 基础路径 |
| `VITE_WS_BASE_URL` | `ws://localhost:8000` | WebSocket 地址 |
