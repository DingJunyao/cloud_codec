"""系统预设初始化服务"""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.preset import Preset
from app.schemas.encode_config import DEFAULT_PRESETS

logger = logging.getLogger(__name__)


async def init_system_presets(db: AsyncSession) -> int:
    """
    初始化系统预设

    Returns:
        创建的预设数量
    """
    # 检查是否已有系统预设
    result = await db.execute(
        select(Preset).where(Preset.is_builtin == True).limit(1)
    )
    existing = result.scalar_one_or_none()

    if existing:
        logger.info("系统预设已存在，跳过初始化")
        return 0

    created_count = 0

    for i, preset_data in enumerate(DEFAULT_PRESETS):
        preset = Preset(
            name=preset_data["name"],
            description=preset_data.get("description", ""),
            is_builtin=True,
            is_default=(i == 0),  # 第一个预设为默认
            created_by=None,
            config=preset_data["config"],
        )
        db.add(preset)
        created_count += 1
        logger.info(f"创建系统预设: {preset_data['name']}")

    await db.commit()
    logger.info(f"系统预设初始化完成，共 {created_count} 个")

    return created_count


async def get_default_preset(db: AsyncSession) -> Preset | None:
    """获取默认预设"""
    result = await db.execute(
        select(Preset).where(
            Preset.is_builtin == True,
            Preset.is_default == True
        )
    )
    return result.scalar_one_or_none()
