"""任务 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from datetime import datetime


class TaskCreate(BaseModel):
    """创建任务请求"""
    source_file: str = Field(..., description="源文件路径")
    preset_id: Optional[str] = Field(None, description="预设ID (UUID)")
    config: Optional[Dict[str, Any]] = Field(None, description="自定义转码配置，与 preset_id 二选一")
    name: Optional[str] = Field(None, max_length=200, description="任务名称（默认为源文件名）")


class TaskResponse(BaseModel):
    """任务响应"""
    id: str = Field(..., description="任务ID (UUID)")
    name: str = Field(..., description="任务名称")
    status: Literal["pending", "processing", "completed", "failed", "cancelled"] = Field(
        ..., description="任务状态"
    )
    progress: int = Field(..., ge=0, le=100, description="进度百分比")
    progress_data: Optional[Dict[str, Any]] = Field(
        None,
        description="进度详情 {fps, speed, eta, frame, total_frames}"
    )
    source_file: str = Field(..., description="源文件路径")
    source_size: Optional[int] = Field(None, description="源文件大小（字节）")
    output_file: Optional[str] = Field(None, description="输出文件路径")
    output_size: Optional[int] = Field(None, description="输出文件大小（字节）")
    preset_id: Optional[str] = Field(None, description="预设ID")
    config: Dict[str, Any] = Field(..., description="转码配置")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应"""
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int


class TaskProgressUpdate(BaseModel):
    """任务进度更新（WebSocket 推送）"""
    type: Literal["progress", "log", "status", "error"] = Field(..., description="消息类型")
    data: Dict[str, Any] = Field(..., description="消息数据")


class TaskLogEntry(BaseModel):
    """任务日志条目"""
    id: str
    task_id: str
    level: Literal["debug", "info", "warning", "error"]
    message: str
    created_at: datetime


class DownloadInfo(BaseModel):
    """下载信息"""
    url: str
    filename: str
    size: Optional[int] = None
