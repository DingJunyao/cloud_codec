# 任务队列 (RQ)

## 概述

项目使用 RQ (Redis Queue) 处理后台转码任务。

## 架构

```
┌─────────┐      ┌─────────┐      ┌──────────┐
│  API    │ ───> │  Redis  │ ───> │  Worker  │ ───> FFmpeg
└─────────┘      └─────────┘      └──────────┘
    │                                   │
    └──────────── WebSocket 进度 ────────┘
```

## Worker 函数

**位置**: `backend/app/tasks/encode.py`

```python
def encode_task(task_id: str, user_id: str) -> str:
    """执行转码任务 - RQ worker 入口"""
    return asyncio.run(_encode_task_async(task_id, user_id))
```

### 任务元数据

在 worker 中访问 RQ job 元数据：

```python
from rq import get_current_job

job = get_current_job()
job.meta['progress'] = 50
job.save_meta()
```

### 进度更新

```python
# 更新任务进度到数据库
task = await TaskService.update_progress(db, task, progress)
await db.commit()

# 通知 WebSocket
await broadcast_task_progress(task_id, {
    "status": "processing",
    "progress": progress,
    "message": f"转码中... {progress}%"
})
```

## 运行 Worker

```bash
cd backend

# 基础 worker
rq worker app.tasks.encode --url redis://localhost:6379/0

# 带详细日志
rq worker app.tasks.encode --url redis://localhost:6379/0 --log-level=debug

# 多 worker 并行处理
rq worker app.tasks.encode --url redis://localhost:6379/0 --num-workers 4
```

## 入队任务

```python
from rq import Queue
from redis import Redis

queue = Queue("encode", connection=Redis.from_url("redis://localhost:6379/0"))

# 入队
job = queue.enqueue(
    'app.tasks.encode.encode_task',
    task_id=str(task.id),
    user_id=str(user.id),
    timeout='1h'  # 1小时超时
)

# 获取 job ID
job_id = job.id
```

## 同步数据库会话

RQ worker 运行在同步上下文，需要同步数据库会话：

```python
def get_db_sync():
    """创建同步数据库会话"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings

    # 移除 async 驱动前缀
    sync_url = settings.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "")

    engine = create_engine(sync_url, echo=settings.APP_ENV == "development")
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    from contextlib import contextmanager

    @contextmanager
    def get_session():
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return get_session()
```

使用：
```python
db_gen = get_db_sync()
db = next(db_gen)
try:
    task = db.query(Task).get(task_id)
    # ... 处理
finally:
    db.close()
```

## 错误处理

Worker 中的异常会自动标记任务为失败：

```python
try:
    result = await process_transcode(task)
except Exception as e:
    # 更新任务状态为失败
    task.status = TaskStatus.FAILED
    task.error_message = str(e)
    await db.commit()
    raise  # RQ 会记录异常
```

查看失败任务：
```bash
rq info --url redis://localhost:6379/0
rq failed --url redis://localhost:6379/0
```

## 监控

### RQ Dashboard

```bash
pip install rq-dashboard
rq-dashboard --url redis://localhost:6379/0
```

访问 http://localhost:9181 查看 RQ 任务状态。

### 命令行

```bash
# 查看队列状态
rq info --url redis://localhost:6379/0

# 查看失败任务
rq failed --url redis://localhost:6379/0

# 重试失败任务
rq requeue --url redis://localhost:6379/0 <job_id>

# 清空队列
rq empty --url redis://localhost:6379/0 default
```

## 配置

**`.env` 配置**:
```bash
# Redis 连接
REDIS_URL=redis://localhost:6379/0

# 任务超时（秒）
RQ_DEFAULT_TIMEOUT=3600
```

## 最佳实践

1. **幂等性**: Worker 函数应该是幂等的，可以安全重试
2. **超时**: 为长时间运行的任务设置合理的超时
3. **错误记录**: 记录详细错误信息到数据库
4. **进度更新**: 定期更新任务进度，即使很小的增量
5. **资源清理**: 使用 `finally` 确保资源释放
