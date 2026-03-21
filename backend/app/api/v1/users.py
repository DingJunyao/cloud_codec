"""用户管理 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.api.deps import get_current_user
from app.schemas.auth import UserResponse, PasswordUpdateRequest
from app.services.user_service import UserService
from app.models.user import User

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """获取当前用户信息"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    email: str | None = None
):
    """更新当前用户信息"""
    if email:
        current_user.email = email
        await db.commit()
        await db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.put("/me/password")
async def update_my_password(
    password_data: PasswordUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """更新当前用户密码"""
    try:
        await UserService.update_password(
            db,
            current_user,
            password_data.old_password,
            password_data.new_password
        )
        await db.commit()
    except ValueError as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return {"message": "Password updated successfully"}
