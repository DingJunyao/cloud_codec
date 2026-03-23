"""文件上传 API"""
from fastapi import APIRouter, Depends, UploadFile, File
from pathlib import Path
from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User
import uuid

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传文件"""
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("video/"):
        return {"error": "只支持视频文件"}

    # 创建用户目录
    upload_dir = settings.STORAGE_PATH / "uploads" / str(current_user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名（存储用）
    file_ext = Path(file.filename).suffix if file.filename else ".mp4"
    storage_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / storage_filename

    # 流式保存文件（避免内存中缓冲整个文件）
    chunk_size = 1024 * 1024  # 1MB chunks
    with open(file_path, "wb") as f:
        while chunk := await file.read(chunk_size):
            f.write(chunk)

    # 提取原始文件名（不含扩展名）
    original_name = Path(file.filename).stem if file.filename else "video"

    # 返回相对路径和原始文件名
    relative_path = file_path.relative_to(settings.STORAGE_PATH)
    return {
        "file_path": str(relative_path),
        "filename": storage_filename,
        "original_name": original_name  # 原始文件名（不含扩展名）
    }
