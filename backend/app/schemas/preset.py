"""预设 Schema"""
from pydantic import BaseModel, Field


class PresetCreate(BaseModel):
    """创建预设请求"""
    name: str = Field(..., description="预设名称")
    video_codec: str = Field("", description="视频编码器")
    video_bitrate: str = Field("", description="视频比特率")
    video_resolution: str = Field("", description="视频分辨率")
    fps: int = Field(None, description="帧率")
    audio_codec: str = Field("", description="音频编码器")
    audio_bitrate: str = Field("", description="音频比特率")
    audio_channels: int = Field(None, description="音频声道数")
    output_format: str = Field("mp4", description="输出格式")
    extra_options: str = Field("", description="额外选项")


class PresetResponse(PresetCreate):
    """预设响应"""
    id: int
    user_id: int
    is_system: bool

    class Config:
        from_attributes = True
