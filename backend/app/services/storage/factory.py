"""存储工厂"""
from app.services.storage.base import StorageBackend
from app.services.storage.local import LocalStorage
from app.core.config import settings

_storage_backend: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """获取存储后端实例（单例）"""
    global _storage_backend
    if _storage_backend is None:
        _storage_backend = LocalStorage()
    return _storage_backend


async def init_storage():
    """初始化存储"""
    storage = get_storage()
    if hasattr(storage, "base_path"):
        import os
        os.makedirs(storage.base_path, exist_ok=True)
