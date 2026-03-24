# 开发命令

## 后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器（热重载）
uvicorn app.main:app --reload

# 指定端口
uvicorn app.main:app --reload --port 8001
```

## Worker（任务队列）

⚠️ **必须在后台运行**

```bash
cd backend

# 启动 Worker（推荐方式）
nohup python -m app.worker > /tmp/worker.log 2>&1 &

# 查看日志
tail -f /tmp/worker.log

# 查看 Worker 进程
ps aux | grep "python.*worker"

# 停止 Worker
kill <PID>

# 强制停止（如果进程被暂停）
kill -9 <PID>
```

### 重队卡住的任务

```bash
cd backend

# 使用重队脚本
python requeue_pending.py

# 或者手动处理
sqlite3 data/cloudcodec.db "UPDATE tasks SET status='PENDING', progress=0 WHERE status='PROCESSING';"
```

## 数据库迁移

```bash
cd backend

# 生成迁移文件
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 前端

```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 构建
npm run build

# 预览构建结果
npm run preview
```

## Redis 队列管理

```bash
# 查看队列长度
redis-cli LLEN rq:queue:default

# 清空队列
redis-cli DEL rq:queue:default

# 查看所有 RQ 相关的 key
redis-cli KEYS "rq:*"
```
