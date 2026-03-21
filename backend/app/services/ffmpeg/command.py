"""FFmpeg 命令构建"""
from typing import List
from app.services.ffmpeg.base import get_encoder, FFmpegConfig


class FFmpegCommandBuilder:
    """FFmpeg 命令构建器"""

    def __init__(self, config: FFmpegConfig | None = None):
        self.config = config or FFmpegConfig()
        self.cmd: List[str] = [self.config.ffmpeg_path]

    def input(self, file_path: str) -> "FFmpegCommandBuilder":
        self.cmd.extend(["-i", file_path])
        return self

    def overwrite(self) -> "FFmpegCommandBuilder":
        self.cmd.append("-y")
        return self

    def video_codec(self, codec: str, hw_accel: str = "auto") -> "FFmpegCommandBuilder":
        encoder = get_encoder(codec, hw_accel)
        self.cmd.extend(["-c:v", encoder])
        return self

    def video_preset(self, preset: str) -> "FFmpegCommandBuilder":
        self.cmd.extend(["-preset", preset])
        return self

    def video_crf(self, crf: int) -> "FFmpegCommandBuilder":
        self.cmd.extend(["-crf", str(crf)])
        return self

    def video_scale(self, width: int | None, height: int | None) -> "FFmpegCommandBuilder":
        if width or height:
            scale_expr = f"scale={width or -2}:{height or -2}"
            self.cmd.extend(["-vf", scale_expr])
        return self

    def audio_codec(self, codec: str) -> "FFmpegCommandBuilder":
        self.cmd.extend(["-c:a", codec])
        return self

    def audio_bitrate(self, bitrate: str) -> "FFmpegCommandBuilder":
        self.cmd.extend(["-b:a", bitrate])
        return self

    def format(self, container: str) -> "FFmpegCommandBuilder":
        self.cmd.extend(["-f", container.lstrip(".")])
        return self

    def output(self, file_path: str) -> List[str]:
        self.cmd.append(file_path)
        return self.cmd


def build_ffmpeg_command(
    input_file: str,
    output_file: str,
    config: dict
) -> List[str]:
    """构建 FFmpeg 命令"""
    video_cfg = config.get("video", {})
    audio_cfg = config.get("audio", {})

    builder = FFmpegCommandBuilder()
    builder.overwrite()
    builder.input(input_file)

    codec = video_cfg.get("codec", "h264")
    hw_accel = video_cfg.get("hw_accel", "auto")
    builder.video_codec(codec, hw_accel)

    if "preset" in video_cfg:
        builder.video_preset(video_cfg["preset"])
    if "crf" in video_cfg:
        builder.video_crf(video_cfg["crf"])
    if "width" in video_cfg or "height" in video_cfg:
        builder.video_scale(video_cfg.get("width"), video_cfg.get("height"))

    builder.audio_codec(audio_cfg.get("codec", "aac"))
    if "bitrate" in audio_cfg:
        builder.audio_bitrate(audio_cfg["bitrate"])

    container = config.get("container", "mp4")
    return builder.output(output_file)
