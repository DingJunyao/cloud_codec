# 项目概述

CloudCoder (码上转) 是一个视频转码服务平台，支持用户自定义转码预设、实时进度跟踪和 WebSocket 通信。

## 技术栈

### 后端
- **框架**: FastAPI 0.109+
- **数据库**: SQLAlchemy 2.0 (async) + aiosqlite/PostgreSQL
- **认证**: JWT + passlib
- **转码**: FFmpeg (支持硬件加速)
- **任务队列**: RQ (Redis Queue)
- **WebSocket**: 实时进度推送

### 前端
- **框架**: Vue 3.4+ (Composition API + TypeScript)
- **构建**: Vite 5
- **路由**: Vue Router 4
- **状态管理**: Pinia
- **UI**: Element Plus
- **HTTP**: Axios

## 核心功能

1. **用户认证** - JWT Token 认证，自动刷新
2. **视频转码** - 支持多种格式，自定义预设
3. **实时进度** - WebSocket 推送转码进度
4. **预设管理** - 系统预设 + 用户自定义预设
5. **任务管理** - 创建/查看/取消任务，状态实时更新

## 快速访问

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |
