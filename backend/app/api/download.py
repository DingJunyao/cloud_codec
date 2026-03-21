"""文件下载 API"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User
from typing import Optional

router = APIRouter(prefix="/download", tags=["download"])


@router.get("/")
async def download_file(
    path: str,
    current_user: User = Depends(get_current_user)
):
    """下载文件"""
    # 安全检查：确保路径在用户目录下
    file_path = Path(settings.storage_dir) / path.lstrip("/")

    # 验证路径
    try:
        file_path = file_path.resolve()
        storage_path = Path(settings.storage_dir).resolve()
        file_path.relative_to(storage_path)
    except ValueError:
        raise HTTPException(status_code=403, detail="无权访问此文件")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(file_path, filename=file_path.name)
