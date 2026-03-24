# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 快速开始

```bash
# 后端 API
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Worker（必须在后台运行）
cd backend
nohup python -m app.worker > /tmp/worker.log 2>&1 &
tail -f /tmp/worker.log  # 查看日志

# 前端
cd frontend
npm install
npm run dev
```

**访问**: 前端 http://localhost:5173 | 后端 http://localhost:8000 | API 文档 http://localhost:8000/docs

⚠️ **Worker 注意事项**：
- 必须使用 `nohup` 或 `screen` 在后台运行
- 不要在前台终端运行（避免 Ctrl+Z 暂停进程）
- 详细说明见 [`cc/task-queue.md`](cc/task-queue.md)

---

## 开发情况

本项目为 monorepo 项目，包含前端和后端。

### 前端

技术栈：TypeScrPt + Vue + Element UI + Vite

目录：`frontend`，所有前端相关操作均在此目录下进行。

开发 URL：`http://localhost:5173`

通常会打开浏览器调试。如有需要，可以使用 Chrome 开发者工具 MCP 查看页面情况，操作页面。由于一般情况下已经打开了页面，所以不要使用 Playwright。开发者在 Windows 下使用 Edge 浏览器，在 Linux 下使用 Chromium 浏览器。

响应式设计。开发时要兼顾不同地图引擎和桌面、移动端的体验。

所有前端的修改都必须确保构建通过。

### 后端

技术栈：Python + FastAPI

目录：`backend`，所有后端相关操作均在此目录下进行，并且使用虚拟环境。

虚拟环境：先找 `conda` 下的 `cloud_coder` 环境，没有则使用项目根目录下的 `.venv` 下的环境。

所有后端的修改都必须确保无语法错误。

### 数据库

数据库：`backend/.env` 文件中指定。一般情况下为 `backend/data/cloudcodec.db`。

数据库操作优先使用相应的 MCP。

开发过程中不要自行修改数据库，除非开发者明确允许此操作。

表结构需要变动时，除了维护 alembic 外，还需要提供对应的 SQL 脚本，包括一下数据库引擎的版本：

- SQLite
- MySQL
- PostgreSQL

### 测试

所有操作均需确保无语法层面上的报错，构建、编译通过。

不要在对话中启动服务，因为我已经启动了自动重载的前端、后端服务。

### 记录要点

当某项开发工作完成、告一段落或有关键性进展时，需要自动记录要点。用户要求记录要点时，也要记录。

要点按照以下的详细文档索引记录。

注意：为了节约 token，即便用户要求记录到 CLAUDE.md，也要按照下面的详细文档索引记录。

## 📚 详细文档索引

详细文档已拆分到 `cc/` 目录，按需读取：

| 文件 | 内容 |
|------|------|
| [`cc/overview.md`](cc/overview.md) | 项目概述、技术栈、核心功能 |
| [`cc/commands.md`](cc/commands.md) | 开发命令、启动、构建、迁移 |
| [`cc/architecture.md`](cc/architecture.md) | 后端/前端架构详解、目录结构 |
| [`cc/environment.md`](cc/environment.md) | 环境配置、.env 变量、默认值 |
| [`cc/patterns.md`](cc/patterns.md) | 代码模式、最佳实践、约定 |
| [`cc/troubleshooting.md`](cc/troubleshooting.md) | 常见问题及解决方案 |
| [`cc/database.md`](cc/database.md) | 数据库使用、Async Session、迁移 |
| [`cc/task-queue.md`](cc/task-queue.md) | RQ 任务队列、Worker、监控 |

---

## ⚠️ 关键注意事项

### 文件类型冲突
**前端只使用 `.ts` 文件**。删除任何 `.js` 重复文件（`vite.config.js` 等），Vite 可能优先加载 `.js` 导致别名解析失败。

### 路径别名
`@` → `src/`，仅在 `.ts` 文件中有效。确保 `vite.config.ts` 存在且 `vite.config.js` 不存在。

### 环境变量
后端需要 `.env` 文件，最少配置：
```bash
APP_SECRET=min-32-chars-secret
JWT_SECRET=min-32-chars-secret
DATABASE_URL=sqlite+aiosqlite:///./data/cloudcodec.db
```

### Async/Await
所有数据库操作必须使用 `async def` 和 `await`：
```python
async def get_user(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

---

## 🔧 快速参考

### 依赖注入
```python
# 数据库会话
db: AsyncSession = Depends(get_db)

# 当前用户
current_user: User = Depends(get_current_user)

# 管理员用户
admin: User = Depends(get_current_admin)
```

### 路由注册
在 `backend/app/api/v1/__init__.py` 中注册新路由：
```python
from app.api import your_new_router
api_router.include_router(your_new_router.router, prefix="/your-route")
```

### 前端 API 调用
```typescript
import request from '@/api/request'

export default {
  async list() {
    return request.get('/items/')
  }
}
```

### Pinia Store
```typescript
export const useMyStore = defineStore('my', () => {
  const items = ref([])
  async function fetch() {
    items.value = await myApi.list()
  }
  return { items, fetch }
})
```

---

## 📂 核心目录

```
backend/app/
├── main.py              # 入口，FastAPI app
├── core/config.py       # 配置（Pydantic Settings）
├── database.py          # DB session, init_db()
├── models/              # SQLAlchemy 模型
├── api/v1/              # API 路由（聚合到 api_router）
├── services/            # 业务逻辑层
└── tasks/encode.py      # RQ worker 函数

frontend/src/
├── main.ts              # 入口
├── router/index.ts      # Vue Router + 认证守卫
├── stores/              # Pinia stores
├── api/                 # Axios 客户端
└── views/               # 页面组件
```

---

遇到具体问题时，查阅 `cc/` 目录下对应的详细文档。
