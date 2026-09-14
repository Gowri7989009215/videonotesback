"""OAuth authentication router (Google)."""

from fastapi import APIRouter, HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from models.schemas import OAuthLoginRequest
from models.user import create_oauth_user
from utils.security import create_access_token
from config.settings import settings

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/google")
async def google_login(req: OAuthLoginRequest):
    try:
        id_info = id_token.verify_oauth2_token(
            req.id_token,
            google_requests.Request(),
            settings.google_client_id if settings.google_client_id else None
        )
        email = id_info["email"]
        name = id_info.get("name")
        sub = id_info["sub"]

        user = await create_oauth_user(email=email, name=name, provider="google", provider_id=sub)
        token = create_access_token({"sub": user["id"], "email": user["email"]})
        return {"user": user, "token": token}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth verification failed: {e}"
        )
