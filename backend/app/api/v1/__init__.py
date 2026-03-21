"""API v1 路由聚合"""
from fastapi import APIRouter

api_router = APIRouter()

# 导入现有路由
from app.api.v1 import auth, users

# 认证和用户
api_router.include_router(auth.router)
api_router.include_router(users.router)

# 任务和预设
from app.api import tasks, presets, upload, download
api_router.include_router(tasks.router)
api_router.include_router(presets.router)
api_router.include_router(upload.router)
api_router.include_router(download.router)

__all__ = ["api_router"]
