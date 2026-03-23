"""任务服务"""
import os
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task, TaskStatus
from app.models.preset import Preset
from app.schemas.task import TaskCreate


class TaskService:
    """任务管理服务"""

    async def create_task(
        self,
        db: AsyncSession,
        data: TaskCreate,
        user_id: str
    ) -> Task:
        """创建转码任务"""
        # 必须提供 preset_id 或 config
        if not data.preset_id and not data.config:
            raise ValueError("必须提供 preset_id 或 config")

        config: dict = {}
        preset_id: Optional[UUID] = None
        preset_name: Optional[str] = None

        if data.preset_id:
            # 验证预设存在
            result = await db.execute(
                select(Preset).where(Preset.id == UUID(data.preset_id))
            )
            preset = result.scalar_one_or_none()
            if not preset:
                raise ValueError("预设不存在")
            config = preset.config
            preset_id = UUID(data.preset_id)
            preset_name = preset.name

        # 从源文件路径提取文件名作为任务名称
        source_filename = os.path.basename(data.source_file)
        task_name = os.path.splitext(source_filename)[0]

        # 使用提供的名称或文件名（处理空字符串情况）
        final_name = data.name.strip() if data.name else None
        final_name = final_name or task_name

        # 创建任务记录
        task = Task(
            user_id=UUID(user_id),
            name=final_name,
            preset_id=preset_id,
            status=TaskStatus.PENDING,
            progress=0,
            source_file=data.source_file,
            config=config,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        # 启动转码任务
        try:
            self._enqueue_task(str(task.id), user_id)
        except ConnectionError:
            # Redis 不可用，删除已创建的任务
            await db.delete(task)
            await db.commit()
            raise

        return task

    def _enqueue_task(self, task_id: str, user_id: str):
        """将任务加入队列"""
        from rq import Queue
        from redis import Redis
        from redis.exceptions import RedisError
        from app.core.config import settings
        from app.tasks.encode import encode_task

        try:
            redis_conn = Redis.from_url(settings.REDIS_URL)
            # 测试连接
            redis_conn.ping()
            queue = Queue(connection=redis_conn)
            queue.enqueue(encode_task, task_id, user_id, job_timeout=31536000)  # 1年超时
        except RedisError as e:
            raise ConnectionError(f"任务队列服务不可用，请确保 Redis 已启动: {e}")

    async def list_tasks(
        self,
        db: AsyncSession,
        user_id: str,
        status: Optional[str] = None
    ) -> List[Task]:
        """获取任务列表"""
        query = select(Task).where(Task.user_id == UUID(user_id))
        if status:
            query = query.where(Task.status == TaskStatus(status))
        result = await db.execute(query)
        return result.scalars().all()

    async def get_task(
        self,
        db: AsyncSession,
        task_id: str,
        user_id: str
    ) -> Task:
        """获取任务详情"""
        result = await db.execute(
            select(Task).where(
                Task.id == UUID(task_id),
                Task.user_id == UUID(user_id)
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError("任务不存在")
        return task

    async def cancel_task(
        self,
        db: AsyncSession,
        task_id: str,
        user_id: str
    ) -> Task:
        """取消任务"""
        task = await self.get_task(db, task_id, user_id)
        if task.status not in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            raise ValueError("只能取消待处理或处理中的任务")

        # 取消转码进程
        from app.tasks.transcode_worker import TranscodeWorker
        await TranscodeWorker.cancel_task(task_id)

        task.status = TaskStatus.CANCELLED
        await db.commit()
        await db.refresh(task)
        return task

    async def delete_task(
        self,
        db: AsyncSession,
        task_id: str,
        user_id: str
    ):
        """删除任务(仅限已完成、失败、已取消的任务)"""
        task = await self.get_task(db, task_id, user_id)
        if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            raise ValueError("只能删除已完成、失败或已取消的任务")

        await db.delete(task)
        await db.commit()

    async def get_download_url(
        self,
        db: AsyncSession,
        task_id: str,
        user_id: str
    ) -> dict:
        """获取下载链接"""
        task = await self.get_task(db, task_id, user_id)
        if task.status != TaskStatus.COMPLETED:
            raise ValueError("任务未完成")
        if not task.output_file:
            raise ValueError("输出文件不存在")

        # 获取预设名称（如果有）
        preset_name = None
        if task.preset_id:
            result = await db.execute(
                select(Preset).where(Preset.id == task.preset_id)
            )
            preset = result.scalar_one_or_none()
            if preset:
                preset_name = preset.name

        # 构建下载文件名：任务名_预设名.扩展名 或 任务名.扩展名
        container = task.config.get("container", "mp4")
        if preset_name:
            # 清理预设名中的特殊字符
            safe_preset_name = "".join(c for c in preset_name if c.isalnum() or c in ('_', '-'))
            filename = f"{task.name}_{safe_preset_name}.{container}"
        else:
            filename = f"{task.name}.{container}"

        # 返回下载信息
        return {
            "url": f"/api/download/?path={task.output_file}&filename={filename}",
            "filename": filename,
            "size": task.output_size,
        }

    async def retry_task(
        self,
        db: AsyncSession,
        task_id: str,
        user_id: str
    ) -> Task:
        """重新转码任务（仅限失败、已完成、已取消的任务）"""
        task = await self.get_task(db, task_id, user_id)

        # 检查状态
        if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            raise ValueError("只能重新转码已完成、失败或已取消的任务")

        # 删除旧的输出文件
        if task.output_file:
            import os
            from app.core.config import settings
            output_path = os.path.join(settings.STORAGE_PATH, task.output_file)
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass  # 忽略删除失败

        # 重置任务状态
        task.status = TaskStatus.PENDING
        task.progress = 0
        task.progress_data = None
        task.output_file = None
        task.output_size = None
        task.error_message = None
        task.started_at = None
        task.completed_at = None

        await db.commit()
        await db.refresh(task)

        # 重新加入队列
        try:
            self._enqueue_task(str(task.id), user_id)
        except ConnectionError:
            # Redis 不可用，回滚状态
            task.status = TaskStatus.FAILED
            task.error_message = "任务队列服务不可用"
            await db.commit()
            raise

        return task
