"""RQ 转码任务入口"""
import asyncio
import logging
from datetime import datetime, timezone
from rq import get_current_job

logger = logging.getLogger(__name__)


def encode_task(task_id: str, user_id: str) -> str:
    """
    RQ 任务入口：执行转码任务

    Args:
        task_id: 任务ID
        user_id: 用户ID

    Returns:
        结果消息
    """
    # 在 RQ worker 中可能已有事件循环
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果循环正在运行，创建新的
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _encode_task_async(task_id, user_id)
                )
                return future.result()
        else:
            return loop.run_until_complete(_encode_task_async(task_id, user_id))
    except RuntimeError:
        # 没有事件循环，创建新的
        return asyncio.run(_encode_task_async(task_id, user_id))


async def _encode_task_async(task_id: str, user_id: str) -> str:
    """异步执行转码任务"""
    job = get_current_job()

    # 获取数据库会话
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    from app.models.task import Task, TaskStatus
    from app.tasks.transcode_worker import TranscodeWorker
    from uuid import UUID
    from datetime import datetime

    # 创建同步引擎
    sync_url = settings.DATABASE_URL
    for prefix in ["+aiosqlite", "+asyncpg", "+aiomysql"]:
        sync_url = sync_url.replace(prefix, "")

    engine = create_engine(sync_url, echo=False)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    session = Session()
    try:
        # 获取任务
        result = session.execute(
            select(Task).where(Task.id == UUID(task_id))
        )
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        # 检查任务状态
        if task.status != TaskStatus.PENDING:
            raise ValueError(f"任务状态不正确: {task.status}")

        # 更新状态为处理中
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.now(timezone.utc)
        session.commit()

        # 创建工作器并执行
        worker = TranscodeWorker(task_id)
        success = await worker.start(task)

        # 刷新任务状态
        session.refresh(task)

        if success:
            logger.info(f"任务 {task_id} 完成")
            return f"Task {task_id} completed"
        elif task.status == TaskStatus.CANCELLED:
            return f"Task {task_id} cancelled"
        else:
            return f"Task {task_id} failed"

    except Exception as e:
        logger.error(f"任务 {task_id} 执行失败: {e}")

        # 更新失败状态
        try:
            result = session.execute(
                select(Task).where(Task.id == UUID(task_id))
            )
            task = result.scalar_one_or_none()
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.now(timezone.utc)
                session.commit()
        except Exception:
            pass

        raise
    finally:
        session.close()
