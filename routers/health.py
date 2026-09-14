"""Health check endpoint router."""

from fastapi import APIRouter
from config.database import check_connection

router = APIRouter(tags=["Health"])

@router.get("/health")
@router.get("/api/health")
async def health_check():
    db_ok = await check_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
        "service": "VideoNotes AI FastAPI"
    }
