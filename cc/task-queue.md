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

## 启动 Worker

### 重要说明

⚠️ **Worker 必须在后台运行！**

```bash
cd backend
nohup python -m app.worker > /tmp/worker.log 2>&1 &

# 查看日志
tail -f /tmp/worker.log
```

**不要**直接在前台终端运行 `python -m app.worker`，因为：
- 在终端按 `Ctrl+Z` 会暂停 Worker 及其子进程
- 终端关闭会导致 Worker 进程终止
- 子进程（ffmpeg）可能会收到终端信号而暂停

### 启动命令

```bash
# 方式1: 使用 nohup（推荐）
cd backend
nohup python -m app.worker > /tmp/worker.log 2>&1 &

# 方式2: 使用 screen
screen -dmS worker python -m app.worker
screen -r worker  # 重新连接

# 方式3: 使用 systemd（生产环境推荐）
# 创建 /etc/systemd/system/cloudcodec-worker.service
```

### 停止 Worker

```bash
# 查找 worker 进程
ps aux | grep "python.*worker"

# 终止进程
kill <PID>

# 如果进程被暂停（状态 T），强制终止
kill -9 <PID>
```

## 超时配置

转码任务可能需要很长时间，已配置：

- **队列默认超时**: 1 年（31536000 秒）
- **任务超时**: 1 年（31536000 秒）

配置位置：
- `backend/app/worker.py`: `Queue(..., default_timeout=31536000)`
- `backend/app/services/task_service.py`: `queue.enqueue(..., job_timeout=31536000)`

## 处理卡住的任务

如果 Worker 进程异常终止，任务可能会卡在 `PROCESSING` 状态。

### 使用重队脚本

```bash
cd backend
python requeue_pending.py
```

这个脚本会：
1. 将所有 `PROCESSING` 状态的任务重置为 `PENDING`
2. 将 `PENDING` 任务重新加入队列

### 手动处理

```bash
# 1. 检查进程状态
ps aux | grep -E "(python.*worker|ffmpeg)"

# 如果看到进程状态是 T（暂停），需要终止
kill -9 <PID>

# 2. 检查队列
redis-cli LLEN rq:queue:default  # 查看队列长度
redis-cli DEL rq:queue:default   # 清空队列

# 3. 运行重队脚本
python requeue_pending.py

# 4. 重启 Worker
nohup python -m app.worker > /tmp/worker.log 2>&1 &
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
```

## 监控

### rq-dashboard

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
```

## 最佳实践

1. **幂等性**: Worker 函数应该是幂等的，可以安全重试
2. **超时**: 为长时间运行的任务设置合理的超时（已配置1年）
3. **错误记录**: 记录详细错误信息到数据库
4. **进度更新**: 定期更新任务进度，即使很小的增量
5. **资源清理**: 使用 `finally` 确保资源释放
6. **后台运行**: 始终使用 `nohup` 或 `screen` 启动 Worker
