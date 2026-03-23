"""RQ Worker 入口"""
import redis
from rq import Worker, Queue, Connection
from app.core.config import settings
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def run_worker():
    """运行 RQ Worker
    
    注意：任务超时时间在 task_service.py 的 enqueue() 中设置 job_timeout 参数。
    FFmpeg 转码任务设置为 1 年（31536000 秒）以避免被强制终止。
    """
    redis_url = settings.REDIS_URL
    logger.info(f"Worker starting, connecting to: {redis_url}")

    with Connection(redis.from_url(redis_url)):
        qs = [Queue('default')]
        worker = Worker(qs)
        logger.info("Worker started, listening for tasks...")
        worker.work()


if __name__ == "__main__":
    run_worker()
