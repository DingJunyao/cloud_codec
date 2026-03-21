"""本地存储实现"""
import aiofiles
import os
import shutil
from app.services.storage.base import StorageBackend
from app.core.config import settings


class LocalStorage(StorageBackend):
    """本地文件系统存储"""

    def __init__(self):
        self.base_path = settings.STORAGE_PATH

    def get_full_path(self, path: str) -> str:
        """获取完整文件路径"""
        safe_path = Path(path).as_posix()
        if safe_path.startswith("..") or "/../" in safe_path:
            raise ValueError("Invalid path")
        full_path = (self.base_path / safe_path).resolve()
        return str(full_path)

    async def save(self, path: str, content: bytes) -> str:
        """保存文件内容"""
        full_path = self.get_full_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)
        return full_path

    async def read(self, path: str) -> bytes:
        """读取文件内容"""
        full_path = self.get_full_path(path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, path: str) -> bool:
        """删除文件"""
        full_path = self.get_full_path(path)
        if not os.path.exists(full_path):
            return False
        os.remove(full_path)
        return True

    async def exists(self, path: str) -> bool:
        """检查文件是否存在"""
        return os.path.exists(self.get_full_path(path))

    async def get_size(self, path: str) -> int:
        """获取文件大小"""
        full_path = self.get_full_path(path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
        return os.path.getsize(full_path)
