"""用户业务逻辑服务"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID

from app.models.user import User
from app.core.security import get_password_hash, verify_password


class UserService:
    """用户服务"""

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
        """根据 ID 获取用户"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        username: str,
        email: str,
        password: str
    ) -> User:
        """创建新用户（首个注册的用户自动成为管理员）"""
        existing = await UserService.get_by_username(db, username)
        if existing:
            raise ValueError("Username already exists")

        existing = await UserService.get_by_email(db, email)
        if existing:
            raise ValueError("Email already exists")

        # 检查是否为第一个用户
        from sqlalchemy import func
        result = await db.execute(select(func.count(User.id)))
        user_count = result.scalar()

        # 第一个注册的用户自动成为管理员
        is_first_user = user_count == 0
        is_admin = True if is_first_user else False

        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            is_active=True,
            is_admin=is_admin,
        )
        db.add(user)
        await db.flush()

        if is_first_user:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"首个用户 '{username}' 注册，自动设置为管理员")

        return user

    @staticmethod
    async def verify_password(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """验证用户密码"""
        user = await UserService.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    async def update_password(
        db: AsyncSession,
        user: User,
        old_password: str,
        new_password: str
    ) -> User:
        """更新用户密码"""
        if not verify_password(old_password, user.password_hash):
            raise ValueError("Invalid old password")

        user.password_hash = get_password_hash(new_password)
        await db.flush()
        return user
