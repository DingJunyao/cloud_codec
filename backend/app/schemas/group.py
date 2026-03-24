"""用户组相关 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID


class UserGroupBase(BaseModel):
    """用户组基础 Schema"""
    name: str = Field(..., min_length=1, max_length=50, description="用户组名称")
    description: Optional[str] = Field(None, description="用户组描述")
    max_file_size: Optional[int] = Field(None, ge=0, description="最大文件大小（字节）")
    max_storage: Optional[int] = Field(None, ge=0, description="最大存储空间（字节）")
    result_retention_days: Optional[int] = Field(None, ge=0, description="结果保留天数")
    local_paths: Optional[List[str]] = Field(None, description="允许访问的本地路径列表")
    allowed_preset_ids: Optional[List[str]] = Field(None, description="允许使用的预设ID列表")
    default_preset_id: Optional[str] = Field(None, description="默认预设ID")
    api_access_enabled: bool = Field(False, description="是否允许API访问")
    email_enabled: bool = Field(False, description="是否启用邮件通知")


class UserGroupCreate(UserGroupBase):
    """创建用户组 Schema"""
    pass


class UserGroupUpdate(BaseModel):
    """更新用户组 Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="用户组名称")
    description: Optional[str] = Field(None, description="用户组描述")
    max_file_size: Optional[int] = Field(None, ge=0, description="最大文件大小（字节）")
    max_storage: Optional[int] = Field(None, ge=0, description="最大存储空间（字节）")
    result_retention_days: Optional[int] = Field(None, ge=0, description="结果保留天数")
    local_paths: Optional[List[str]] = Field(None, description="允许访问的本地路径列表")
    allowed_preset_ids: Optional[List[str]] = Field(None, description="允许使用的预设ID列表")
    default_preset_id: Optional[str] = Field(None, description="默认预设ID")
    api_access_enabled: Optional[bool] = Field(None, description="是否允许API访问")
    email_enabled: Optional[bool] = Field(None, description="是否启用邮件通知")


class UserGroupResponse(UserGroupBase):
    """用户组响应 Schema"""
    id: UUID = Field(..., description="用户组ID")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    user_count: int = Field(0, description="用户数量")

    class Config:
        from_attributes = True


class PermissionResponse(BaseModel):
    """权限响应 Schema"""
    id: UUID = Field(..., description="权限ID")
    code: str = Field(..., description="权限代码")
    name: str = Field(..., description="权限名称")
    description: Optional[str] = Field(None, description="权限描述")

    class Config:
        from_attributes = True
