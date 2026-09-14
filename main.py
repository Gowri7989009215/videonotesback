"""
VideoNotes AI — FastAPI Backend
================================
Main application entry point with Swagger UI enabled.

Swagger UI:  http://localhost:4000/docs
ReDoc:       http://localhost:4000/redoc
"""

import os
import sys
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from os.path import join, dirname

load_dotenv(join(dirname(__file__), ".env"))

from config.settings import settings
from config.database import get_pool, close_pool
from utils.background import register_handler, shutdown as shutdown_background
from workers.video_processor import process_video_job
from routers.auth import router as auth_router
from routers.oauth import router as oauth_router
from routers.users import router as users_router
from routers.videos import router as videos_router
from routers.jobs import router as jobs_router
from routers.files import router as files_router
from routers.health import router as health_router
from models.video import cleanup_stale_jobs

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    print("============================================================")
    print("  VideoNotes AI — FastAPI Backend Starting")
    print("============================================================")

    try:
        await get_pool()
        print("[Startup] Database connection pool initialized.")
    except Exception as e:
        print(f"[Startup] WARNING: Database connection failed: {e}")

    register_handler("process_video", process_video_job)
    print("[Startup] Background video processing worker registered.")

    try:
        await cleanup_stale_jobs(timeout_minutes=15)
        print("[Startup] Stale stuck job cleanup completed.")
    except Exception as e:
        print(f"[Startup] Stale job cleanup warning: {e}")

    root = settings.storage_root
    for d in [root, f"{root}/uploads", f"{root}/temp", f"{root}/pdfs", f"{root}/frames"]:
        os.makedirs(d, exist_ok=True)
    print(f"[Startup] Storage directories ensured at: {os.path.abspath(root)}")

    print(f"[Startup] Swagger UI: http://localhost:{settings.port}/docs")
    print(f"[Startup] ReDoc:      http://localhost:{settings.port}/redoc")
    print(f"[Startup] API base:   http://localhost:{settings.port}/api")
    print("============================================================")

    yield

    print("[Shutdown] Closing connections...")
    shutdown_background()
    await close_pool()
    print("[Shutdown] Complete.")

app = FastAPI(
    title="VideoNotes AI API",
    description="""
**VideoNotes AI** turns long-form videos into concise visual notes.

## Features
- 🎥 Upload videos or paste YouTube links
- 📸 Extract frames at configurable intervals
- 📝 AI-generated transcripts and notes
- 📄 PDF generation with frames + transcripts
- 🤖 AI summaries, flashcards, quizzes, and more

## Authentication
All protected endpoints require a JWT token in the `Authorization: Bearer <token>` header.
Get a token by calling `POST /api/auth/login`.
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list if settings.origins_list else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)}
    )

# Primary API routes (prefixed with /api)
app.include_router(auth_router, prefix="/api")
app.include_router(oauth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(videos_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(files_router, prefix="/api")

# Fallback API routes (without /api prefix, in case VITE_API_BASE_URL is set without /api)
app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(users_router)
app.include_router(videos_router)
app.include_router(jobs_router)
app.include_router(files_router)
app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)
