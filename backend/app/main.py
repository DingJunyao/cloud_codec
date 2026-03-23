"""主应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware import RequestLoggingMiddleware, TimingMiddleware
import logging
import asyncio

logger = logging.getLogger(__name__)

setup_logging()

# Redis 订阅器任务
_redis_subscriber_task: asyncio.Task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _redis_subscriber_task

    logger.info(f"Starting {settings.APP_NAME}...")
    logger.info(f"Environment: {settings.APP_ENV}")

    # 初始化数据库
    from app.database import init_db
    await init_db()
    logger.info("Database initialized")

    # 初始化系统预设
    from app.services.preset_init import init_system_presets
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await init_system_presets(db)

    logger.info("System presets initialized")

    # 初始化硬件加速检测
    from app.services.hw_accel import get_hw_accel_service
    hw_service = get_hw_accel_service()
    hw_status = hw_service.get_status()
    logger.info(f"Hardware acceleration: {hw_status}")

    # 启动 Redis 订阅器（用于接收 RQ worker 的进度消息）
    from app.tasks.websocket import redis_subscriber
    _redis_subscriber_task = asyncio.create_task(redis_subscriber())
    logger.info("Redis subscriber started")

    yield

    # 关闭 Redis 订阅器
    if _redis_subscriber_task:
        _redis_subscriber_task.cancel()
        try:
            await _redis_subscriber_task
        except asyncio.CancelledError:
            pass

    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Video transcoding service",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自定义中间件
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestLoggingMiddleware)


@app.get("/")
async def root():
    """健康检查"""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "status": "healthy",
        "environment": settings.APP_ENV,
    }


@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "ok"}


@app.get("/config")
async def get_config():
    """获取公开配置（前端使用）"""
    return {
        "appName": settings.APP_NAME,
        "maxUploadSize": settings.MAX_UPLOAD_SIZE,
        "allowedVideoTypes": settings.ALLOWED_VIDEO_TYPES_LIST,
        "corsOrigins": settings.CORS_ORIGINS_LIST,
    }


# 包含路由
from app.api.v1 import api_router
app.include_router(api_router, prefix="/api")
