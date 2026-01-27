"""
认证路由模块

提供用户注册、登录、Token 刷新等接口
"""

from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.database import User, get_db
from ..schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    Token,
    PasswordChange,
)
from ..services.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    authenticate_user,
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    get_user_by_username,
)
from ..utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    用户注册
    
    - **username**: 用户名（3-50字符）
    - **password**: 密码（至少6字符）
    - **email**: 邮箱（可选）
    """
    # 检查是否允许注册
    if not settings.auth.allow_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前不允许用户注册"
        )
    
    # 检查用户名是否已存在
    existing_user = await get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    if user_data.email:
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
    
    # 创建用户
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        is_admin=False,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info(f"新用户注册: {new_user.username}")
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    
    返回 JWT Token，有效期默认24小时
    """
    user = await authenticate_user(db, user_data.username, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建 Token
    access_token_expires = timedelta(minutes=settings.auth.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "is_admin": user.is_admin,
        },
        expires_delta=access_token_expires,
    )
    
    logger.info(f"用户登录: {user.username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.auth.access_token_expire_minutes * 60,
    }


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    获取当前登录用户信息
    
    需要在请求头中携带 Token：
    ```
    Authorization: Bearer <token>
    ```
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    更新当前用户信息
    
    - **email**: 新邮箱（可选）
    - **password**: 新密码（可选，至少6字符）
    """
    # 更新邮箱
    if user_data.email is not None:
        # 检查邮箱是否已被使用
        result = await db.execute(
            select(User).where(
                User.email == user_data.email,
                User.id != current_user.id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
        current_user.email = user_data.email
    
    # 更新密码
    if user_data.password is not None:
        current_user.hashed_password = get_password_hash(user_data.password)
    
    await db.commit()
    await db.refresh(current_user)
    
    logger.info(f"用户信息已更新: {current_user.username}")
    
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    修改密码
    
    - **old_password**: 原密码
    - **new_password**: 新密码（至少6字符）
    """
    # 验证原密码
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    # 更新密码
    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    logger.info(f"用户密码已修改: {current_user.username}")
    
    return {"message": "密码修改成功"}


# ==================== 管理员接口 ====================

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> List[User]:
    """
    获取所有用户列表（管理员）
    
    - **skip**: 跳过记录数
    - **limit**: 返回记录数限制
    """
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    启用/禁用用户（管理员）
    
    - **user_id**: 用户ID
    """
    # 不能禁用自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user.is_active = not user.is_active
    await db.commit()
    
    status_text = "启用" if user.is_active else "禁用"
    logger.info(f"用户 {user.username} 已被{status_text}")
    
    return {
        "message": f"用户已{status_text}",
        "user_id": user_id,
        "is_active": user.is_active,
    }


@router.put("/users/{user_id}/toggle-admin")
async def toggle_user_admin(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    设置/取消管理员权限（管理员）
    
    - **user_id**: 用户ID
    """
    # 不能取消自己的管理员权限
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的管理员权限"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user.is_admin = not user.is_admin
    await db.commit()
    
    status_text = "设置为管理员" if user.is_admin else "取消管理员权限"
    logger.info(f"用户 {user.username} 已被{status_text}")
    
    return {
        "message": f"用户已{status_text}",
        "user_id": user_id,
        "is_admin": user.is_admin,
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    删除用户（管理员）
    
    - **user_id**: 用户ID
    """
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    username = user.username
    await db.delete(user)
    await db.commit()
    
    logger.info(f"用户已删除: {username}")
    
    return {"message": f"用户 {username} 已删除"}
