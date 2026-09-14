"""Video upload and retrieval router."""

import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from routers.auth import get_current_user
from models.video import create_video, find_video_by_id
from config.settings import settings

router = APIRouter(prefix="/api/videos", tags=["Videos"])

@router.post("/upload")
async def upload_video(file: UploadFile = File(...), user = Depends(get_current_user)):
    user_id = str(user["id"])
    filename = f"{uuid.uuid4()}_{file.filename}"
    upload_dir = os.path.join(settings.storage_root, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    video = await create_video(user_id=user_id, filename=filename)
    return video

@router.get("/{video_id}")
async def get_video(video_id: str, user = Depends(get_current_user)):
    video = await find_video_by_id(video_id)
    if not video or video["userId"] != str(user["id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video
