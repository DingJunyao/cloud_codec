"""硬件加速检测服务"""
import subprocess
import platform
import logging
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# 硬件加速优先级（可配置）
HW_ACCEL_PRIORITY = [
    'nvenc',        # NVIDIA GPU
    'qsv',          # Intel Quick Sync
    'vaapi',        # Linux VAAPI
    'videotoolbox', # macOS
    'amf',          # AMD
]

# 编解码器到硬件编码器的映射
ENCODER_MAP = {
    'h264': {
        'nvenc': 'h264_nvenc',
        'qsv': 'h264_qsv',
        'vaapi': 'h264_vaapi',
        'videotoolbox': 'h264_videotoolbox',
        'amf': 'h264_amf',
        'software': 'libx264',
    },
    'h265': {
        'nvenc': 'hevc_nvenc',
        'qsv': 'hevc_qsv',
        'vaapi': 'hevc_vaapi',
        'videotoolbox': 'hevc_videotoolbox',
        'amf': 'hevc_amf',
        'software': 'libx265',
    },
    'hevc': {
        'nvenc': 'hevc_nvenc',
        'qsv': 'hevc_qsv',
        'vaapi': 'hevc_vaapi',
        'videotoolbox': 'hevc_videotoolbox',
        'amf': 'hevc_amf',
        'software': 'libx265',
    },
    'vp9': {
        'nvenc': None,  # 不支持
        'qsv': None,
        'vaapi': 'vp9_vaapi',
        'videotoolbox': None,
        'amf': None,
        'software': 'libvpx-vp9',
    },
    'av1': {
        'nvenc': 'av1_nvenc',
        'qsv': 'av1_qsv',
        'vaapi': 'av1_vaapi',
        'videotoolbox': None,
        'amf': 'av1_amf',
        'software': 'libaom-av1',
    },
}

# 解码器映射
DECODER_MAP = {
    'h264': {
        'nvenc': 'h264_cuvid',
        'qsv': 'h264_qsv',
        'vaapi': 'h264_vaapi',
        'videotoolbox': 'h264',
        'amf': 'h264',
        'software': 'h264',
    },
    'h265': {
        'nvenc': 'hevc_cuvid',
        'qsv': 'hevc_qsv',
        'vaapi': 'hevc_vaapi',
        'videotoolbox': 'hevc',
        'amf': 'hevc',
        'software': 'hevc',
    },
}


