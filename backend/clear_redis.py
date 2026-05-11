"""清空 Redis 队列"""
import redis
from app.core.config import settings

redis_conn = redis.from_url(settings.REDIS_URL)
redis_conn.flushall()
print("Redis 已清空")
