# 开发命令

## 后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器（热重载）
uvicorn app.main:app --reload

# 指定端口运行
uvicorn app.main:app --reload --port 8000

# 初始化数据库
python -c "import asyncio; from app.database import init_db; asyncio.run(init_db())"

# 运行 RQ worker（后台任务）
rq worker app.tasks.encode --url redis://localhost:6379/0
```

## 前端

```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 类型检查
vue-tsc --noEmit
```

## 数据库迁移

```bash
cd backend

# 创建新迁移
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```
