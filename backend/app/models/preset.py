"""预设数据模型"""
from sqlalchemy import String, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING, List
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.task import Task


class Preset(Base, UUIDMixin, TimestampMixin):
    """转码预设模型"""

    __tablename__ = "presets"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_builtin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为系统内置预设"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为默认预设"
    )

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="创建者用户ID，系统预设为NULL"
    )

    config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="转码配置参数"
    )

    # 关系
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="preset",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Preset(id={self.id}, name={self.name}, is_builtin={self.is_builtin})>"
