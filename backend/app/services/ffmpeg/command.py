"""FFmpeg 命令构建"""
from typing import List, Optional
from app.services.hw_accel import get_encoder, get_decoder, get_hw_accel_service


class FFmpegCommandBuilder:
    """FFmpeg 命令构建器"""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        self.cmd: List[str] = [ffmpeg_path]
        self._hw_accel_used: Optional[str] = None

    def overwrite(self) -> "FFmpegCommandBuilder":
        """覆盖输出文件"""
        self.cmd.append("-y")
        return self

    def hide_banner(self) -> "FFmpegCommandBuilder":
        """隐藏 banner"""
        self.cmd.append("-hide_banner")
        return self

    def hw_accel(self, hw_accel: str = "auto") -> "FFmpegCommandBuilder":
        """设置硬件加速"""
        if hw_accel == "none":
            return self

        service = get_hw_accel_service()

        if hw_accel == "auto":
            hw_accel = service.get_best_available() or "none"
            if hw_accel == "none":
                return self

        # 添加硬件加速参数
        if hw_accel == "nvenc":
            self.cmd.extend(["-hwaccel", "cuda"])
        elif hw_accel == "qsv":
            self.cmd.extend(["-hwaccel", "qsv"])
        elif hw_accel == "vaapi":
            self.cmd.extend(["-hwaccel", "vaapi"])
        elif hw_accel == "videotoolbox":
            self.cmd.extend(["-hwaccel", "videotoolbox"])
        elif hw_accel == "amf":
            self.cmd.extend(["-hwaccel", "d3d11va"])

        self._hw_accel_used = hw_accel
        return self

    def input(self, file_path: str) -> "FFmpegCommandBuilder":
        """设置输入文件"""
        self.cmd.extend(["-i", file_path])
        return self

    def video_codec(self, codec: str, hw_accel: str = "auto") -> "FFmpegCommandBuilder":
        """设置视频编码器"""
        encoder = get_encoder(codec, hw_accel)
        self.cmd.extend(["-c:v", encoder])
        return self

    def video_preset(self, preset: str) -> "FFmpegCommandBuilder":
        """设置编码预设"""
        self.cmd.extend(["-preset", preset])
        return self

    def video_crf(self, crf: int) -> "FFmpegCommandBuilder":
        """设置 CRF 质量"""
        self.cmd.extend(["-crf", str(crf)])
        return self

    def video_bitrate(self, bitrate: str) -> "FFmpegCommandBuilder":
        """设置视频码率"""
        self.cmd.extend(["-b:v", bitrate])
        return self

    def video_profile(self, profile: str) -> "FFmpegCommandBuilder":
        """设置编码配置"""
        self.cmd.extend(["-profile:v", profile])
        return self

    def video_level(self, level: str) -> "FFmpegCommandBuilder":
        """设置编码级别"""
        self.cmd.extend(["-level", level])
        return self

    def video_scale(
        self,
        width: Optional[int],
        height: Optional[int],
        keep_aspect: bool = True
    ) -> "FFmpegCommandBuilder":
        """设置视频缩放"""
        if not width and not height:
            return self

        # -2 表示自动计算以保持宽高比，同时确保是偶数
        w = width or -2
        h = height or -2

        if keep_aspect:
            # 使用 force_original_aspect_ratio=decrease 确保不超出指定尺寸
            # 然后用 pad 确保尺寸是偶数
            scale_expr = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2"
        else:
            # 直接缩放并确保偶数
            scale_expr = f"scale={w}:{h},pad=ceil(iw/2)*2:ceil(ih/2)*2"

        self.cmd.extend(["-vf", scale_expr])
        return self

    def video_fps(self, fps: int) -> "FFmpegCommandBuilder":
        """设置帧率"""
        self.cmd.extend(["-r", str(fps)])
        return self

    def audio_codec(self, codec: str) -> "FFmpegCommandBuilder":
        """设置音频编码器"""
        if codec == "none":
            self.cmd.extend(["-an"])
        elif codec == "copy":
            self.cmd.extend(["-c:a", "copy"])
        else:
            self.cmd.extend(["-c:a", codec])
        return self

    def audio_bitrate(self, bitrate: str) -> "FFmpegCommandBuilder":
        """设置音频码率"""
        self.cmd.extend(["-b:a", bitrate])
        return self

    def audio_channels(self, channels: int) -> "FFmpegCommandBuilder":
        """设置音频声道数"""
        self.cmd.extend(["-ac", str(channels)])
        return self

    def audio_sample_rate(self, sample_rate: int) -> "FFmpegCommandBuilder":
        """设置音频采样率"""
        self.cmd.extend(["-ar", str(sample_rate)])
        return self

    def format(self, container: str) -> "FFmpegCommandBuilder":
        """设置容器格式"""
        self.cmd.extend(["-f", container.lstrip(".")])
        return self

    def progress(self, output: str = "pipe:1") -> "FFmpegCommandBuilder":
        """设置进度输出"""
        self.cmd.extend(["-progress", output])
        return self

    def custom_params(self, params: str) -> "FFmpegCommandBuilder":
        """添加自定义参数"""
        if params:
            self.cmd.extend(params.split())
        return self

    def filter_complex(self, filter_str: str) -> "FFmpegCommandBuilder":
        """添加复杂滤镜"""
        self.cmd.extend(["-filter_complex", filter_str])
        return self

    def output(self, file_path: str) -> List[str]:
        """设置输出文件并返回完整命令"""
        self.cmd.append(file_path)
        return self.cmd

    def build(self) -> List[str]:
        """返回当前命令"""
        return self.cmd


