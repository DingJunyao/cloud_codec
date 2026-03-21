"""存储抽象基类"""
from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    async def save(self, path: str, content: bytes) -> str:
        """保存文件内容，返回路径"""
        pass

    @abstractmethod
    async def read(self, path: str) -> bytes:
        """读取文件"""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """检查文件是否存在"""
        pass

    @abstractmethod
    async def get_size(self, path: str) -> int:
        """获取文件大小"""
        pass

    def get_full_path(self, path: str) -> str:
        """获取完整文件路径"""
        return str(self.base_path / path)
