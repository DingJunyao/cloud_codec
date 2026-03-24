#!/usr/bin/env python
"""重新将 PENDING 状态的任务加入队列"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker
from rq import Queue
from redis import Redis

from app.core.config import settings
from app.models.task import Task, TaskStatus
from app.tasks.encode import encode_task


def main():
    # 创建同步引擎
    sync_url = settings.DATABASE_URL
    for prefix in ["+aiosqlite", "+asyncpg", "+aiomysql"]:
        sync_url = sync_url.replace(prefix, "")

    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # 重置卡住的 PROCESSING 任务为 PENDING
    session.execute(
        update(Task)
        .where(Task.status == TaskStatus.PROCESSING)
        .values(status=TaskStatus.PENDING, error_message=None)
    )
    session.commit()

    # 查询所有 PENDING 任务
    result = session.execute(
        select(Task).where(Task.status == TaskStatus.PENDING)
    )
    pending_tasks = result.scalars().all()

    if not pending_tasks:
        print("没有待处理的任务")
        return

    # 连接 Redis
    redis_conn = Redis.from_url(settings.REDIS_URL)
    queue = Queue(connection=redis_conn)

    print(f"找到 {len(pending_tasks)} 个待处理任务，正在加入队列...")

    for task in pending_tasks:
        queue.enqueue(
            encode_task,
            str(task.id),
            str(task.user_id),
            job_timeout=31536000
        )
        print(f"  - 任务 {task.id} ({task.name}) 已加入队列")

    print("完成！")


if __name__ == "__main__":
    main()
