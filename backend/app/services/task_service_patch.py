    def _enqueue_task(self, task_id: str, user_id: str):
        """将任务加入队列"""
        from rq import Queue
        from redis import Redis
        from redis.exceptions import RedisError
        from app.core.config import settings
        from app.tasks.encode import encode_task

        # FFmpeg 转码任务超时：1 年（31536000 秒）
        FFMPEG_JOB_TIMEOUT = 31536000

        try:
            redis_conn = Redis.from_url(settings.REDIS_URL)
            # 测试连接
            redis_conn.ping()
            queue = Queue(connection=redis_conn)
            # 设置 job_timeout 为 1 年，避免长时间转码任务被强制终止
            queue.enqueue(encode_task, task_id, user_id, job_timeout=FFMPEG_JOB_TIMEOUT)
        except RedisError as e:
            raise ConnectionError(f"任务队列服务不可用，请确保 Redis 已启动: {e}")
