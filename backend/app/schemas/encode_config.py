"""转码配置 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class VideoCodecOptions(BaseModel):
    """视频编码器选项"""
    preset: Optional[str] = Field(
        "medium",
        description="编码预设",
        pattern="^(ultrafast|superfast|veryfast|faster|fast|medium|slow|slower|veryslow)$"
    )
    crf: Optional[int] = Field(
        23,
        ge=0,
        le=51,
        description="质量因子 (0-51)"
    )
    profile: Optional[str] = Field(
        None,
        description="编码配置",
        pattern="^(baseline|main|high|high10|high422|high444)$"
    )
    level: Optional[str] = Field(
        None,
        description="编码级别",
        pattern="^[0-9]+(\\.[0-9])?$"
    )
    bitrate: Optional[str] = Field(
        None,
        description="目标码率 (如 5M, 2500K)",
        pattern="^[0-9]+[KMk]?$"
    )


class ResolutionConfig(BaseModel):
    """分辨率配置"""
    mode: Literal["auto", "custom", "scale"] = Field(
        "auto",
        description="分辨率模式"
    )
    width: Optional[int] = Field(
        None,
        ge=1,
        le=7680,
        description="宽度"
    )
    height: Optional[int] = Field(
        None,
        ge=1,
        le=4320,
        description="高度"
    )
    keep_aspect: bool = Field(
        True,
        description="保持宽高比"
    )


class VideoConfig(BaseModel):
    """视频配置"""
    codec: str = Field(
        "h264",
        description="视频编解码器",
        pattern="^(h264|h265|hevc|vp9|av1|copy)$"
    )
    codec_options: VideoCodecOptions = Field(
        default_factory=VideoCodecOptions,
        description="编码器选项"
    )
    resolution: ResolutionConfig = Field(
        default_factory=ResolutionConfig,
        description="分辨率配置"
    )
    fps: Optional[int] = Field(
        None,
        ge=1,
        le=120,
        description="帧率 (null 保持原始)"
    )
    hw_accel: Literal["auto", "none", "nvenc", "qsv", "vaapi", "videotoolbox", "amf"] = Field(
        "auto",
        description="硬件加速"
    )


class AudioConfig(BaseModel):
    """音频配置"""
    codec: str = Field(
        "aac",
        description="音频编解码器",
        pattern="^(aac|mp3|opus|ac3|eac3|flac|copy|none)$"
    )
    bitrate: str = Field(
        "128k",
        description="码率",
        pattern="^[0-9]+[KMk]?$"
    )
    channels: Optional[int] = Field(
        2,
        ge=1,
        le=8,
        description="声道数"
    )
    sample_rate: Optional[int] = Field(
        48000,
        ge=8000,
        le=192000,
        description="采样率"
    )


class FilterItem(BaseModel):
    """滤镜项"""
    type: str = Field(..., description="滤镜类型")
    params: dict = Field(default_factory=dict, description="滤镜参数")


class EncodeConfig(BaseModel):
    """完整转码配置"""
    video: VideoConfig = Field(
        default_factory=VideoConfig,
        description="视频配置"
    )
    audio: AudioConfig = Field(
        default_factory=AudioConfig,
        description="音频配置"
    )
    container: Literal["mp4", "mkv", "webm", "mov", "avi"] = Field(
        "mp4",
        description="容器格式"
    )
    filters: List[FilterItem] = Field(
        default_factory=list,
        description="滤镜链"
    )
    custom_params: Optional[str] = Field(
        "",
        description="自定义 FFmpeg 参数"
    )


# 预设的默认配置模板
DEFAULT_PRESETS = [
    {
        "name": "通用兼容",
        "description": "适用于大多数场景的高质量预设，最大兼容性",
        "config": {
            "video": {
                "codec": "h264",
                "codec_options": {"preset": "medium", "crf": 23},
                "resolution": {"mode": "auto"},
                "hw_accel": "auto"
            },
            "audio": {"codec": "aac", "bitrate": "128k", "channels": 2, "sample_rate": 48000},
            "container": "mp4"
        }
    },
    {
        "name": "Web 优化",
        "description": "适用于网页播放的 1080p 视频",
        "config": {
            "video": {
                "codec": "h264",
                "codec_options": {"preset": "medium", "crf": 23, "profile": "high", "level": "4.1"},
                "resolution": {"mode": "scale", "height": 1080, "keep_aspect": True},
                "hw_accel": "auto"
            },
            "audio": {"codec": "aac", "bitrate": "128k", "channels": 2, "sample_rate": 48000},
            "container": "mp4"
        }
    },
    {
        "name": "移动设备",
        "description": "适用于手机平板的 720p 视频",
        "config": {
            "video": {
                "codec": "h264",
                "codec_options": {"preset": "fast", "crf": 26, "profile": "main", "level": "3.1"},
                "resolution": {"mode": "scale", "height": 720, "keep_aspect": True},
                "hw_accel": "auto"
            },
            "audio": {"codec": "aac", "bitrate": "96k", "channels": 2, "sample_rate": 44100},
            "container": "mp4"
        }
    },
    {
        "name": "压缩存储",
        "description": "使用 H.265 编码，节省存储空间",
        "config": {
            "video": {
                "codec": "h265",
                "codec_options": {"preset": "medium", "crf": 28},
                "resolution": {"mode": "auto"},
                "hw_accel": "auto"
            },
            "audio": {"codec": "aac", "bitrate": "128k", "channels": 2, "sample_rate": 48000},
            "container": "mp4"
        }
    },
    {
        "name": "快速转码",
        "description": "速度优先，快速完成转码",
        "config": {
            "video": {
                "codec": "h264",
                "codec_options": {"preset": "veryfast", "crf": 23},
                "resolution": {"mode": "auto"},
                "hw_accel": "auto"
            },
            "audio": {"codec": "aac", "bitrate": "128k", "channels": 2, "sample_rate": 48000},
            "container": "mp4"
        }
    },
    {
        "name": "4K 优化",
        "description": "适用于 4K 视频的高质量预设",
        "config": {
            "video": {
                "codec": "h265",
                "codec_options": {"preset": "slow", "crf": 24, "profile": "main"},
                "resolution": {"mode": "scale", "height": 2160, "keep_aspect": True},
                "hw_accel": "auto"
            },
            "audio": {"codec": "aac", "bitrate": "192k", "channels": 2, "sample_rate": 48000},
            "container": "mp4"
        }
    }
]
