"""任务日志模型"""
from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.base import Base, TimestampMixin, UUIDMixin


class TaskLog(Base, UUIDMixin, TimestampMixin):
    """任务日志模型 - 持久化存储转码日志"""

    __tablename__ = "task_logs"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    log_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="info",
        comment="日志类型: info, progress, error"
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="日志内容"
    )

    # 关联关系
    task: Mapped["Task"] = relationship("Task", back_populates="logs")

    # 复合索引：按任务ID和创建时间查询
    __table_args__ = (
        Index('ix_task_logs_task_id_created_at', 'task_id', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<TaskLog(task_id={self.task_id}, type={self.log_type})>"
