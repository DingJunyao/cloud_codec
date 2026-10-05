# 数据库注意事项

## Async Session 使用

### 正确的模式

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

# 依赖注入（推荐）
@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

### 手动会话管理

```python
from app.database import AsyncSessionLocal

async def process_task(task_id: str):
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            # ... 操作
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**注意**: `get_db()` 依赖会自动处理提交和关闭，不要手动调用 `session.commit()`。

## 模型定义

### 基础模型

所有模型继承自：
- `Base` - SQLAlchemy 声明基类
- `TimestampMixin` - 自动添加 `created_at`, `updated_at`
- `UUIDMixin` - 自动添加 `id` (UUID)

```python
from app.models.base import Base, TimestampMixin, UUIDMixin

class Task(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tasks"

    name: Mapped[str] = mapped_column(String(100))
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
```

### 关系定义

```python
from sqlalchemy.orm import relationship

class User(Base, UUIDMixin, TimestampMixin):
    # 一对多
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="user",
        lazy="selectin"  # 预加载策略
    )

    # 多对一
    group_id: Mapped[str | None] = mapped_column(ForeignKey("user_groups.id"))
    group: Mapped[Optional["UserGroup"]] = relationship("UserGroup", back_populates="users")
```

**常用加载策略**:
- `lazy="selectin"` - 预加载，适合小数据集
- `lazy="joined"` - JOIN 查询
- `lazy="select"` (默认) - 懒加载，访问时查询

### 查询模式

```python
from sqlalchemy import select

# 单条记录
result = await db.execute(
    select(User).where(User.username == "admin")
)
user = result.scalar_one_or_none()

# 列表
result = await db.execute(
    select(Task).where(Task.status == TaskStatus.COMPLETED)
)
tasks = result.scalars().all()

# 关联加载
result = await db.execute(
    select(Task)
    .options(selectinload(Task.user))  # 预加载关系
    .where(Task.id == task_id)
)
task = result.scalar_one()
```

## 数据库初始化

### 首次运行

```bash
cd backend

# 方法 1: Python 脚本
python -c "import asyncio; from app.database import init_db; asyncio.run(init_db())"

# 方法 2: Alembic
alembic upgrade head
```

### 添加新模型

1. 在 `app/models/` 中创建模型文件
2. 在 `app/models/__init__.py` 中导入
3. 生成迁移：`alembic revision --autogenerate -m "add new model"`
4. 应用迁移：`alembic upgrade head`

## 迁移工作流

```bash
# 创建迁移
alembic revision --autogenerate -m "add progress to tasks"

# 查看待应用的迁移
alembic current

# 应用迁移
alembic upgrade head

# 回滚一步
alembic downgrade -1

# 查看迁移历史
alembic history
```

## 同步会话（RQ Worker）

RQ worker 运行在同步上下文，需要同步数据库会话：

```python
# app/tasks/encode.py
def get_db_sync():
    """同步上下文的数据库会话（用于 RQ Worker）"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings

    sync_engine = create_engine(
        settings.DATABASE_URL.replace("+aiosqlite", ""),
        echo=settings.APP_ENV == "development",
    )

    SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)

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

在 RQ worker 中使用：
```python
db_gen = get_db_sync()
db = next(db_gen)
try:
    # ... 同步数据库操作
    task = db.query(Task).get(task_id)
finally:
    db.close()
```
