"""认证相关的 Pydantic 模型"""
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., min_length=3)
    password: str


class UserResponse(UserBase):
    """用户响应模型"""
    id: UUID
    is_active: bool
    is_admin: bool
    group_id: UUID | None = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Token 响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str


class PasswordUpdateRequest(BaseModel):
    """密码更新请求"""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