def build_ffmpeg_command(
    input_file: str,
    output_file: str,
    config: dict,
    progress_pipe: bool = True
) -> List[str]:
    """
    根据配置构建 FFmpeg 命令

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        config: 转码配置
        progress_pipe: 是否输出进度到管道

    Returns:
        FFmpeg 命令列表
    """
    video_cfg = config.get("video", {})
    audio_cfg = config.get("audio", {})
    codec_options = video_cfg.get("codec_options", {})
    resolution_cfg = video_cfg.get("resolution", {})

    hw_accel = video_cfg.get("hw_accel", "auto")

    builder = FFmpegCommandBuilder()
    builder.overwrite()
    builder.hide_banner()

    # 硬件加速（解码）
    builder.hw_accel(hw_accel)

    # 输入文件
    builder.input(input_file)

    # 视频编码
    codec = video_cfg.get("codec", "h264")
    if codec == "copy":
        builder.cmd.extend(["-c:v", "copy"])
    else:
        builder.video_codec(codec, hw_accel)

        # 编码参数（仅软件编码器支持部分参数）
        if hw_accel in ["none", "auto"] or not get_hw_accel_service().is_available(hw_accel or ""):
            if "preset" in codec_options:
                builder.video_preset(codec_options["preset"])
            if "crf" in codec_options:
                builder.video_crf(codec_options["crf"])
        else:
            # 硬件编码器使用 preset
            if "preset" in codec_options:
                builder.video_preset(codec_options["preset"])
            # 硬件编码器使用 CQP 或码率
            if "crf" in codec_options:
                # NVENC 使用 -cq
                if hw_accel == "nvenc":
                    builder.cmd.extend(["-cq", str(codec_options["crf"])])

        if "profile" in codec_options:
            builder.video_profile(codec_options["profile"])
        if "level" in codec_options:
            builder.video_level(codec_options["level"])
        if "bitrate" in codec_options:
            builder.video_bitrate(codec_options["bitrate"])

    # 分辨率
    mode = resolution_cfg.get("mode", "auto")
    has_scale_filter = False
    if mode != "auto":
        width = resolution_cfg.get("width")
        height = resolution_cfg.get("height")
        keep_aspect = resolution_cfg.get("keep_aspect", True)
        builder.video_scale(width, height, keep_aspect)
        has_scale_filter = True

    # 帧率
    if video_cfg.get("fps"):
        builder.video_fps(video_cfg["fps"])

    # 音频编码
    audio_codec = audio_cfg.get("codec", "aac")
    builder.audio_codec(audio_codec)

    if audio_codec not in ["copy", "none"]:
        if "bitrate" in audio_cfg:
            builder.audio_bitrate(audio_cfg["bitrate"])
        if "channels" in audio_cfg:
            builder.audio_channels(audio_cfg["channels"])
        if "sample_rate" in audio_cfg:
            builder.audio_sample_rate(audio_cfg["sample_rate"])

    # 容器格式
    container = config.get("container", "mp4")
    builder.format(container)

    # 进度输出
    if progress_pipe:
        builder.progress("pipe:1")

    # 自定义参数
    if config.get("custom_params"):
        builder.custom_params(config["custom_params"])

    # 滤镜
    filters = config.get("filters", [])
    filter_parts = []
    for f in filters:
        ftype = f.get("type")
        params = f.get("params", {})
        if ftype == "scale":
            filter_parts.append(f"scale={params.get('width', -2)}:{params.get('height', -2)}")
            has_scale_filter = True
        elif ftype == "deinterlace":
            filter_parts.append("yadif")
        elif ftype == "denoise":
            filter_parts.append("hqdn3d")
        # 可以添加更多滤镜类型

    # 如果视频编码器不是 copy，需要确保尺寸是偶数
    if codec != "copy" and not has_scale_filter:
        # 添加 pad 滤镜确保尺寸是偶数
        filter_parts.append("pad=ceil(iw/2)*2:ceil(ih/2)*2")

    if filter_parts:
        builder.filter_complex(",".join(filter_parts))

    return builder.output(output_file)
