"""WebSocket 进度推送"""
from typing import Dict, Set
from fastapi import WebSocket
import json

_active_connections: Dict[str, Set[WebSocket]] = {}


async def connect_websocket(websocket: WebSocket, task_id: str):
    """连接 WebSocket"""
    await websocket.accept()
    if task_id not in _active_connections:
        _active_connections[task_id] = set()
    _active_connections[task_id].add(websocket)


def disconnect_websocket(websocket: WebSocket, task_id: str):
    """断开 WebSocket"""
    if task_id in _active_connections:
        _active_connections[task_id].discard(websocket)


async def broadcast_task_progress(task_id: str, data: dict):
    """向任务的所有 WebSocket 连接广播进度"""
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
