"""API v1 路由聚合"""
from fastapi import APIRouter

api_router = APIRouter()

# 导入现有路由
from app.api.v1 import auth, users, groups

# 认证和用户
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(groups.router)

# 管理后台
from app.api import admin
api_router.include_router(admin.router)

# 任务和预设
from app.api import tasks, presets, upload, download
api_router.include_router(tasks.router)
api_router.include_router(presets.router)
api_router.include_router(upload.router)
api_router.include_router(download.router)

__all__ = ["api_router"]
