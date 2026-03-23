"""核心配置"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List, Optional
from pathlib import Path
from urllib.parse import urlparse


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # 应用配置
    APP_NAME: str = "码上转"
    APP_ENV: str = Field(default="development", pattern="^(development|production|testing)$")
    APP_SECRET: str = Field(min_length=32)
    APP_URL: str = "http://localhost:8000"

    @field_validator("APP_URL")
    @classmethod
    def validate_app_url(cls, v):
        """验证应用 URL 格式"""
        result = urlparse(v)
        if not all([result.scheme, result.netloc]):
            raise ValueError("APP_URL must be a valid URL")
        return v.rstrip("/")

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/cloudcodec.db"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v):
        """验证数据库 URL 格式"""
        if not v.startswith(("sqlite+", "postgresql+", "mysql+")):
            raise ValueError("DATABASE_URL must start with 'sqlite+', 'postgresql+', or 'mysql+'")
        return v

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # 存储配置
    STORAGE_TYPE: str = Field(default="local", pattern="^(local|s3)$")
    STORAGE_PATH: Path = Field(default=Path("./data"))

    @field_validator("STORAGE_PATH", mode="before")
    @classmethod
    def validate_storage_path(cls, v):
        """确保存储路径是绝对路径，基于 backend 目录"""
        path = Path(v) if not isinstance(v, Path) else v
        if not path.is_absolute():
            # 获取 backend 目录（config.py 所在目录的父目录）
            backend_dir = Path(__file__).parent.parent.parent
            path = backend_dir / path
        return path.resolve()

    # JWT 配置
    JWT_SECRET: str = Field(min_length=32)
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, gt=0)

    # CORS 配置
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        """解析 CORS 源列表，开发环境允许所有来源"""
        if self.APP_ENV == "development":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # 文件上传配置
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024 * 1024, gt=0)
    ALLOWED_VIDEO_TYPES: str = "video/mp4,video/x-matroska,video/webm,video/quicktime,video/x-msvideo"

    @property
    def ALLOWED_VIDEO_TYPES_LIST(self) -> List[str]:
        """解析允许的视频类型列表"""
        return [t.strip() for t in self.ALLOWED_VIDEO_TYPES.split(",")]

    # FFmpeg 配置
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    HW_ACCEL_PRIORITY: str = "nvenc,qsv,vaapi,videotoolbox,amf"

    @property
    def HW_ACCEL_LIST(self) -> List[str]:
        """硬件加速优先级列表"""
        return [a.strip() for a in self.HW_ACCEL_PRIORITY.split(",") if a.strip()]

    def model_post_init(self, __context: object) -> None:
        """配置初始化后处理"""
        # 确保存储目录存在
        self.STORAGE_PATH.mkdir(parents=True, exist_ok=True)


settings = Settings()
