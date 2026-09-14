"""User stats and profile router."""

from fastapi import APIRouter, Depends
from routers.auth import get_current_user
from models.video import get_user_stats

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/stats")
async def user_stats(user = Depends(get_current_user)):
    user_id = str(user["id"])
    return await get_user_stats(user_id)

@router.get("/me")
async def get_user_me(user = Depends(get_current_user)):
    return {
        "id": str(user["id"]),
        "email": user["email"],
        "name": user.get("name") or user["email"].split("@")[0],
        "isVerified": user.get("is_verified", True),
        "createdAt": user["created_at"].isoformat() if user.get("created_at") else None
    }
