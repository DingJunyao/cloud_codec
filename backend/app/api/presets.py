"""预设 API 路由"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.preset import PresetCreate, PresetResponse
from app.models.preset import Preset
from app.models.user import User
from app.core.deps import get_current_user, get_current_admin
from app.database import get_db

router = APIRouter(prefix="/presets", tags=["presets"])


@router.get("/", response_model=List[PresetResponse])
async def list_presets(
    is_builtin: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取预设列表"""
    query = select(Preset).where(
        or_(Preset.created_by == str(current_user.id), Preset.is_builtin == True)
    )
    if is_builtin is not None:
        query = query.where(Preset.is_builtin == is_builtin)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=PresetResponse)
async def create_preset(
    data: PresetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建预设"""
    preset = Preset(**data.model_dump(), created_by=str(current_user.id))
    db.add(preset)
    await db.commit()
    await db.refresh(preset)
    return preset


@router.get("/{preset_id}", response_model=PresetResponse)
async def get_preset(
    preset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取预设详情"""
    from uuid import UUID
    result = await db.execute(select(Preset).where(Preset.id == UUID(preset_id)))
    preset = result.scalar_one_or_none()
    if not preset or (preset.created_by != str(current_user.id) and not preset.is_builtin):
        raise HTTPException(status_code=404, detail="预设不存在")
    return preset


@router.delete("/{preset_id}")
async def delete_preset(
    preset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除预设"""
    from uuid import UUID
    result = await db.execute(select(Preset).where(Preset.id == UUID(preset_id)))
    preset = result.scalar_one_or_none()
    if not preset or preset.created_by != str(current_user.id):
        raise HTTPException(status_code=404, detail="预设不存在")
    if preset.is_builtin:
        raise HTTPException(status_code=403, detail="不能删除系统预设")
    await db.delete(preset)
    await db.commit()
    return {"message": "删除成功"}
