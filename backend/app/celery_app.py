"""Celery 应用实例"""
from celery import Celery
from app.core.config import settings

# 创建 Celery 实例
celery_app = Celery(
    "cloudcodec",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# 配置
celery_app.conf.update(
    # 任务结果过期时间（1天）
    result_expires=86400,
    # 接受的序列化格式
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    # 时区
    timezone="UTC",
    # 启用任务跟踪
    task_track_started=True,
    # 任务超时（1年，用于长时间转码任务）
    task_time_limit=31536000,
    # 软超时
    task_soft_time_limit=31536000 - 3600,
)

# 自动发现任务
celery_app.autodiscover_tasks(["app.tasks"])
