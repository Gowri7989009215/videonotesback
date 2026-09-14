"""Authentication router."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.schemas import (
    RegisterRequest,
    LoginRequest,
    VerifyEmailRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from services.auth_service import (
    register_user,
    login_user,
    verify_email_code,
    request_password_reset,
    reset_password
)
from utils.security import decode_access_token
from models.user import find_user_by_id

router = APIRouter(prefix="/api/auth", tags=["Auth"])
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await find_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

@router.post("/register")
async def register(req: RegisterRequest):
    return await register_user(req.email, req.password, name=req.name)

@router.post("/login")
async def login(req: LoginRequest):
    return await login_user(req.email, req.password)

@router.post("/verify")
async def verify(req: VerifyEmailRequest):
    await verify_email_code(req.email, req.code)
    return {"message": "Email verified successfully"}

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    await request_password_reset(req.email)
    return {"message": "Password reset email sent if account exists"}

@router.post("/reset-password")
async def reset_pwd(req: ResetPasswordRequest):
    await reset_password(req.email, req.code, req.new_password)
    return {"message": "Password reset successfully"}

@router.get("/me")
async def get_me(user = Depends(get_current_user)):
    return {
        "id": str(user["id"]),
        "email": user["email"],
        "name": user.get("name"),
        "isVerified": user.get("is_verified", True),
        "createdAt": user["created_at"].isoformat() if user.get("created_at") else None
    }
