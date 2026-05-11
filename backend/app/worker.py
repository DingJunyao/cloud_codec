"""Celery Worker 入口"""
import sys

# 显式导入任务模块以注册任务
from app.tasks import encode  # noqa: F401

from app.celery_app import celery_app
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info(f"Starting Celery Worker on {sys.platform}")

    # Windows 必须使用 solo 池，Linux/macOS 使用 prefork
    pool = "solo" if sys.platform == "win32" else "prefork"
    logger.info(f"Using pool: {pool}")

    celery_app.worker_main(["worker", "--loglevel=info", f"--pool={pool}"])
