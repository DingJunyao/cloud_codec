"""硬件加速支持检测"""
import subprocess
import logging
from typing import List, Optional, Dict, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class HardwareAccelService:
    """硬件加速服务"""

    def __init__(self):
        self._supported: Optional[List[str]] = None
        self._encoders: Optional[Dict[str, List[str]]] = None

    def get_supported(self) -> List[str]:
        """获取支持的硬件加速方法"""
        if self._supported is None:
            self._supported = get_supported_hw_accels()
        return self._supported

    def is_available(self, hw_accel: str) -> bool:
        """检查硬件加速是否可用"""
        if hw_accel in ["auto", "none"]:
            return True
        return hw_accel in self.get_supported()

    def get_best_available(self) -> Optional[str]:
        """获取最佳可用的硬件加速方法"""
        supported = self.get_supported()
        # 按优先级排序（nvenc > qsv > vaapi > videotoolbox > amf）
        priority = ["nvenc", "qsv", "vaapi", "videotoolbox", "amf"]
        for accel in priority:
            if accel in supported:
                return accel
        return None

    def get_status(self) -> Dict[str, Any]:
        """获取硬件加速状态"""
        return {
            "supported": self.get_supported(),
            "available_count": len(self.get_supported())
        }


@lru_cache
def get_supported_hw_accels() -> List[str]:
    """获取系统支持的硬件加速方法列表（带缓存）"""
    supported = ["auto", "none"]  # 始终支持

    # 测试各种硬件编码器是否真的可用
    encoders_to_test = [
        ("nvenc", "h264_nvenc"),
        ("qsv", "h264_qsv"),
        ("vaapi", "h264_vaapi"),
        ("videotoolbox", "h264_videotoolbox"),
        ("amf", "h264_amf")
    ]

    for accel_name, encoder in encoders_to_test:
        if _test_encoder_available(encoder):
            supported.append(accel_name)
            logger.info(f"硬件编码器可用: {accel_name} ({encoder})")
        else:
            logger.debug(f"硬件编码器不可用: {accel_name} ({encoder})")

    return supported


def _test_encoder_available(encoder: str) -> bool:
    """测试编码器是否真的可用"""
    try:
        # 根据编码器选择合适的 preset 参数
        preset_map = {
            "h264_nvenc": "p1",
            "hevc_nvenc": "p1",
            "h264_qsv": "faster",
            "hevc_qsv": "faster",
            "h264_vaapi": "",  # vaapi 不支持 preset
            "hevc_vaapi": "",
            "h264_videotoolbox": "medium",
            "hevc_videotoolbox": "medium",
            "h264_amf": "speed",
            "hevc_amf": "speed"
        }

        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", "testsrc=duration=1:size=160x120:rate=1",
            "-c:v", encoder
        ]

        # 添加 preset 参数（如果支持）
        preset = preset_map.get(encoder, "")
        if preset:
            cmd.extend(["-preset", preset])

        cmd.extend(["-f", "null", "-"])

        # 使用 Popen 替代 run，以支持超时终止和 start_new_session
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True  # 创建新会话，避免终端信号影响
        )
        try:
            stdout, stderr = process.communicate(timeout=5)

            # 检查是否有编码器加载失败的关键错误
            error_output = stderr.lower()
            critical_errors = [
                "cannot load",
                "could not load",
                "no nvidia",
                "libcuda.so.1",
                "libnpp",
                "driver not found",
                "no intel media",
                "libva",
                "videotoolbox"
            ]

            for error in critical_errors:
                if error in error_output:
                    logger.debug(f"{encoder} 检测到关键错误: {error}")
                    return False

            # 成功编码
            return process.returncode == 0
        except subprocess.TimeoutExpired:
            # 超时时终止进程
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            return False
    except Exception as e:
        logger.debug(f"{encoder} 测试异常: {e}")
        return False


_hw_accel_service: Optional[HardwareAccelService] = None


def get_hw_accel_service() -> HardwareAccelService:
    """获取硬件加速服务单例"""
    global _hw_accel_service
    if _hw_accel_service is None:
        _hw_accel_service = HardwareAccelService()
    return _hw_accel_service


def get_available_hw_accel() -> List[str]:
    """获取可用的硬件加速列表"""
    return get_hw_accel_service().get_supported()


def get_encoder(codec: str, hw_accel: str = "auto") -> str:
    """根据编解码器和硬件加速获取编码器名称"""
    if hw_accel == "none":
        hw_accel = None
    
    # H.264 编码器
    if codec.lower() in ["h264", "h.264"]:
        if hw_accel == "nvenc":
            return "h264_nvenc"
        if hw_accel == "qsv":
            return "h264_qsv"
        if hw_accel == "vaapi":
            return "h264_vaapi"
        if hw_accel == "videotoolbox":
            return "h264_videotoolbox"
        if hw_accel == "amf":
            return "h264_amf"
        return "libx264"
    
    # H.265 编码器
    if codec.lower() in ["h265", "hevc", "h.265"]:
        if hw_accel == "nvenc":
            return "hevc_nvenc"
        if hw_accel == "qsv":
            return "hevc_qsv"
        if hw_accel == "vaapi":
            return "hevc_vaapi"
        if hw_accel == "videotoolbox":
            return "hevc_videotoolbox"
        if hw_accel == "amf":
            return "hevc_amf"
        return "libx265"
    
    # 其他编解码器返回原值
    return codec


def get_decoder(codec: str, hw_accel: str = "auto") -> str:
    """根据编解码器和硬件加速获取解码器名称"""
    if hw_accel in ["none", "auto"]:
        return codec
    
    # H.264 解码器
    if codec.lower() in ["h264", "h.264"]:
        if hw_accel == "nvenc":
            return "h264_cuvid"
        if hw_accel == "qsv":
            return "h264_qsv"
        if hw_accel == "vaapi":
            return "h264_vaapi"
    
    # H.265 解码器
    if codec.lower() in ["h265", "hevc", "h.265"]:
        if hw_accel == "nvenc":
            return "hevc_cuvid"
        if hw_accel == "qsv":
            return "hevc_qsv"
        if hw_accel == "vaapi":
            return "hevc_vaapi"
    
    return codec
