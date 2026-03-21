"""RQ 转码任务"""
from rq import get_current_job
from app.database import AsyncSessionLocal
from app.models.task import Task, TaskStatus
from app.services.storage import get_storage
import asyncio

def encode_task(task_id: str, user_id: str) -> str:
    """执行转码任务"""
    return asyncio.run(_encode_task_async(task_id, user_id))


async def _encode_task_async(task_id: str, user_id: str) -> str:
    """异步执行转码任务"""
    job = get_current_job()

    # 获取数据库会话
    db_gen = get_db_sync()
    db = next(db_gen)

    try:
        from app.services.task_service import TaskService
        from uuid import UUID

        task = await TaskService.get_by_id(db, UUID(task_id), UUID(user_id))
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        # 更新状态为处理中
        task = await TaskService.update_status(db, task, TaskStatus.PROCESSING)
        await db.commit()

        # 获取存储和输出路径
        storage = get_storage()
        output_path = f"results/{user_id}/{task_id}/output.mp4"

        # 模拟转码（实际应调用 FFmpeg）
        import time
        for i in range(0, 101, 10):
            task = await TaskService.update_progress(db, task, i)
            await db.commit()
            time.sleep(0.1)

        # 完成任务
        task = await TaskService.update_status(db, task, TaskStatus.COMPLETED)
        await db.commit()

        return f"Task {task_id} completed"

    except Exception as e:
        # 更新失败状态
        try:
            task = await TaskService.get_by_id(db, UUID(task_id), UUID(user_id))
            if task:
                await TaskService.update_status(db, task, TaskStatus.FAILED, str(e))
                await db.commit()
        except:
            pass
        raise
    finally:
        db.close()


def get_db_sync():
    """同步上下文的数据库会话（用于 RQ Worker）"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings

    sync_engine = create_engine(
        settings.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", ""),
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
