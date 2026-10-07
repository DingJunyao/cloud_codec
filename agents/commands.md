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

## 依赖管理

后端有两份依赖描述，必须保持等价（相同的包、相同的版本约束），以哪种方式安装结果都一致：

- `backend/pyproject.toml` 的 `[project].dependencies` — 供 `uv` / `pip install -e .` 使用
- `backend/requirements.txt` — 供 `pip install -r` 使用

新增依赖时两处都要加，版本约束保持一致。修改 pyproject.toml 后需重新生成锁文件：

```bash
cd backend
uv lock
```

可选依赖组（仅 pyproject.toml）：`dev`（pytest/ruff/mypy）、`mysql`（pymysql）、`postgresql`（psycopg2-binary）。

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

任务队列为 Celery（broker 为 Redis，默认队列名 `celery`）：

```bash
# 查看队列长度
redis-cli LLEN celery

# 查看 Celery worker 状态与正在执行的任务
celery -A app.celery_app inspect active

# 清空队列（谨慎操作，会丢弃未执行的任务消息）
redis-cli DEL celery
```
