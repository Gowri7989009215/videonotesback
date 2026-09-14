"""Pydantic schemas for request and response models."""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str = Field(..., min_length=6)

class OAuthLoginRequest(BaseModel):
    id_token: str

class CreateJobRequest(BaseModel):
    video_id: Optional[str] = None
    youtube_url: Optional[str] = None
    mode: str = "frames+transcript"
    interval_seconds: int = 3

class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
