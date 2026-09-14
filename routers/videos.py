"""Video upload and retrieval router."""

import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from routers.auth import get_current_user
from models.schemas import CreateYouTubeJobRequest
from models.video import create_video, create_job, find_video_by_id
from utils.background import dispatch_background
from config.settings import settings

router = APIRouter(prefix="/videos", tags=["Videos"])

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    mode: str = Form("frames+transcript"),
    intervalSeconds: Optional[int] = Form(None),
    interval_seconds: Optional[int] = Form(None),
    user = Depends(get_current_user)
):
    user_id = str(user["id"])
    interval = intervalSeconds if intervalSeconds is not None else (interval_seconds if interval_seconds is not None else 3)

    filename = f"{uuid.uuid4()}_{file.filename}"
    upload_dir = os.path.join(settings.storage_root, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    video = await create_video(user_id=user_id, filename=filename)
    job = await create_job(user_id=user_id, video_id=video["id"], mode=mode, interval_seconds=interval)

    await dispatch_background("process_video", {"job_id": job["id"]})
    return {
        "id": job["id"],
        "jobId": job["id"],
        "videoId": video["id"],
        "status": job["status"],
        "mode": job["mode"],
        "intervalSeconds": job["intervalSeconds"],
        "createdAt": job["createdAt"]
    }

@router.post("/youtube")
async def create_youtube_job(req: CreateYouTubeJobRequest, user = Depends(get_current_user)):
    user_id = str(user["id"])
    try:
        yt_url = req.get_url()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    interval = req.get_interval()
    video = await create_video(user_id=user_id, youtube_url=yt_url)
    job = await create_job(user_id=user_id, video_id=video["id"], mode=req.mode, interval_seconds=interval)

    await dispatch_background("process_video", {"job_id": job["id"]})
    return {
        "id": job["id"],
        "jobId": job["id"],
        "videoId": video["id"],
        "status": job["status"],
        "mode": job["mode"],
        "intervalSeconds": job["intervalSeconds"],
        "createdAt": job["createdAt"]
    }

@router.get("/{video_id}")
async def get_video(video_id: str, user = Depends(get_current_user)):
    video = await find_video_by_id(video_id)
    if not video or video["userId"] != str(user["id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video
