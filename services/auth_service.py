"""Authentication business logic."""

import random
import string
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from models.user import (
    find_user_by_email,
    create_user,
    mark_user_verified,
    update_user_password,
    create_oauth_user
)
from models.auth import (
    store_verification_code,
    verify_code,
    store_password_reset_code,
    verify_password_reset_code
)
from utils.security import verify_password, hash_password, create_access_token
from utils.email import send_verification_email, send_password_reset_email
from config.settings import settings

def _generate_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))

async def register_user(email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
    existing = await find_user_by_email(email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    pwd_hash = hash_password(password)
    is_verified = not settings.require_email_verification
    user = await create_user(email, pwd_hash, name=name, is_verified=is_verified)
    
    if settings.require_email_verification:
        code = _generate_code()
        await store_verification_code(email, code)
        await send_verification_email(email, code)
    
    token = create_access_token({"sub": user["id"], "email": user["email"]})
    return {"user": user, "token": token}

async def login_user(email: str, password: str) -> Dict[str, Any]:
    user = await find_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    user_id = str(user["id"])
    token = create_access_token({"sub": user_id, "email": user["email"]})
    return {
        "user": {
            "id": user_id,
            "email": user["email"],
            "name": user.get("name"),
            "isVerified": user.get("is_verified", True),
            "createdAt": user["created_at"].isoformat() if user.get("created_at") else None
        },
        "token": token
    }

async def verify_email_code(email: str, code: str) -> bool:
    success = await verify_code(email, code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    await mark_user_verified(email)
    return True

async def request_password_reset(email: str):
    user = await find_user_by_email(email)
    if not user:
        return
    code = _generate_code()
    await store_password_reset_code(email, code)
    await send_password_reset_email(email, code)

async def reset_password(email: str, code: str, new_password: str):
    success = await verify_password_reset_code(email, code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset code"
        )
    user = await find_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    pwd_hash = hash_password(new_password)
    await update_user_password(str(user["id"]), pwd_hash)
