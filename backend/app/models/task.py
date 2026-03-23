"""任务数据模型"""
from sqlalchemy import String, Integer, BigInteger, Text, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from enum import Enum
from datetime import datetime
from app.models.base import Base, TimestampMixin, UUIDMixin


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(Base, UUIDMixin, TimestampMixin):
    """转码任务模型"""

    __tablename__ = "tasks"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="任务名称（源文件名）"
    )

    preset_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("presets.id", ondelete="SET NULL"),
        nullable=True
    )

    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="进度百分比 0-100"
    )

    source_file: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="源文件路径"
    )
    source_size: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="源文件大小（字节）"
    )

    output_file: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="输出文件路径"
    )
    output_size: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="输出文件大小（字节）"
    )

    config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="转码配置参数"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="失败时的错误信息"
    )

    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    progress_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment='{"fps": 120, "speed": "2.5x", "eta": 60}'
    )

    user: Mapped["User"] = relationship("User", back_populates="tasks")
    preset: Mapped[Optional["Preset"]] = relationship("Preset", back_populates="tasks")
    logs: Mapped[list["TaskLog"]] = relationship(
        "TaskLog",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskLog.created_at"
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, status={self.status}, progress={self.progress}%)>"
