"""转码工作器"""
import asyncio
import logging
import os
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID

from app.services.ffmpeg.executor import FFmpegExecutor, ProgressInfo
from app.tasks.websocket import broadcast_task_progress, broadcast_task_progress_sync, add_log_to_history
from app.database import AsyncSessionLocal
from app.models.task import Task, TaskStatus
from app.core.config import settings
from sqlalchemy import select

logger = logging.getLogger(__name__)


class TranscodeWorker:
    """转码任务工作器"""

    # 活跃的执行器，用于取消
    _executors: dict[str, FFmpegExecutor] = {}

    def __init__(self, task_id: str):
        self.task_id = task_id
        self._executor: Optional[FFmpegExecutor] = None

    def _get_full_path(self, relative_path: str) -> str:
        """将相对路径转换为完整路径"""
        return os.path.join(settings.STORAGE_PATH, relative_path)

    async def start(self, task: Task) -> bool:
        """
        启动转码任务

        Args:
            task: 任务模型

        Returns:
            是否成功
        """
        # 获取完整输入路径
        input_path = self._get_full_path(task.source_file)

        # 发送开始日志
        start_log = {
            "type": "log",
            "data": {"line": f"[任务开始] 输入文件: {input_path}"}
        }
        add_log_to_history(self.task_id, start_log)
        await broadcast_task_progress(self.task_id, start_log)

        # 发送 FFmpeg 命令日志
        from app.services.ffmpeg.command import build_ffmpeg_command
        cmd = build_ffmpeg_command(input_path, self._get_output_path(task), task.config, progress_pipe=True)
        cmd_log = {
            "type": "log",
            "data": {"line": f"[FFmpeg命令] {' '.join(cmd)}"}
        }
        add_log_to_history(self.task_id, cmd_log)
        await broadcast_task_progress(self.task_id, cmd_log)

        # 创建执行器
        self._executor = FFmpegExecutor(
            task_id=self.task_id,
            input_file=input_path,
            output_file=self._get_output_path(task),
            config=task.config,
        )

        # 注册执行器
        self._executors[self.task_id] = self._executor

        try:
            # 执行转码 - 使用同步回调，传递事件循环
            success = await self._executor.execute(
                on_progress=lambda p, loop: self._on_progress_sync(p, loop),
                on_log=lambda l, loop: self._on_log_sync(l, loop),
            )

            # 获取事件循环用于广播
            loop = asyncio.get_running_loop()

            # 更新任务状态
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Task).where(Task.id == UUID(self.task_id))
                )
                task = result.scalar_one_or_none()
                if task:
                    if success:
                        task.status = TaskStatus.COMPLETED
                        task.progress = 100
                        task.output_file = self._get_output_relative_path(task)
                        # 获取输出文件大小
                        output_path = self._get_output_path(task)
                        if os.path.exists(output_path):
                            task.output_size = os.path.getsize(output_path)
                        task.completed_at = datetime.now(timezone.utc)
                        # 发送完成状态
                        broadcast_task_progress_sync(self.task_id, {
                            "type": "status",
                            "data": {
                                "status": "completed",
                                "progress": 100,
                                "output_file": task.output_file,
                                "output_size": task.output_size
                            }
                        }, loop)
                        # 发送完成日志
                        self._on_log_sync(f"[任务完成] 输出文件: {task.output_file}", loop)
                    elif self._executor._cancelled:
                        task.status = TaskStatus.CANCELLED
                        task.error_message = "用户取消"
                        # 发送取消状态
                        broadcast_task_progress_sync(self.task_id, {
                            "type": "status",
                            "data": {"status": "cancelled"}
                        }, loop)
                        self._on_log_sync("[任务已取消]", loop)
                    else:
                        task.status = TaskStatus.FAILED
                        # 记录 FFmpeg 返回码作为错误信息
                        return_code = self._executor._return_code
                        task.error_message = f"FFmpeg 返回码: {return_code}" if return_code is not None else "FFmpeg 执行失败"
                        # 发送失败状态
                        broadcast_task_progress_sync(self.task_id, {
                            "type": "status",
                            "data": {"status": "failed", "error": task.error_message}
                        }, loop)
                        self._on_log_sync(f"[任务失败] {task.error_message}", loop)
                    await db.commit()

            return success

        except Exception as e:
            logger.error(f"[{self.task_id}] 转码异常: {e}")
            try:
                loop = asyncio.get_running_loop()
                self._on_log_sync(f"[转码异常] {e}", loop)
            except RuntimeError:
                pass
            return False
        finally:
            # 清理执行器
            self._executors.pop(self.task_id, None)

    async def cancel(self) -> bool:
        """取消转码任务"""
        if self._executor:
            await self._executor.cancel()
            return True

        # 尝试从全局执行器中获取
        executor = self._executors.get(self.task_id)
        if executor:
            await executor.cancel()
            return True

        return False

    def _on_progress_sync(self, progress: ProgressInfo, loop: asyncio.AbstractEventLoop = None):
        """进度回调（同步版本，在子线程中调用）"""
        try:
            # WebSocket 推送进度，传递事件循环
            broadcast_task_progress_sync(self.task_id, {
                "type": "progress",
                "data": {
                    "percent": round(progress.progress, 1),
                    "fps": round(progress.fps, 1),
                    "speed": progress.speed,
                    "eta": progress.eta,
                    "frame": progress.frame,
                }
            }, loop)
        except Exception as e:
            logger.warning(f"[{self.task_id}] 更新进度失败: {e}")

    def _on_log_sync(self, line: str, loop: asyncio.AbstractEventLoop = None):
        """日志回调（同步版本，在子线程中调用）"""
        try:
            # WebSocket 推送日志，传递事件循环
            broadcast_task_progress_sync(self.task_id, {
                "type": "log",
                "data": {
                    "line": line
                }
            }, loop)
        except Exception as e:
            logger.warning(f"[{self.task_id}] 推送日志失败: {e}")

    def _get_output_path(self, task: Task) -> str:
        """获取输出文件完整路径"""
        # 输出目录
        output_dir = os.path.join(
            settings.STORAGE_PATH,
            "results",
            str(task.user_id),
            str(task.id)
        )
        os.makedirs(output_dir, exist_ok=True)

        # 输出文件名
        container = task.config.get("container", "mp4")
        output_name = f"output.{container}"

        return os.path.join(output_dir, output_name)

    def _get_output_relative_path(self, task: Task) -> str:
        """获取输出文件的相对路径（用于存储到数据库）"""
        container = task.config.get("container", "mp4")
        return f"results/{task.user_id}/{task.id}/output.{container}"

    @classmethod
    async def cancel_task(cls, task_id: str) -> bool:
        """取消指定任务"""
        executor = cls._executors.get(task_id)
        if executor:
            await executor.cancel()
            return True
        return False
