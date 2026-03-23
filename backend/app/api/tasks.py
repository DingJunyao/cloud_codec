"""任务 API 路由"""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timezone
from app.schemas.task import TaskCreate, TaskResponse
from app.services.task_service import TaskService
from app.tasks.websocket import connect_websocket, disconnect_websocket
from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.task_log import TaskLog

router = APIRouter(prefix="/tasks", tags=["tasks"])


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


def task_to_response(task) -> dict:
    """将任务模型转换为响应格式"""
    return {
        "id": str(task.id),
        "name": task.name,
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
        "updated_at": format_datetime_utc(task.updated_at),
    }


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建转码任务"""
    service = TaskService()
    try:
        task = await service.create_task(db, task_data, str(current_user.id))
        return task_to_response(task)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    service = TaskService()
    tasks = await service.list_tasks(db, str(current_user.id), status)
    return [task_to_response(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务详情"""
    service = TaskService()
    task = await service.get_task(db, task_id, str(current_user.id))
    return task_to_response(task)


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """取消任务"""
    service = TaskService()
    task = await service.cancel_task(db, task_id, str(current_user.id))
    return task_to_response(task)


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除任务（仅限已完成、失败、已取消的任务）"""
    service = TaskService()
    await service.delete_task(db, task_id, str(current_user.id))
    return {"message": "任务已删除"}


@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """重新转码任务（仅限已完成、失败、已取消的任务）"""
    service = TaskService()
    try:
        task = await service.retry_task(db, task_id, str(current_user.id))
        return task_to_response(task)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/{task_id}/download")
async def download_task_result(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """下载转码结果"""
    service = TaskService()
    return await service.get_download_url(db, task_id, str(current_user.id))


@router.websocket("/ws/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: str):
    """任务进度 WebSocket"""
    await connect_websocket(websocket, task_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        disconnect_websocket(websocket, task_id)


@router.get("/{task_id}/logs")
async def get_task_logs(
    task_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务历史日志"""
    from uuid import UUID

    # 先验证任务存在且属于当前用户
    service = TaskService()
    await service.get_task(db, task_id, str(current_user.id))

    # 转换为 UUID 类型
    task_uuid = UUID(task_id)

    # 查询日志
    result = await db.execute(
        select(TaskLog)
        .where(TaskLog.task_id == task_uuid)
        .order_by(TaskLog.created_at)
        .offset(offset)
        .limit(limit)
    )
    logs = result.scalars().all()

    # 获取总数
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count()).where(TaskLog.task_id == task_uuid)
    )
    total = count_result.scalar()

    return {
        "total": total,
        "logs": [
            {
                "id": str(log.id),
                "type": log.log_type,
                "message": log.message,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    }
