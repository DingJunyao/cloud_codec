"""任务服务"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task, TaskStatus
from app.models.preset import Preset
from app.schemas.task import TaskCreate, TaskResponse


class TaskService:
    """任务管理服务"""

    async def create_task(self, db: AsyncSession, data: TaskCreate, user_id: str) -> Task:
        """创建转码任务"""
        # 验证预设存在
        result = await db.execute(select(Preset).where(Preset.id == UUID(str(data.preset_id))))
        preset = result.scalar_one_or_none()
        if not preset:
            raise ValueError("预设不存在")

        # 创建任务记录
        task = Task(
            user_id=UUID(user_id),
            preset_id=UUID(str(data.preset_id)),
            status=TaskStatus.PENDING,
            progress=0,
            source_file=data.video_path,
            config=preset.config,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        # TODO: 启动转码任务
        # from app.tasks.transcode_worker import TranscodeWorker
        # worker = TranscodeWorker(str(task.id))
        # await worker.start(task, preset)

        return task

    async def list_tasks(self, db: AsyncSession, user_id: str, status: Optional[str] = None) -> List[Task]:
        """获取任务列表"""
        query = select(Task).where(Task.user_id == UUID(user_id))
        if status:
            query = query.where(Task.status == TaskStatus(status))
        result = await db.execute(query)
        return result.scalars().all()

    async def get_task(self, db: AsyncSession, task_id: str, user_id: str) -> Task:
        """获取任务详情"""
        result = await db.execute(
            select(Task).where(Task.id == UUID(task_id), Task.user_id == UUID(user_id))
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError("任务不存在")
        return task

    async def cancel_task(self, db: AsyncSession, task_id: str, user_id: str) -> Task:
        """取消任务"""
        task = await self.get_task(db, task_id, user_id)
        if task.status not in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            raise ValueError("只能取消待处理或处理中的任务")

        # TODO: 取消转码任务
        # from app.tasks.transcode_worker import TranscodeWorker
        # worker = TranscodeWorker(task_id)
        # await worker.cancel()

        task.status = TaskStatus.CANCELLED
        await db.commit()
        await db.refresh(task)
        return task
