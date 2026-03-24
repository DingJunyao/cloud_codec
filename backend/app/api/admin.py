"""管理员 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.preset import Preset
from app.services.hw_accel import get_hw_accel_service

router = APIRouter(prefix="/admin", tags=["admin"])


def format_datetime_utc(dt: datetime | None) -> str | None:
    """将 datetime 转换为 UTC ISO 格式字符串（带 Z 后缀）"""
    if dt is None:
        return None
    # 如果是 naive datetime，假设它是 UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # 转换为 UTC 并格式化为 ISO 字符串
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'


def user_to_response(user: User) -> dict:
    """将用户模型转换为响应格式"""
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "created_at": format_datetime_utc(user.created_at),
        "updated_at": format_datetime_utc(user.updated_at),
    }


def task_to_response(task: Task) -> dict:
    """将任务模型转换为响应格式"""
    return {
        "id": str(task.id),
        "user_id": str(task.user_id),
        "status": task.status.value if hasattr(task.status, 'value') else task.status,
        "progress": task.progress,
        "progress_data": task.progress_data,
        "source_file": task.source_file,
        "source_size": task.source_size,
        "output_file": task.output_file,
        "output_size": task.output_size,
        "preset_id": str(task.preset_id) if task.preset_id else None,
        "config": task.config,
        "error_message": task.error_message,
        "created_at": format_datetime_utc(task.created_at),
        "started_at": format_datetime_utc(task.started_at),
        "completed_at": format_datetime_utc(task.completed_at),
    }


@router.get("/stats")
async def get_system_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取系统统计信息"""
    # 用户统计
    user_count = await db.execute(select(func.count(User.id)))
    total_users = user_count.scalar() or 0

    # 任务统计
    task_count = await db.execute(select(func.count(Task.id)))
    total_tasks = task_count.scalar() or 0

    # 今日任务
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = await db.execute(
        select(func.count(Task.id)).where(Task.created_at >= today)
    )
    today_tasks = today_count.scalar() or 0

    # 各状态任务数
    status_counts = {}
    for status in TaskStatus:
        count = await db.execute(
            select(func.count(Task.id)).where(Task.status == status)
        )
        status_counts[status.value] = count.scalar() or 0

    # 预设统计
    preset_count = await db.execute(select(func.count(Preset.id)))
    total_presets = preset_count.scalar() or 0

    builtin_count = await db.execute(
        select(func.count(Preset.id)).where(Preset.is_builtin == True)
    )
    builtin_presets = builtin_count.scalar() or 0

    # 硬件加速状态
    hw_service = get_hw_accel_service()
    hw_status = hw_service.get_status()

    return {
        "users": {
            "total": total_users,
        },
        "tasks": {
            "total": total_tasks,
            "today": today_tasks,
            "by_status": status_counts,
        },
        "presets": {
            "total": total_presets,
            "builtin": builtin_presets,
            "custom": total_presets - builtin_presets,
        },
        "hardware": hw_status,
    }


@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表"""
    query = select(User)

    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )

    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    # 获取每个用户的任务数
    user_list = []
    for user in users:
        task_count = await db.execute(
            select(func.count(Task.id)).where(Task.user_id == user.id)
        )
        user_list.append({
            **user_to_response(user),
            "task_count": task_count.scalar() or 0
        })

    return user_list


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取用户详情"""
    try:
        uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的用户ID")

    result = await db.execute(select(User).where(User.id == uuid))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取用户任务统计
    task_count = await db.execute(
        select(func.count(Task.id)).where(Task.user_id == uuid)
    )
    total_tasks = task_count.scalar() or 0

    completed_count = await db.execute(
        select(func.count(Task.id)).where(
            Task.user_id == uuid,
            Task.status == TaskStatus.COMPLETED
        )
    )
    completed_tasks = completed_count.scalar() or 0

    return {
        **user_to_response(user),
        "stats": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
        }
    }


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """启用/禁用用户"""
    try:
        uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的用户ID")

    result = await db.execute(select(User).where(User.id == uuid))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不能禁用自己
    if str(user.id) == str(admin.id):
        raise HTTPException(status_code=400, detail="不能禁用自己的账户")

    user.is_active = not user.is_active
    await db.commit()
    await db.refresh(user)

    return {
        "message": f"用户已{'启用' if user.is_active else '禁用'}",
        "user": user_to_response(user)
    }


@router.get("/tasks")
async def list_all_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取所有任务列表"""
    # 计算分页
    skip = (page - 1) * page_size

    # 基础查询
    base_query = select(Task)

    if status:
        try:
            base_query = base_query.where(Task.status == TaskStatus(status))
        except ValueError:
            pass

    if user_id:
        try:
            base_query = base_query.where(Task.user_id == UUID(user_id))
        except ValueError:
            pass

    # 获取总数
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 获取分页数据
    query = base_query.order_by(Task.created_at.desc()).offset(skip).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()

    # 获取用户名映射
    user_ids = list(set(str(t.user_id) for t in tasks))
    users_result = await db.execute(
        select(User).where(User.id.in_([UUID(uid) for uid in user_ids]))
    )
    users = {str(u.id): u.username for u in users_result.scalars().all()}

    # 构建响应
    items = []
    for t in tasks:
        item = task_to_response(t)
        item["username"] = users.get(str(t.user_id), "-")
        items.append(item)

    return {"items": items, "total": total}


@router.get("/tasks/{task_id}")
async def get_task_detail(
    task_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取任务详情（管理员）"""
    try:
        uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的任务ID")

    result = await db.execute(select(Task).where(Task.id == uuid))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task_to_response(task)


@router.put("/users/{user_id}/group")
async def assign_user_group(
    user_id: str,
    group_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """为用户分配用户组"""
    try:
        user_uuid = UUID(user_id)
        group_uuid = UUID(group_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的ID")

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    from app.models.group import UserGroup
    from app.services.group_service import UserGroupService

    group = await UserGroupService.get_by_id(db, group_uuid)
    if not group:
        raise HTTPException(status_code=404, detail="用户组不存在")

    await UserGroupService.assign_user(db, user, group)
    await db.commit()

    return {
        "message": f"已将用户 {user.username} 分配到用户组 {group.name}",
        "user": user_to_response(user)
    }


@router.delete("/users/{user_id}/group")
async def remove_user_group(
    user_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """移除用户的用户组"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的用户ID")

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    from app.services.group_service import UserGroupService

    await UserGroupService.remove_user_group(db, user)
    await db.commit()

    return {
        "message": f"已移除用户 {user.username} 的用户组",
        "user": user_to_response(user)
    }
