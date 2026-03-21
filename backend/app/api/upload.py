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
    upload_dir = Path(settings.storage_dir) / "uploads" / str(current_user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名
    file_ext = Path(file.filename).suffix
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / filename

    # 保存文件
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 返回相对路径
    relative_path = file_path.relative_to(settings.storage_dir)
    return {"file_path": str(relative_path), "filename": filename}
