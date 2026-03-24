"""用户组管理 API 路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import timezone
from uuid import UUID

from app.database import get_db
from app.core.deps import get_current_admin
from app.models.user import User
from app.models.group import UserGroup
from app.schemas.group import (
    UserGroupCreate, UserGroupUpdate, UserGroupResponse,
    PermissionResponse
)
from app.services.group_service import UserGroupService

router = APIRouter(prefix="/admin/groups", tags=["用户组管理"])


def format_datetime_utc(dt) -> str:
    """将 datetime 转换为 UTC ISO 格式字符串"""
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'


def group_to_response(group: UserGroup, user_count: int = 0) -> dict:
    """将用户组模型转换为响应格式"""
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "max_file_size": group.max_file_size,
        "max_storage": group.max_storage,
        "result_retention_days": group.result_retention_days,
        "local_paths": group.local_paths,
        "allowed_preset_ids": group.allowed_preset_ids,
        "default_preset_id": group.default_preset_id,
        "api_access_enabled": group.api_access_enabled,
        "email_enabled": group.email_enabled,
        "created_at": format_datetime_utc(group.created_at),
        "updated_at": format_datetime_utc(group.updated_at),
        "user_count": user_count
    }


@router.get("/", response_model=List[UserGroupResponse])
async def list_groups(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取所有用户组"""
    groups = await UserGroupService.list_groups(db)
    result = []
    for group in groups:
        count = await UserGroupService.get_user_count(db, group.id)
        result.append(group_to_response(group, count))
    return result


@router.post("/", response_model=UserGroupResponse)
async def create_group(
    data: UserGroupCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建用户组"""
    try:
        group = await UserGroupService.create(db, data.model_dump())
        await db.commit()
        await db.refresh(group)
        return group_to_response(group, 0)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/permissions/list", response_model=List[PermissionResponse])
async def list_permissions(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取所有权限"""
    permissions = await UserGroupService.list_permissions(db)
    return [
        {
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "description": p.description
        }
        for p in permissions
    ]


@router.get("/{group_id}", response_model=UserGroupResponse)
async def get_group(
    group_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取用户组详情"""
    try:
        uuid = UUID(group_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的用户组ID")

    group = await UserGroupService.get_by_id(db, uuid)
    if not group:
        raise HTTPException(status_code=404, detail="用户组不存在")

    count = await UserGroupService.get_user_count(db, uuid)
    return group_to_response(group, count)


@router.put("/{group_id}", response_model=UserGroupResponse)
async def update_group(
    group_id: str,
    data: UserGroupUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新用户组"""
    try:
        uuid = UUID(group_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的用户组ID")

    group = await UserGroupService.get_by_id(db, uuid)
    if not group:
        raise HTTPException(status_code=404, detail="用户组不存在")

    try:
        # 过滤 None 值
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        await UserGroupService.update(db, group, update_data)
        await db.commit()
        await db.refresh(group)
        count = await UserGroupService.get_user_count(db, uuid)
        return group_to_response(group, count)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除用户组"""
    try:
        uuid = UUID(group_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的用户组ID")

    group = await UserGroupService.get_by_id(db, uuid)
    if not group:
        raise HTTPException(status_code=404, detail="用户组不存在")

    try:
        await UserGroupService.delete(db, group)
        await db.commit()
        return {"message": "用户组已删除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
