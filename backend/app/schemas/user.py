"""用户 Schema"""
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str | None
    is_admin: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str
