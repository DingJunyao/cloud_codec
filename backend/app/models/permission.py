"""权限数据模型"""
from sqlalchemy import String, Text, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from app.models.base import Base, TimestampMixin, UUIDMixin

# 多对多关联表
group_permissions = Table(
    "group_permissions",
    Base.metadata,
    Column("group_id", ForeignKey("user_groups.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(Base, UUIDMixin, TimestampMixin):
    """权限模型"""

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, code={self.code}, name={self.name})>"
