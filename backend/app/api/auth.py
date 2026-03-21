"""认证 API 路由"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate, UserResponse, Token
from app.models.user import User
from app.core.security import create_access_token, get_password_hash, verify_password
from app.database import get_db
from sqlalchemy import select

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(data: UserCreate):
    """用户注册"""
    async with get_db() as db:
        # 检查用户名是否已存在
        result = await db.execute(select(User).where(User.username == data.username))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="用户名已存在")

        # 创建用户
        user = User(
            username=data.username,
            email=data.email,
            hashed_password=get_password_hash(data.password)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
    async with get_db() as db:
        result = await db.execute(select(User).where(User.username == form_data.username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        access_token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "token_type": "bearer"}
