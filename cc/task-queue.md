# 任务队列 (Celery)

## 概述

项目使用 Celery 处理后台转码任务，通过 Redis 作为消息代理和结果存储后端。Celery 是跨平台的分布式任务队列，原生支持 Windows、Linux 和 macOS。

## 架构

```
┌─────────┐      ┌─────────┐      ┌──────────┐
│  API    │ ───> │  Redis  │ ───> │  Worker  │ ───> FFmpeg
└─────────┘      └─────────┘      └──────────┘
    │                                   │
    └──────────── WebSocket 进度 ────────┘
```

## 跨平台支持

Celery 会根据操作系统自动选择合适的并发模型：

| 平台    | 默认并发模型 | 说明                         |
|---------|-------------|------------------------------|
| Linux   | `prefork`   | 使用 fork() 创建子进程       |
| macOS   | `prefork`   | 使用 fork() 创建子进程       |
| Windows | `solo` / `threads` | 不使用 fork，兼容 Windows |

代码无需修改，Celery 自动处理平台差异。

## 启动 Worker

### 开发环境

```bash
cd backend
python -m app.worker
```

### 生产环境

#### Linux / macOS

```bash
# 使用 nohup（推荐）
cd backend
nohup python -m app.worker > /tmp/worker.log 2>&1 &

# 查看日志
tail -f /tmp/worker.log
```

#### Windows

```bash
# 使用 start 命令在新窗口启动
cd backend
start /B python -m app.worker > worker.log 2>&1

# 或使用 pythonw（无控制台窗口）
pythonw -m app.worker
```

### 停止 Worker

```bash
# Linux / macOS
ps aux | grep "celery.*worker"
kill <PID>

# Windows
tasklist | findstr python
taskkill /PID <PID> /F
```

## 超时配置

转码任务可能需要很长时间，已配置：

- **任务时间限制**：1 年（31 536 000 秒）
- **软超时**：1 年减 1 小时（允许优雅终止）

配置位置：`backend/app/celery_app.py`

## Worker 函数

**位置**：`backend/app/tasks/encode.py`

```python
@celery_app.task(name="app.tasks.encode.encode_task", bind=True)
def encode_task(self, task_id: str, user_id: str) -> str:
    """执行转码任务 - Celery worker 入口"""
    # ...
```

### 任务装饰器

- `bind=True`：将任务实例绑定到第一个参数 `self`
- 可通过 `self.request.id` 获取任务 ID
- 可通过 `self.update_state()` 更新任务状态

## 监控

### Flower (推荐)

Flower 是 Celery 的实时监控 Web 工具：

```bash
pip install flower
celery -A app.celery_app flower
```

访问 <http://localhost:5555> 查看任务状态、Worker 健康状态等。

### 命令行

```bash
# 查看活跃任务
celery -A app.celery_app inspect active

# 查看注册的任务
celery -A app.celery_app inspect registered

# 查看 worker 状态
celery -A app.celery_app inspect stats

# 清除所有任务
celery -A app.celery_app purge
```

## 配置

**`.env` 配置**：

```bash
# Redis 连接（Celery 同时作为 broker 和 backend）
REDIS_URL=redis://localhost:6379/0
```

## 最佳实践

1. **幂等性**：Worker 函数应该是幂等的，可以安全重试
2. **超时**：为长时间运行的任务设置合理的超时（已配置 1 年）
3. **错误记录**：记录详细错误信息到数据库
4. **进度更新**：定期更新任务进度，即使很小的增量
5. **资源清理**：使用 `finally` 确保资源释放
6. **后台运行**：生产环境使用进程管理器（systemd/supervisor）

## 从 RQ 迁移的变化

| 变更点   | RQ                       | Celery                          |
|----------|--------------------------|---------------------------------|
| 导入     | `from rq import Queue`    | `from app.celery_app import celery_app` |
| 任务装饰器 | 无（普通函数）            | `@celery_app.task()`            |
| 发送任务 | `queue.enqueue(fn, args)` | `task.delay(args)`              |
| Worker 启动 | `python -m app.worker`  | `python -m app.worker`（相同）   |
| 跨平台   | 仅 Unix/Linux            | Windows/Linux/macOS             |
