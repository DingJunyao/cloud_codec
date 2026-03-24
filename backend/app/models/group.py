"""用户组数据模型"""
from sqlalchemy import String, Text, Integer, BigInteger, Boolean, JSON, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.permission import Permission


class UserGroup(Base, UUIDMixin, TimestampMixin):
    """用户组模型"""

    __tablename__ = "user_groups"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 配置
    max_file_size: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="最大文件大小（字节），None 表示无限制"
    )
    max_storage: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="最大存储空间（字节），None 表示无限制"
    )
    result_retention_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="结果保留天数，None 表示永久保留"
    )
    local_paths: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="允许访问的本地路径列表"
    )
    allowed_preset_ids: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="允许使用的预设ID列表"
    )
    default_preset_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="默认预设ID"
    )
    api_access_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否允许API访问"
    )
    email_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否启用邮件通知"
    )

    # 关系
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="group",
        lazy="selectin"
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary="group_permissions",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<UserGroup(id={self.id}, name={self.name})>"