class HardwareAccelService:
    """硬件加速检测和管理服务"""

    _instance: Optional['HardwareAccelService'] = None
    _available: dict[str, bool] = {}
    _ffmpeg_path: str = 'ffmpeg'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._detect_all()

    def _detect_all(self):
        """检测所有硬件加速方案"""
        system = platform.system()

        # 根据系统调整优先级
        if system == 'Darwin':  # macOS
            priority = ['videotoolbox', 'nvenc', 'qsv']
        elif system == 'Linux':
            priority = ['nvenc', 'vaapi', 'qsv', 'amf']
        else:  # Windows
            priority = ['nvenc', 'qsv', 'amf']

        logger.info(f"检测硬件加速，系统: {system}")

        for hw_accel in priority:
            available = self._detect(hw_accel)
            self._available[hw_accel] = available
            status = "可用" if available else "不可用"
            logger.info(f"  {hw_accel}: {status}")

    def _detect(self, hw_accel: str) -> bool:
        """检测特定硬件加速是否可用"""
        detectors = {
            'nvenc': self._detect_nvenc,
            'qsv': self._detect_qsv,
            'vaapi': self._detect_vaapi,
            'videotoolbox': self._detect_videotoolbox,
            'amf': self._detect_amf,
        }

        detector = detectors.get(hw_accel)
        if detector:
            try:
                return detector()
            except Exception as e:
                logger.debug(f"检测 {hw_accel} 时出错: {e}")
                return False
        return False

    def _detect_nvenc(self) -> bool:
        """检测 NVIDIA NVENC - 需要 NVIDIA GPU 和驱动"""
        try:
            # 首先检查 FFmpeg 是否支持
            result = subprocess.run(
                [self._ffmpeg_path, '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if 'h264_nvenc' not in result.stdout:
                return False

            # 检查 NVIDIA 驱动是否存在（nvidia-smi）
            try:
                nvidia_smi = subprocess.run(
                    ['nvidia-smi'],
                    capture_output=True,
                    timeout=5
                )
                return nvidia_smi.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                return False
        except Exception:
            return False

    def _detect_vaapi(self) -> bool:
        """检测 Linux VAAPI - 需要实际测试硬件编码"""
        if platform.system() != 'Linux':
            return False
        try:
            # 检查 /dev/dri/renderD128 是否存在
            import os
            if not os.path.exists('/dev/dri/renderD128'):
                return False

            # 检查 FFmpeg 是否支持 VAAPI
            result = subprocess.run(
                [self._ffmpeg_path, '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if 'vaapi' not in result.stdout:
                return False

            # 实际测试 VAAPI 是否可用（关键！）
            test_result = subprocess.run(
                [self._ffmpeg_path, '-hide_banner', '-vaapi_device', '/dev/dri/renderD128',
                 '-f', 'lavfi', '-i', 'nullsrc=s=256x256:d=0.1',
                 '-vf', 'format=nv12,hwupload', '-c:v', 'h264_vaapi', '-f', 'null', '-'],
                capture_output=True,
                text=True,
                timeout=10
            )
            # 如果返回码为 0，VAAPI 可用
            return test_result.returncode == 0
        except Exception:
            return False

    def _detect_qsv(self) -> bool:
        """检测 Intel Quick Sync"""
        try:
            result = subprocess.run(
                [self._ffmpeg_path, '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return 'h264_qsv' in result.stdout and 'hevc_qsv' in result.stdout
        except Exception:
            return False

    def _detect_videotoolbox(self) -> bool:
        """检测 macOS VideoToolbox"""
        if platform.system() != 'Darwin':
            return False
        try:
            result = subprocess.run(
                [self._ffmpeg_path, '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return 'videotoolbox' in result.stdout
        except Exception:
            return False

    def _detect_amf(self) -> bool:
        """检测 AMD AMF"""
        if platform.system() != 'Windows':
            return False
        try:
            result = subprocess.run(
                [self._ffmpeg_path, '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return 'h264_amf' in result.stdout and 'hevc_amf' in result.stdout
        except Exception:
            return False

    def get_available(self) -> list[str]:
        """获取所有可用的硬件加速方案"""
        return [k for k, v in self._available.items() if v]

    def is_available(self, hw_accel: str) -> bool:
        """检查特定硬件加速是否可用"""
        return self._available.get(hw_accel, False)

    def get_best_available(self) -> Optional[str]:
        """获取最佳可用硬件加速方案"""
        for hw_accel in HW_ACCEL_PRIORITY:
            if self._available.get(hw_accel, False):
                return hw_accel
        return None

    def get_encoder(self, codec: str, hw_accel: str = 'auto') -> str:
        """
        获取编码器名称

        Args:
            codec: 编解码器 (h264, h265, vp9, av1)
            hw_accel: 硬件加速类型 (auto, none, nvenc, qsv, vaapi, videotoolbox, amf)

        Returns:
            编码器名称
        """
        codec_map = ENCODER_MAP.get(codec, ENCODER_MAP.get('h264'))

        if hw_accel == 'none':
            return codec_map['software']

        if hw_accel == 'auto':
            # 自动选择最佳可用
            best = self.get_best_available()
            if best and codec_map.get(best):
                return codec_map[best]
            return codec_map['software']

        # 指定硬件加速
        if self._available.get(hw_accel, False):
            encoder = codec_map.get(hw_accel)
            if encoder:
                return encoder

        # 降级到软件编码
        logger.warning(f"硬件加速 {hw_accel} 不可用，降级到软件编码")
        return codec_map['software']

    def get_decoder(self, codec: str, hw_accel: str = 'auto') -> str:
        """获取解码器名称"""
        codec_map = DECODER_MAP.get(codec, {})

        if hw_accel == 'none' or hw_accel == 'auto':
            if hw_accel == 'auto':
                best = self.get_best_available()
                if best and codec_map.get(best):
                    return codec_map[best]
            return codec_map.get('software', codec)

        if self._available.get(hw_accel, False):
            return codec_map.get(hw_accel, codec_map.get('software', codec))

        return codec_map.get('software', codec)

    def get_status(self) -> dict:
        """获取硬件加速状态摘要"""
        return {
            'available': self.get_available(),
            'best': self.get_best_available(),
            'details': dict(self._available),
            'system': platform.system(),
        }


# 全局单例
_hw_accel_service: Optional[HardwareAccelService] = None


def get_hw_accel_service() -> HardwareAccelService:
    """获取硬件加速服务单例"""
    global _hw_accel_service
    if _hw_accel_service is None:
        _hw_accel_service = HardwareAccelService()
    return _hw_accel_service


def get_encoder(codec: str, hw_accel: str = 'auto') -> str:
    """便捷函数：获取编码器"""
    return get_hw_accel_service().get_encoder(codec, hw_accel)


def get_decoder(codec: str, hw_accel: str = 'auto') -> str:
    """便捷函数：获取解码器"""
    return get_hw_accel_service().get_decoder(codec, hw_accel)


def get_available_hw_accel() -> list[str]:
    """便捷函数：获取可用硬件加速列表"""
    return get_hw_accel_service().get_available()
