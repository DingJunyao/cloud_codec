"""用户数据模型"""
from sqlalchemy import String, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING, List
from enum import Enum
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.group import UserGroup
    from app.models.task import Task


class UserRole(str, Enum):
    """用户角色"""
    USER = "user"
    ADMIN = "admin"


class User(Base, UUIDMixin, TimestampMixin):
    """用户模型"""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    group_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("user_groups.id", ondelete="SET NULL"),
        nullable=True
    )

    # 关系
    group: Mapped[Optional["UserGroup"]] = relationship(
        "UserGroup",
        back_populates="users",
        lazy="selectin"
    )
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
