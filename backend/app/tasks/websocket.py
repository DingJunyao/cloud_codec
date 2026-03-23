"""WebSocket 进度推送 - 使用 Redis Pub/Sub 跨进程通信"""
from typing import Dict, Set
from fastapi import WebSocket
import json
import asyncio
import logging
from collections import deque
from datetime import datetime
import redis.asyncio as aioredis
import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_active_connections: Dict[str, Set[WebSocket]] = {}
# 日志缓存：每个任务最多保存 1000 条历史日志（用于实时推送）
_log_history: Dict[str, deque] = {}
MAX_LOG_HISTORY = 1000

# Redis Pub/Sub 频道名称
REDIS_CHANNEL = "task_progress"

# Redis 客户端（同步版本，用于 RQ worker）
_redis_sync: redis.Redis = None

# 同步数据库引擎（用于 RQ worker）
_sync_db_engine = None
_sync_session_factory = None
_sync_session_context = None


def get_redis_sync() -> redis.Redis:
    """获取同步 Redis 客户端（用于 RQ worker）"""
    global _redis_sync
    if _redis_sync is None:
        _redis_sync = redis.from_url(settings.REDIS_URL)
    return _redis_sync


def get_sync_db_session():
    """获取同步数据库会话（用于 RQ worker）- 返回 context manager"""
    global _sync_db_engine, _sync_session_factory, _sync_session_context
    if _sync_session_context is None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from contextlib import contextmanager

        # 将异步数据库 URL 转换为同步
        db_url = settings.DATABASE_URL
        db_url = db_url.replace("+aiosqlite", "").replace("+aiomysql", "").replace("+aiopostgres", "")

        _sync_db_engine = create_engine(db_url, echo=False, pool_pre_ping=True)
        _sync_session_factory = sessionmaker(bind=_sync_db_engine, expire_on_commit=False)

        @contextmanager
        def session_context():
            session = _sync_session_factory()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

        _sync_session_context = session_context

    return _sync_session_context()


def _determine_log_type(data: dict) -> str:
    """根据日志数据判断日志类型"""
    if data.get("type") == "error":
        return "error"
    if data.get("type") == "progress":
        return "progress"

    # 检查日志内容
    line = ""
    if data.get("type") == "log" and isinstance(data.get("data"), dict):
        line = data["data"].get("line", "")
    elif isinstance(data.get("data"), dict):
        line = data["data"].get("line", "")

    line_lower = line.lower()
    if "error" in line_lower or "失败" in line or "异常" in line:
        return "error"
    if "进度" in line or "progress" in line_lower:
        return "progress"

    return "info"


def _extract_log_message(data: dict) -> str:
    """从日志数据中提取消息内容"""
    if data.get("type") == "log" and isinstance(data.get("data"), dict):
        return data["data"].get("line", "")
    if isinstance(data.get("data"), dict):
        return data["data"].get("line", "")
    return json.dumps(data)


async def connect_websocket(websocket: WebSocket, task_id: str):
    """连接 WebSocket"""
    await websocket.accept()
    if task_id not in _active_connections:
        _active_connections[task_id] = set()
    _active_connections[task_id].add(websocket)

    # 发送历史日志（过滤掉 status 和 progress 类型，避免影响当前状态）
    if task_id in _log_history:
        for log_data in _log_history[task_id]:
            # 只发送日志类型，不发送状态变更和进度更新（进度应从数据库获取）
            if log_data.get("type") == "log":
                try:
                    await websocket.send_text(json.dumps(log_data))
                except Exception:
                    pass


def disconnect_websocket(websocket: WebSocket, task_id: str):
    """断开 WebSocket"""
    if task_id in _active_connections:
        _active_connections[task_id].discard(websocket)
        # 注意：不要在没有连接时清理日志缓存
        # 用户可能在任务运行期间多次连接/断开


