"""预设 Schema"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.schemas.encode_config import EncodeConfig


class PresetBase(BaseModel):
    """预设基础字段"""
    name: str = Field(..., min_length=1, max_length=100, description="预设名称")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    config: EncodeConfig = Field(..., description="转码配置")


class PresetCreate(PresetBase):
    """创建预设请求"""
    pass


class PresetUpdate(BaseModel):
    """更新预设请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    config: Optional[EncodeConfig] = None


class PresetClone(BaseModel):
    """克隆预设请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="新预设名称，默认为原名称副本")


class PresetResponse(BaseModel):
    """预设响应"""
    id: str = Field(..., description="预设ID (UUID)")
    name: str = Field(..., description="预设名称")
    description: Optional[str] = Field(None, description="描述")
    is_builtin: bool = Field(..., description="是否为系统内置预设")
    is_default: bool = Field(..., description="是否为默认预设")
    created_by: Optional[str] = Field(None, description="创建者用户ID")
    config: dict = Field(..., description="转码配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True
