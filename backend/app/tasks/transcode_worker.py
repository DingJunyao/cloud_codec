"""转码工作器（存根）"""
from typing import Optional, Any


class TranscodeWorker:
    """转码任务工作器"""

    def __init__(self, task_id: str):
        self.task_id = task_id

    async def start(self, task: Any, preset: Any) -> None:
        """启动转码任务"""
        # TODO: 实现转码逻辑
        raise NotImplementedError("转码功能尚未实现")

    async def cancel(self) -> None:
        """取消转码任务"""
        # TODO: 实现取消逻辑
        raise NotImplementedError("取消功能尚未实现")
