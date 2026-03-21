"""FFmpeg 基础配置"""
from dataclasses import dataclass
from app.core.config import settings


@dataclass
class FFmpegConfig:
    """FFmpeg 配置"""
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"


ENCODER_MAP = {
    "h264": {
        "nvenc": "h264_nvenc",
        "qsv": "h264_qsv",
        "vaapi": "h264_vaapi",
        "software": "libx264",
    },
    "h265": {
        "nvenc": "hevc_nvenc",
        "qsv": "hevc_qsv",
        "vaapi": "hevc_vaapi",
        "software": "libx265",
    },
}


def get_encoder(codec: str, hw_accel: str = "auto") -> str:
    """获取编码器名称"""
    if codec not in ENCODER_MAP:
        return "libx264"
    encoders = ENCODER_MAP[codec]
    if hw_accel == "auto":
        return encoders.get("nvenc", encoders.get("software", "libx264"))
    return encoders.get(hw_accel, encoders["software"])
