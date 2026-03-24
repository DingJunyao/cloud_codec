"""系统信息 API"""
from fastapi import APIRouter
from app.services.hw_accel import get_supported_hw_accels

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/hw-accel")
async def get_hw_accel_support():
    """获取系统支持的硬件加速列表"""
    return {
        "supported": get_supported_hw_accels(),
        "available": [
            {"value": "auto", "label": "自动"},
            {"value": "none", "label": "禁用"},
            {"value": "nvenc", "label": "NVIDIA NVENC"},
            {"value": "qsv", "label": "Intel QSV"},
            {"value": "vaapi", "label": "VAAPI"},
            {"value": "videotoolbox", "label": "VideoToolbox"},
            {"value": "amf", "label": "AMD AMF"}
        ]
    }
