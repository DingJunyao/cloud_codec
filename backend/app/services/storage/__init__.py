"""存储服务"""
from app.services.storage.base import StorageBackend
from app.services.storage.factory import get_storage, init_storage

__all__ = ["StorageBackend", "get_storage", "init_storage"]
