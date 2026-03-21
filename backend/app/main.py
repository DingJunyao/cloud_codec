"""主应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware import RequestLoggingMiddleware, TimingMiddleware
import logging

logger = logging.getLogger(__name__)

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"Starting {settings.APP_NAME}...")
    logger.info(f"Environment: {settings.APP_ENV}")

    # 初始化数据库
    from app.database import init_db
    await init_db()
    logger.info("Database initialized")

    yield
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
