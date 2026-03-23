"""预设 API 路由"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.preset import PresetCreate, PresetUpdate, PresetClone, PresetResponse
from app.models.preset import Preset
from app.models.user import User
from app.core.deps import get_current_user, get_current_admin
from app.database import get_db
from uuid import UUID
import copy

router = APIRouter(prefix="/presets", tags=["presets"])


def preset_to_response(preset: Preset) -> dict:
    """将预设模型转换为响应格式"""
    return {
        "id": str(preset.id),
        "name": preset.name,
        "description": preset.description,
        "is_builtin": preset.is_builtin,
        "is_default": preset.is_default,
        "created_by": preset.created_by,
        "config": preset.config,
        "created_at": preset.created_at,
        "updated_at": preset.updated_at,
    }


@router.get("/", response_model=List[PresetResponse])
async def list_presets(
    is_builtin: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取预设列表（系统预设 + 用户个人预设）"""
    query = select(Preset).where(
        or_(
            Preset.is_builtin == True,
            Preset.created_by == str(current_user.id)
        )
    ).order_by(Preset.is_builtin.desc(), Preset.created_at.desc())

    if is_builtin is not None:
        query = query.where(Preset.is_builtin == is_builtin)

    result = await db.execute(query)
    presets = result.scalars().all()
    return [preset_to_response(p) for p in presets]


@router.get("/{preset_id}", response_model=PresetResponse)
async def get_preset(
    preset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取预设详情"""
    try:
        uuid = UUID(preset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的预设ID")

    result = await db.execute(select(Preset).where(Preset.id == uuid))
    preset = result.scalar_one_or_none()

    if not preset:
        raise HTTPException(status_code=404, detail="预设不存在")

    # 检查权限：系统预设所有人可见，个人预设仅创建者可见
    if not preset.is_builtin and preset.created_by != str(current_user.id):
        raise HTTPException(status_code=404, detail="预设不存在")

    return preset_to_response(preset)


@router.post("/", response_model=PresetResponse)
async def create_preset(
    data: PresetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建个人预设"""
    preset = Preset(
        name=data.name,
        description=data.description,
        is_builtin=False,
        is_default=False,
        created_by=str(current_user.id),
        config=data.config.model_dump(),
    )
    db.add(preset)
    await db.commit()
    await db.refresh(preset)
    return preset_to_response(preset)


@router.post("/{preset_id}/clone", response_model=PresetResponse)
async def clone_preset(
    preset_id: str,
    data: Optional[PresetClone] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """克隆预设（系统预设或个人预设）"""
    try:
        uuid = UUID(preset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的预设ID")

    result = await db.execute(select(Preset).where(Preset.id == uuid))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="预设不存在")

    # 检查权限
    if not source.is_builtin and source.created_by != str(current_user.id):
        raise HTTPException(status_code=404, detail="预设不存在")

    # 深拷贝配置
    cloned_config = copy.deepcopy(source.config)

    # 确定新名称
    clone_data = data or PresetClone()
    new_name = clone_data.name or f"{source.name} (副本)"

    # 创建新预设
    preset = Preset(
        name=new_name,
        description=source.description,
        is_builtin=False,
        is_default=False,
        created_by=str(current_user.id),
        config=cloned_config,
    )
    db.add(preset)
    await db.commit()
    await db.refresh(preset)
    return preset_to_response(preset)


@router.put("/{preset_id}", response_model=PresetResponse)
async def update_preset(
    preset_id: str,
    data: PresetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新个人预设"""
    try:
        uuid = UUID(preset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的预设ID")

    result = await db.execute(select(Preset).where(Preset.id == uuid))
    preset = result.scalar_one_or_none()

    if not preset:
        raise HTTPException(status_code=404, detail="预设不存在")

    # 不能修改系统预设
    if preset.is_builtin:
        raise HTTPException(status_code=403, detail="不能修改系统预设")

    # 只能修改自己的预设
    if preset.created_by != str(current_user.id):
        raise HTTPException(status_code=403, detail="无权修改此预设")

    # 更新字段
    if data.name is not None:
        preset.name = data.name
    if data.description is not None:
        preset.description = data.description
    if data.config is not None:
        preset.config = data.config.model_dump()

    await db.commit()
    await db.refresh(preset)
    return preset_to_response(preset)


@router.delete("/{preset_id}")
async def delete_preset(
    preset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除个人预设"""
    try:
        uuid = UUID(preset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的预设ID")

    result = await db.execute(select(Preset).where(Preset.id == uuid))
    preset = result.scalar_one_or_none()

    if not preset:
        raise HTTPException(status_code=404, detail="预设不存在")

    # 不能删除系统预设
    if preset.is_builtin:
        raise HTTPException(status_code=403, detail="不能删除系统预设")

    # 只能删除自己的预设
    if preset.created_by != str(current_user.id):
        raise HTTPException(status_code=403, detail="无权删除此预设")

    await db.delete(preset)
    await db.commit()
    return {"message": "删除成功"}
