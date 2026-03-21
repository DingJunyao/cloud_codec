"""任务 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class TaskCreate(BaseModel):
    """创建任务请求"""
    name: str = Field(..., description="任务名称")
    video_path: str = Field(..., description="视频文件路径")
    preset_id: int = Field(..., description="预设ID")
    output_name: Optional[str] = Field(None, description="输出文件名")


class TaskResponse(BaseModel):
    """任务响应"""
    id: str
    name: str
    status: Literal["pending", "processing", "completed", "failed", "cancelled"]
    progress: float
    input_path: str
    output_path: Optional[str]
    preset_id: int
    preset_name: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    user_id: int

    class Config:
        from_attributes = True
