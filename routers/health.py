"""Health check endpoint router."""

from fastapi import APIRouter
from config.database import check_connection

router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/health")
async def health_check():
    db_ok = await check_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
        "service": "VideoNotes AI FastAPI"
    }
