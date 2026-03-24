"""用户组业务逻辑服务"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from uuid import UUID

from app.models.group import UserGroup
from app.models.permission import Permission
from app.models.user import User


class UserGroupService:
    """用户组业务逻辑服务"""

    @staticmethod
    async def list_groups(db: AsyncSession) -> List[UserGroup]:
        """获取所有用户组"""
        result = await db.execute(select(UserGroup).order_by(UserGroup.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, group_id: UUID) -> Optional[UserGroup]:
        """根据 ID 获取用户组"""
        result = await db.execute(select(UserGroup).where(UserGroup.id == group_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[UserGroup]:
        """根据名称获取用户组"""
        result = await db.execute(select(UserGroup).where(UserGroup.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: dict) -> UserGroup:
        """创建用户组"""
        # 检查名称唯一性
        existing = await UserGroupService.get_by_name(db, data['name'])
        if existing:
            raise ValueError("用户组名称已存在")

        group = UserGroup(**data)
        db.add(group)
        await db.flush()
        return group

    @staticmethod
    async def update(db: AsyncSession, group: UserGroup, data: dict) -> UserGroup:
        """更新用户组"""
        # 如果修改名称，检查唯一性
        if 'name' in data and data['name'] and data['name'] != group.name:
            existing = await UserGroupService.get_by_name(db, data['name'])
            if existing and existing.id != group.id:
                raise ValueError("用户组名称已存在")
            group.name = data['name']

        # 更新其他字段
        for key, value in data.items():
            if key != 'name' and value is not None:
                setattr(group, key, value)

        await db.flush()
        return group

    @staticmethod
    async def delete(db: AsyncSession, group: UserGroup):
        """删除用户组"""
        # 检查是否有用户
        if group.users:
            raise ValueError("无法删除仍有用户的用户组")

        await db.delete(group)
        await db.flush()

    @staticmethod
    async def get_user_count(db: AsyncSession, group_id: UUID) -> int:
        """获取用户组内的用户数量"""
        result = await db.execute(
            select(func.count(User.id)).where(User.group_id == str(group_id))
        )
        return result.scalar() or 0

    @staticmethod
    async def assign_user(db: AsyncSession, user: User, group: UserGroup):
        """为用户分配用户组"""
        user.group_id = str(group.id)
        await db.flush()

    @staticmethod
    async def remove_user_group(db: AsyncSession, user: User):
        """移除用户的用户组"""
        user.group_id = None
        await db.flush()

    @staticmethod
    async def list_permissions(db: AsyncSession) -> List[Permission]:
        """获取所有权限"""
        result = await db.execute(select(Permission).order_by(Permission.code))
        return result.scalars().all()