def add_log_to_history(task_id: str, data: dict, persist: bool = True):
    """
    添加日志到历史缓存和数据库（线程安全）

    Args:
        task_id: 任务ID
        data: 日志数据
        persist: 是否持久化到数据库（默认True）
    """
    # 保存到内存缓存
    if task_id not in _log_history:
        _log_history[task_id] = deque(maxlen=MAX_LOG_HISTORY)
    _log_history[task_id].append(data)

    # 持久化到数据库
    if persist:
        try:
            from uuid import UUID
            log_type = _determine_log_type(data)
            message = _extract_log_message(data)

            with get_sync_db_session() as db:
                from app.models.task_log import TaskLog
                log_entry = TaskLog(
                    task_id=UUID(task_id),
                    log_type=log_type,
                    message=message
                )
                db.add(log_entry)
                # commit 由 context manager 自动处理
        except Exception as e:
            # 数据库写入失败不影响主流程
            logger.warning(f"[{task_id}] 日志持久化失败: {e}")


async def broadcast_task_progress(task_id: str, data: dict):
    """向任务的所有 WebSocket 连接广播进度（本地进程内）"""
    # 保存到历史缓存
    add_log_to_history(task_id, data)

    if task_id not in _active_connections:
        return

    message = json.dumps(data)
    disconnected = set()

    for websocket in _active_connections[task_id]:
        try:
            await websocket.send_text(message)
        except Exception:
            disconnected.add(websocket)

    for ws in disconnected:
        disconnect_websocket(ws, task_id)


def broadcast_task_progress_sync(task_id: str, data: dict, loop: asyncio.AbstractEventLoop = None):
    """
    同步版本的广播函数，用于在子线程/子进程中调用
    通过 Redis Pub/Sub 发布消息，由 FastAPI 进程接收并广播

    Args:
        task_id: 任务ID
        data: 要广播的数据
        loop: 可选的事件循环（现在不再使用，保留参数兼容性）
    """
    # 保存到历史缓存（线程安全）
    add_log_to_history(task_id, data)

    # 更新数据库中的进度（用于轮询获取）
    if data.get("type") == "progress":
        try:
            progress_data = data.get("data", {})
            progress_percent = progress_data.get("percent", 0)

            with get_sync_db_session() as db:
                from uuid import UUID
                from app.models.task import Task
                task = db.query(Task).filter(Task.id == UUID(task_id)).first()
                if task:
                    task.progress = int(progress_percent)
                    task.progress_data = progress_data
                    # commit 由 context manager 自动处理
        except Exception as e:
            logger.warning(f"[{task_id}] 更新数据库进度失败: {e}")

    # 通过 Redis Pub/Sub 发布消息
    try:
        r = get_redis_sync()
        message = json.dumps({
            "task_id": task_id,
            "data": data
        })
        r.publish(REDIS_CHANNEL, message)
    except Exception as e:
        logger.warning(f"[{task_id}] Redis 发布失败: {e}")


async def _do_broadcast(task_id: str, data: dict):
    """实际执行广播的异步函数"""
    if task_id not in _active_connections:
        return

    message = json.dumps(data)
    disconnected = set()

    for websocket in _active_connections[task_id]:
        try:
            await websocket.send_text(message)
        except Exception:
            disconnected.add(websocket)

    for ws in disconnected:
        disconnect_websocket(ws, task_id)


async def redis_subscriber():
    """
    Redis 订阅器 - 在 FastAPI 启动时运行
    接收来自 RQ worker 的消息并广播给 WebSocket 客户端
    """
    logger.info("启动 Redis 订阅器...")
    try:
        redis_client = await aioredis.from_url(settings.REDIS_URL)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(REDIS_CHANNEL)

        logger.info(f"已订阅 Redis 频道: {REDIS_CHANNEL}")

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    payload = json.loads(message["data"])
                    task_id = payload.get("task_id")
                    data = payload.get("data")

                    if task_id and data:
                        # 只保存到内存缓存（日志已在 worker 进程中持久化）
                        add_log_to_history(task_id, data, persist=False)
                        # 广播给 WebSocket 客户端
                        await _do_broadcast(task_id, data)

                except json.JSONDecodeError as e:
                    logger.warning(f"JSON 解析错误: {e}")
                except Exception as e:
                    logger.error(f"处理消息错误: {e}")

    except asyncio.CancelledError:
        logger.info("Redis 订阅器已停止")
    except Exception as e:
        logger.error(f"Redis 订阅器错误: {e}")
    finally:
        try:
            await pubsub.unsubscribe(REDIS_CHANNEL)
            await redis_client.close()
        except Exception:
            pass
